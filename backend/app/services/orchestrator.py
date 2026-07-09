"""분석 오케스트레이터 — LangGraph StateGraph에 해당하는 상태 머신.

[수업 정리] 이 파일이 사실상 LangGraph의 StateGraph다. (개념 매핑이 핵심)
======================================================================
LangGraph는 "상태(State)를 들고 노드(Node)들을 엣지(Edge)로 이동하는 그래프"로
멀티스텝 LLM 워크플로를 만든다. 우리는 프레임워크 없이 같은 구조를 손으로 구현했다.

  LangGraph 개념        →  이 코드에서의 구현
  --------------------------------------------------------------------
  State (TypedDict)     →  AnalysisRun (DB 행). 모든 노드가 이 상태를 읽고 갱신
  Node (함수)           →  _run_mapper / _finish / _simulate_and_persist_scenarios ...
  Edge (전이)           →  analyze() 안의 호출 순서
  Conditional edge      →  decide_activity_selection() 결과에 따른 분기
                           (AUTO_SELECTED → 계속 / NEEDS_ACTIVITY_SELECTION → 중단)
  interrupt + resume    →  NEEDS_ACTIVITY_SELECTION 에서 멈춤 → select_activity()로 재개
  checkpointer          →  DB(analysis_runs 등)에 상태/trace 영속화
  START/END             →  analyze() 진입 / status=COMPLETED|FAILED

전체 그래프 흐름(설계 7절):
  이슈 → [입력 가드레일] → Activity 후보검색(pg_trgm) → RAG 검색(retriever)
       → Mapper(LLM) → [출력 가드레일] → 자동선택 판정
         ├─ 자동선택 → baseline/impact CPM(결정론적 엔진)
         │            → Planner(LLM) → [출력 가드레일] → Rule Validator
         │            → 시나리오 시뮬(엔진) → Reviewer(LLM) → Markdown 보고서 → END(COMPLETED)
         └─ 확신부족 → NEEDS_ACTIVITY_SELECTION(interrupt) → 사람이 select_activity → 위 finish 재개

[중요 원칙] 일정 "수치"는 전부 결정론적 엔진(schedule_engine)이 계산하고,
LLM은 구조화/제안/설명만 한다. 노드 사이에서 엔진 계산 결과를 프롬프트로 주입한다.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError
from app.db.models import (
    Activity,
    ActivityMatch,
    AgentRun,
    AnalysisRun,
    Issue,
    Relationship as RelationshipModel,
    Report,
    RetrievalRun,
    ScheduleSnapshot,
)
from app.services.activity_search import search_activity_candidates
from app.services.agents.human_selection import (
    ActivitySelectionStatus,
    decide_activity_selection,
)
from app.services.agents.mapper import IssueMappingAgent
from app.services.agents.planner import RecoveryPlanningAgent
from app.services.agents.reviewer import ReviewAgent
from app.services.agents.rule_validator import validate_agent_outputs
from app.services.agents.schemas import (
    ActivityCandidate,
    AgentOutputError,
    EvidenceChunk,
    IssueMappingResult,
    RankedCandidate,
)
from app.services.embeddings import EmbeddingProvider
from app.services.guardrails import (
    check_agent_output_no_computed_fields,
    check_issue_input,
)
from app.services.llm.json_repair import LLMJsonParseError, parse_llm_json
from app.services.llm.registry import LLMProviderRegistry
from app.services.llm.types import LLMResponse, LLMRole
from app.services.report import (
    ReportCandidate,
    ReportContext,
    ReportEvidence,
    ReportScenario,
    render_markdown_report,
)
from app.services.retrieval import RetrievedChunk, search_knowledge_chunks
from app.services.schedule_engine import (
    ActivityInput,
    ImpactMode as EngineImpactMode,
    RecoveryAction,
    RelationshipInput,
    ScheduleEngineError,
    ScheduleGraph,
    apply_issue_impact,
    simulate_scenario,
)

logger = logging.getLogger("app.orchestrator")

CANDIDATE_SEARCH_LIMIT = 10


class AnalysisStatus:
    """그래프의 상태값. LangGraph State의 status 필드에 해당하며, 노드 전이의 종착지다."""

    PENDING = "PENDING"
    NEEDS_ACTIVITY_SELECTION = "NEEDS_ACTIVITY_SELECTION"  # interrupt: 사람 입력 대기
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisOrchestrator:
    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: EmbeddingProvider,
        registry: LLMProviderRegistry,
    ) -> None:
        self._db = db
        self._embedding = embedding_provider
        self._registry = registry

    # --- Public entry points -----------------------------------------------------

    async def analyze(self, issue: Issue) -> AnalysisRun:
        snapshot = await self._latest_snapshot(issue.project_id)
        run = AnalysisRun(
            issue_id=issue.id,
            project_id=issue.project_id,
            snapshot_id=snapshot.id,
            status=AnalysisStatus.PENDING,
        )
        self._db.add(run)
        await self._db.flush()

        # [가드레일 - Input] 사용자 자연어 이슈를 LLM에 넣기 전에 검사한다.
        # 빈 값/길이 초과/프롬프트 인젝션 의심 시 파이프라인을 시작하지 않고 FAILED 처리.
        input_guardrail = check_issue_input(issue.raw_text)
        if not input_guardrail.passed:
            run.status = AnalysisStatus.FAILED
            run.error_message = "입력 가드레일 위반: " + "; ".join(
                v.message for v in input_guardrail.violations
            )
            await self._db.commit()
            await self._db.refresh(run)
            return run

        try:
            # --- Node: 스냅샷 활동 로드 + Activity 후보검색(pg_trgm) + RAG 검색 ---
            all_activities = await self._snapshot_activities(snapshot.id)
            candidates = await search_activity_candidates(
                self._db, snapshot.id, issue.raw_text, limit=CANDIDATE_SEARCH_LIMIT
            )
            evidence = await self._retrieve_evidence(run, issue)  # retriever.invoke

            # --- Node: Issue Mapping Agent (LLM) → 상태에 매핑 결과 기록 ---
            mapping = await self._run_mapper(run, issue.raw_text, candidates, evidence)
            self._persist_matches(run, candidates, mapping)

            run.issue_delay_days = mapping.delay_days
            run.impact_mode = mapping.impact_mode.value
            run.mapping_json = mapping.model_dump(mode="json")

            # --- Conditional edge: 자동선택 vs 사람선택 분기(human-in-the-loop 게이트) ---
            decision = decide_activity_selection(
                mapping.ranked_candidates,
                [ActivityCandidate(activity_id=a.activity_id, name=a.name, is_completed=a.is_completed) for a in all_activities],
            )

            if decision.status == ActivitySelectionStatus.AUTO_SELECTED:
                # 확신 충분 → 그래프의 나머지 노드(finish)로 곧장 진행
                await self._finish(run, snapshot, all_activities, evidence, mapping, decision.selected_activity_id)
            else:
                # 확신 부족 → interrupt: 여기서 멈추고 사람의 select_activity 를 기다린다
                run.status = AnalysisStatus.NEEDS_ACTIVITY_SELECTION
                await self._store_partial_report(run, snapshot, mapping, candidates, evidence, decision.reasons)

            await self._db.commit()
            await self._db.refresh(run)
            return run
        except (AgentOutputError, ScheduleEngineError) as exc:
            # 그래프 실행 중 에이전트/가드레일/엔진 오류 → 상태를 FAILED로 종료(END)
            run.status = AnalysisStatus.FAILED
            run.error_message = str(exc)
            await self._db.commit()
            await self._db.refresh(run)
            return run

    async def select_activity(self, run: AnalysisRun, activity_id: str) -> AnalysisRun:
        # [interrupt resume] 사람이 Activity를 고르면 중단됐던 그래프를 이 지점부터 재개한다.
        # 저장돼 있던 상태(mapping_json, retrieved chunks)를 복원해 finish 노드로 이어간다.
        if run.status not in (AnalysisStatus.NEEDS_ACTIVITY_SELECTION, AnalysisStatus.COMPLETED):
            raise APIError(
                status_code=409,
                error_code="invalid_analysis_state",
                message=f"Analysis run {run.id} is not awaiting activity selection.",
            )

        snapshot = await self._db.get(ScheduleSnapshot, run.snapshot_id)
        all_activities = await self._snapshot_activities(snapshot.id)
        if not any(a.activity_id == activity_id for a in all_activities):
            raise APIError(
                status_code=422,
                error_code="activity_not_in_snapshot",
                message=f"Activity '{activity_id}' does not exist in the snapshot.",
            )

        mapping = IssueMappingResult.model_validate(run.mapping_json)
        evidence = await self._reload_evidence(run)

        # Clear any previous selection / scenario state before re-running.
        await self._reset_downstream(run)
        await self._mark_selected(run, activity_id)

        await self._finish(run, snapshot, all_activities, evidence, mapping, activity_id)
        await self._db.commit()
        await self._db.refresh(run)
        return run

    # --- Pipeline stages ---------------------------------------------------------

    async def _finish(
        self,
        run: AnalysisRun,
        snapshot: ScheduleSnapshot,
        all_activities: list[Activity],
        evidence: list[EvidenceChunk],
        mapping: IssueMappingResult,
        selected_activity_id: str,
    ) -> None:
        # finish = 그래프의 "선택 이후" 노드 묶음(계산→계획→검증→시뮬→검토→보고서).
        run.selected_activity_id = selected_activity_id
        graph = await self._build_graph(snapshot.id, all_activities)

        if not graph.has_activity(selected_activity_id):
            raise ScheduleEngineError(f"Selected activity '{selected_activity_id}' not in schedule graph.")

        # --- Node: 결정론적 CPM 계산 (LLM 아님!). baseline vs 이슈 반영(impact) ---
        baseline_cpm = graph.compute_cpm()
        impact_mode = EngineImpactMode(mapping.impact_mode.value)
        delay_days = mapping.delay_days or 0

        impacted_graph = apply_issue_impact(graph, impact_mode, selected_activity_id, delay_days)
        impacted_cpm = impacted_graph.compute_cpm()
        impacted_duration = impacted_cpm.project_duration

        target_calc = impacted_cpm.activities[selected_activity_id]
        run.baseline_json = {
            "project_duration": baseline_cpm.project_duration,
            "critical_path": baseline_cpm.critical_path,
        }
        run.impact_json = {
            "project_duration": impacted_duration,
            "project_delay_days": impacted_duration - baseline_cpm.project_duration,
            "target_total_float": target_calc.total_float,
            "is_target_critical": target_calc.is_critical,
            "critical_path": impacted_cpm.critical_path,
        }

        allowed_activity_ids = {a.activity_id for a in all_activities}
        allowed_chunk_ids = {e.chunk_id for e in evidence}

        impact_summary = {
            "impact_mode": impact_mode.value,
            "issue_delay_days": delay_days,
            **run.impact_json,
        }
        # --- Node: Recovery Planning Agent (LLM). 엔진이 계산한 impact를 프롬프트로 주입 ---
        plan = await self._run_planner(run, selected_activity_id, impact_summary, delay_days, evidence)
        run.plan_json = plan.model_dump(mode="json")

        # --- Node: Rule Validator (규칙 가드레일, LLM 아님) ---
        rule_result = validate_agent_outputs(mapping, plan, allowed_activity_ids, allowed_chunk_ids)
        run.rule_validation_json = rule_result.to_summary()

        # --- Node: 시나리오 시뮬레이션 (결정론적 엔진이 recovered_days 계산) ---
        self._simulate_and_persist_scenarios(
            run, graph, impacted_graph, impacted_duration, impact_mode, selected_activity_id, delay_days, plan
        )

        # --- Node: Review Agent (LLM-as-a-judge) ---
        review = await self._run_reviewer(run, mapping, plan, rule_result.to_summary())
        run.review_json = review.model_dump(mode="json")

        # --- Node: Markdown 보고서 생성 → END(COMPLETED) ---
        run.status = AnalysisStatus.COMPLETED
        await self._store_full_report(run, snapshot, mapping, evidence, plan, rule_result, review)

    # --- Agents ------------------------------------------------------------------

    async def _run_mapper(self, run, issue_text, candidates, evidence) -> IssueMappingResult:
        agent = IssueMappingAgent(self._registry)
        agent_candidates = [
            ActivityCandidate(activity_id=c.activity_id, name=c.name, is_completed=c.is_completed)
            for c in candidates
        ]
        mapping = await agent.run(issue_text, agent_candidates, evidence)
        self._run_output_guardrail(agent.last_response)
        self._persist_agent_run(run, LLMRole.ISSUE_MAPPER, agent.last_response, mapping.model_dump(mode="json"))
        return mapping

    async def _run_planner(self, run, activity_id, impact_summary, delay_days, evidence):
        agent = RecoveryPlanningAgent(self._registry)
        plan = await agent.run(activity_id, impact_summary, delay_days, evidence)
        self._run_output_guardrail(agent.last_response)
        self._persist_agent_run(run, LLMRole.RECOVERY_PLANNER, agent.last_response, plan.model_dump(mode="json"))
        return plan

    def _run_output_guardrail(self, response: LLMResponse | None) -> None:
        """[가드레일 - Output] LLM 원본 JSON에 계산 금지 필드가 없는지 검사.
        위반 시 AgentOutputError → analyze()에서 FAILED로 처리된다."""
        if response is None:
            return
        try:
            raw = parse_llm_json(response.content)
        except LLMJsonParseError:
            return  # 형식 오류는 스키마 검증 단계에서 이미 걸러진다.
        guardrail = check_agent_output_no_computed_fields(raw)
        if not guardrail.passed:
            raise AgentOutputError(
                "출력 가드레일 위반: " + "; ".join(v.message for v in guardrail.violations)
            )

    async def _run_reviewer(self, run, mapping, plan, rule_summary):
        agent = ReviewAgent(self._registry)
        review = await agent.run(
            mapping.model_dump(mode="json"), plan.model_dump(mode="json"), rule_summary
        )
        self._persist_agent_run(run, LLMRole.REVIEWER, agent.last_response, review.model_dump(mode="json"))
        return review

    # --- Scenario simulation -----------------------------------------------------

    def _simulate_and_persist_scenarios(
        self, run, graph, impacted_graph, impacted_duration, impact_mode, activity_id, delay_days, plan
    ) -> None:
        for index, scenario in enumerate(plan.scenarios):
            action = RecoveryAction(scenario.action.value)
            target = scenario.target_activity_id if graph.has_activity(scenario.target_activity_id) else activity_id
            sim = simulate_scenario(
                baseline_graph=graph,
                impacted_graph=impacted_graph,
                impacted_duration=impacted_duration,
                impact_mode=impact_mode,
                target_activity_id=target,
                delay_days=delay_days,
                action=action,
                reduction_days=scenario.reduction_days,
            )
            self._db.add(
                ScenarioRunFactory.build(run.id, index, target, scenario, sim)
            )

    # --- Persistence helpers -----------------------------------------------------

    def _persist_agent_run(self, run, role: LLMRole, response: LLMResponse | None, parsed: dict) -> None:
        import json

        self._db.add(
            AgentRun(
                analysis_run_id=run.id,
                agent_role=role.value,
                provider_name=response.provider_name if response else "unavailable",
                model=response.model if response else "unavailable",
                raw_output=response.content if response else json.dumps(parsed, ensure_ascii=False),
            )
        )

    def _persist_matches(self, run, candidates, mapping: IssueMappingResult) -> None:
        confidence_by_id = {c.activity_id: c for c in mapping.ranked_candidates}
        ordered = sorted(
            candidates,
            key=lambda c: (
                confidence_by_id[c.activity_id].confidence if c.activity_id in confidence_by_id else -1.0,
                c.sql_score,
            ),
            reverse=True,
        )
        for rank, candidate in enumerate(ordered):
            ranked = confidence_by_id.get(candidate.activity_id)
            self._db.add(
                ActivityMatch(
                    analysis_run_id=run.id,
                    activity_id=candidate.activity_id,
                    name=candidate.name,
                    sql_score=candidate.sql_score,
                    agent_confidence=ranked.confidence if ranked else None,
                    agent_reason=ranked.reason if ranked else None,
                    rank=rank,
                    is_selected=False,
                )
            )

    async def _mark_selected(self, run, activity_id: str) -> None:
        result = await self._db.execute(
            select(ActivityMatch).where(ActivityMatch.analysis_run_id == run.id)
        )
        for match in result.scalars().all():
            match.is_selected = match.activity_id == activity_id

    async def _reset_downstream(self, run: AnalysisRun) -> None:
        from sqlalchemy import delete as sa_delete

        from app.db.models import ScenarioRun as ScenarioRunModel

        await self._db.execute(
            sa_delete(ScenarioRunModel).where(ScenarioRunModel.analysis_run_id == run.id)
        )
        await self._db.execute(sa_delete(Report).where(Report.analysis_run_id == run.id))

    # --- Data loading ------------------------------------------------------------

    async def _latest_snapshot(self, project_id: int) -> ScheduleSnapshot:
        result = await self._db.execute(
            select(ScheduleSnapshot)
            .where(ScheduleSnapshot.project_id == project_id)
            .order_by(ScheduleSnapshot.imported_at.desc())
        )
        snapshot = result.scalars().first()
        if snapshot is None:
            raise APIError(
                status_code=422,
                error_code="no_snapshot",
                message="Project has no schedule snapshot to analyze.",
            )
        if snapshot.is_dag is False:
            raise APIError(
                status_code=422,
                error_code="snapshot_not_dag",
                message="Latest snapshot contains a cycle and cannot be analyzed.",
            )
        return snapshot

    async def _snapshot_activities(self, snapshot_id: int) -> list[Activity]:
        result = await self._db.execute(select(Activity).where(Activity.snapshot_id == snapshot_id))
        return list(result.scalars().all())

    async def _build_graph(self, snapshot_id: int, activities: list[Activity]) -> ScheduleGraph:
        rel_result = await self._db.execute(
            select(RelationshipModel).where(RelationshipModel.snapshot_id == snapshot_id)
        )
        relationships = list(rel_result.scalars().all())
        return ScheduleGraph(
            [
                ActivityInput(
                    activity_id=a.activity_id,
                    name=a.name,
                    remaining_duration=a.remaining_duration,
                    is_milestone=a.is_milestone,
                    is_completed=a.is_completed,
                )
                for a in activities
            ],
            [
                RelationshipInput(
                    predecessor_id=r.predecessor_id, successor_id=r.successor_id, lag=r.lag
                )
                for r in relationships
            ],
        )

    async def _retrieve_evidence(self, run: AnalysisRun, issue: Issue) -> list[EvidenceChunk]:
        chunks = await search_knowledge_chunks(
            db=self._db,
            embedding_provider=self._embedding,
            project_id=issue.project_id,
            query_text=issue.raw_text,
        )
        run.retrieved_chunk_ids = [c.chunk_id for c in chunks]
        self._db.add(
            RetrievalRun(
                project_id=issue.project_id,
                analysis_run_id=run.id,
                query_text=issue.raw_text,
                returned_chunk_ids=",".join(str(c.chunk_id) for c in chunks),
            )
        )
        return [self._to_evidence(c) for c in chunks]

    async def _reload_evidence(self, run: AnalysisRun) -> list[EvidenceChunk]:
        chunk_ids = run.retrieved_chunk_ids or []
        if not chunk_ids:
            return []
        from app.db.models import KnowledgeChunk, KnowledgeDocument

        result = await self._db.execute(
            select(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .where(KnowledgeChunk.id.in_(chunk_ids))
        )
        evidence: list[EvidenceChunk] = []
        for chunk, document in result.all():
            evidence.append(
                EvidenceChunk(
                    chunk_id=chunk.id,
                    content=chunk.content,
                    source_name=document.source_name,
                    trade=document.trade,
                    location=document.location,
                )
            )
        return evidence

    @staticmethod
    def _to_evidence(chunk: RetrievedChunk) -> EvidenceChunk:
        return EvidenceChunk(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            source_name=chunk.source_name,
            trade=chunk.trade,
            location=chunk.location,
        )

    # --- Reports -----------------------------------------------------------------

    async def _store_partial_report(self, run, snapshot, mapping, candidates, evidence, reasons) -> None:
        await self._db.flush()
        ctx = await self._build_report_context(
            run, snapshot, mapping, evidence, plan=None, rule_result=None, review=None, selection_reasons=reasons
        )
        self._db.add(Report(analysis_run_id=run.id, markdown=render_markdown_report(ctx)))

    async def _store_full_report(self, run, snapshot, mapping, evidence, plan, rule_result, review) -> None:
        await self._db.flush()
        ctx = await self._build_report_context(
            run, snapshot, mapping, evidence, plan=plan, rule_result=rule_result, review=review, selection_reasons=[]
        )
        self._db.add(Report(analysis_run_id=run.id, markdown=render_markdown_report(ctx)))

    async def _build_report_context(
        self, run, snapshot, mapping, evidence, plan, rule_result, review, selection_reasons
    ) -> ReportContext:
        from app.db.models import Project, ScenarioRun as ScenarioRunModel

        project = await self._db.get(Project, run.project_id)

        match_result = await self._db.execute(
            select(ActivityMatch).where(ActivityMatch.analysis_run_id == run.id).order_by(ActivityMatch.rank)
        )
        matches = list(match_result.scalars().all())

        scenario_result = await self._db.execute(
            select(ScenarioRunModel)
            .where(ScenarioRunModel.analysis_run_id == run.id)
            .order_by(ScenarioRunModel.scenario_index)
        )
        scenario_rows = list(scenario_result.scalars().all())

        impact = run.impact_json or {}
        baseline = run.baseline_json or {}

        return ReportContext(
            project_name=project.name if project else "-",
            snapshot_label=snapshot.label,
            generated_at=datetime.now(timezone.utc),
            issue_text=(await self._db.get(Issue, run.issue_id)).raw_text,
            status=run.status,
            issue_type=mapping.issue_type,
            location=mapping.location,
            trade=mapping.trade,
            delay_days=mapping.delay_days,
            impact_mode=mapping.impact_mode.value,
            candidates=[
                ReportCandidate(
                    activity_id=m.activity_id,
                    name=m.name,
                    sql_score=m.sql_score,
                    agent_confidence=m.agent_confidence,
                    is_selected=m.is_selected,
                )
                for m in matches
            ],
            selected_activity_id=run.selected_activity_id,
            selection_reasons=selection_reasons,
            evidence=[
                ReportEvidence(
                    chunk_id=e.chunk_id,
                    source_name=e.source_name,
                    trade=e.trade,
                    location=e.location,
                    content=e.content,
                )
                for e in evidence
            ],
            baseline_duration=baseline.get("project_duration"),
            impact_duration=impact.get("project_duration"),
            project_delay_days=impact.get("project_delay_days"),
            target_total_float=impact.get("target_total_float"),
            is_target_critical=impact.get("is_target_critical"),
            critical_path=impact.get("critical_path", []),
            scenarios=[
                ReportScenario(
                    index=s.scenario_index,
                    action=s.action,
                    target_activity_id=s.target_activity_id,
                    reduction_days=s.reduction_days,
                    adjusted_value_days=s.adjusted_value_days,
                    scenario_project_duration=s.scenario_project_duration,
                    recovered_days=s.recovered_days,
                    applicable=s.applicable,
                    rationale=s.rationale or "",
                    evidence_chunk_ids=s.evidence_chunk_ids or [],
                )
                for s in scenario_rows
            ],
            rule_passed=rule_result.passed if rule_result else None,
            rule_requires_human=rule_result.requires_human_confirmation if rule_result else None,
            rule_violations=[
                {"code": v.code, "message": v.message} for v in rule_result.violations
            ] if rule_result else [],
            review_warnings=[
                {"category": w.category, "message": w.message} for w in review.warnings
            ] if review else [],
            review_needs_human=review.needs_human_review if review else None,
            review_summary=review.summary if review else "",
        )


class ScenarioRunFactory:
    @staticmethod
    def build(analysis_run_id, index, target, scenario, sim):
        from app.db.models import ScenarioRun as ScenarioRunModel

        return ScenarioRunModel(
            analysis_run_id=analysis_run_id,
            scenario_index=index,
            action=scenario.action.value,
            target_activity_id=target,
            reduction_days=scenario.reduction_days,
            adjusted_value_days=sim.adjusted_value_days,
            scenario_project_duration=sim.scenario_project_duration,
            recovered_days=sim.recovered_days,
            applicable=sim.applicable,
            rationale=scenario.rationale,
            evidence_chunk_ids=scenario.evidence_chunk_ids,
        )
