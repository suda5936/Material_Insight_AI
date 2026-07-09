from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError
from app.db.models import (
    ActivityMatch,
    AnalysisRun,
    Issue,
    Project,
    Report,
    ScenarioRun,
)
from app.db.session import get_db
from app.models.analysis import (
    ActivityMatchResponse,
    AnalysisRunResponse,
    IssueCreateRequest,
    IssueResponse,
    ScenarioResponse,
    SelectActivityRequest,
)
from app.services.embeddings import EmbeddingProvider, provide_embedding_provider
from app.services.llm.registry import LLMProviderRegistry, provide_llm_registry
from app.services.orchestrator import AnalysisOrchestrator

router = APIRouter(tags=["analysis"])


@router.post("/api/v1/issues", response_model=IssueResponse, status_code=201)
async def create_issue(payload: IssueCreateRequest, db: AsyncSession = Depends(get_db)) -> Issue:
    project = await db.get(Project, payload.project_id)
    if project is None:
        raise APIError(
            status_code=404,
            error_code="project_not_found",
            message=f"Project {payload.project_id} was not found.",
        )
    issue = Issue(project_id=payload.project_id, raw_text=payload.raw_text)
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
    return issue


async def _load_run_response(db: AsyncSession, run: AnalysisRun) -> AnalysisRunResponse:
    match_result = await db.execute(
        select(ActivityMatch).where(ActivityMatch.analysis_run_id == run.id).order_by(ActivityMatch.rank)
    )
    matches = list(match_result.scalars().all())

    scenario_result = await db.execute(
        select(ScenarioRun).where(ScenarioRun.analysis_run_id == run.id).order_by(ScenarioRun.scenario_index)
    )
    scenarios = list(scenario_result.scalars().all())

    return AnalysisRunResponse(
        id=run.id,
        issue_id=run.issue_id,
        project_id=run.project_id,
        snapshot_id=run.snapshot_id,
        status=run.status,
        selected_activity_id=run.selected_activity_id,
        issue_delay_days=run.issue_delay_days,
        impact_mode=run.impact_mode,
        retrieved_chunk_ids=run.retrieved_chunk_ids or [],
        baseline_json=run.baseline_json,
        impact_json=run.impact_json,
        rule_validation_json=run.rule_validation_json,
        review_json=run.review_json,
        error_message=run.error_message,
        activity_matches=[
            ActivityMatchResponse(
                activity_id=m.activity_id,
                name=m.name,
                sql_score=m.sql_score,
                agent_confidence=m.agent_confidence,
                agent_reason=m.agent_reason,
                rank=m.rank,
                is_selected=m.is_selected,
            )
            for m in matches
        ],
        scenarios=[
            ScenarioResponse(
                scenario_index=s.scenario_index,
                action=s.action,
                target_activity_id=s.target_activity_id,
                reduction_days=s.reduction_days,
                adjusted_value_days=s.adjusted_value_days,
                scenario_project_duration=s.scenario_project_duration,
                recovered_days=s.recovered_days,
                applicable=s.applicable,
                rationale=s.rationale,
                evidence_chunk_ids=s.evidence_chunk_ids or [],
            )
            for s in scenarios
        ],
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.post("/api/v1/issues/{issue_id}/analyze", response_model=AnalysisRunResponse, status_code=201)
async def analyze_issue(
    issue_id: int,
    db: AsyncSession = Depends(get_db),
    embedding_provider: EmbeddingProvider = Depends(provide_embedding_provider),
    registry: LLMProviderRegistry = Depends(provide_llm_registry),
) -> AnalysisRunResponse:
    issue = await db.get(Issue, issue_id)
    if issue is None:
        raise APIError(
            status_code=404, error_code="issue_not_found", message=f"Issue {issue_id} was not found."
        )

    orchestrator = AnalysisOrchestrator(db, embedding_provider, registry)
    run = await orchestrator.analyze(issue)
    return await _load_run_response(db, run)


@router.post("/api/v1/issues/{issue_id}/select-activity", response_model=AnalysisRunResponse)
async def select_activity(
    issue_id: int,
    payload: SelectActivityRequest,
    db: AsyncSession = Depends(get_db),
    embedding_provider: EmbeddingProvider = Depends(provide_embedding_provider),
    registry: LLMProviderRegistry = Depends(provide_llm_registry),
) -> AnalysisRunResponse:
    run = await db.get(AnalysisRun, payload.analysis_run_id)
    if run is None or run.issue_id != issue_id:
        raise APIError(
            status_code=404,
            error_code="analysis_run_not_found",
            message=f"Analysis run {payload.analysis_run_id} was not found for issue {issue_id}.",
        )

    orchestrator = AnalysisOrchestrator(db, embedding_provider, registry)
    run = await orchestrator.select_activity(run, payload.activity_id)
    return await _load_run_response(db, run)


@router.get("/api/v1/analysis-runs/{analysis_run_id}", response_model=AnalysisRunResponse)
async def get_analysis_run(analysis_run_id: int, db: AsyncSession = Depends(get_db)) -> AnalysisRunResponse:
    run = await db.get(AnalysisRun, analysis_run_id)
    if run is None:
        raise APIError(
            status_code=404,
            error_code="analysis_run_not_found",
            message=f"Analysis run {analysis_run_id} was not found.",
        )
    return await _load_run_response(db, run)


@router.get("/api/v1/analysis-runs/{analysis_run_id}/report.md", response_class=PlainTextResponse)
async def get_analysis_report(analysis_run_id: int, db: AsyncSession = Depends(get_db)) -> PlainTextResponse:
    result = await db.execute(select(Report).where(Report.analysis_run_id == analysis_run_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise APIError(
            status_code=404,
            error_code="report_not_found",
            message=f"No report found for analysis run {analysis_run_id}.",
        )
    return PlainTextResponse(content=report.markdown, media_type="text/markdown; charset=utf-8")
