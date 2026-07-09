from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReportEvidence:
    chunk_id: int
    source_name: str
    trade: str
    location: str
    content: str


@dataclass
class ReportCandidate:
    activity_id: str
    name: str
    sql_score: float
    agent_confidence: float | None
    is_selected: bool


@dataclass
class ReportScenario:
    index: int
    action: str
    target_activity_id: str
    reduction_days: int
    adjusted_value_days: int
    scenario_project_duration: int
    recovered_days: int
    applicable: bool
    rationale: str
    evidence_chunk_ids: list[int]


@dataclass
class ReportContext:
    project_name: str
    snapshot_label: str
    generated_at: datetime
    issue_text: str
    status: str
    issue_type: str
    location: str | None
    trade: str | None
    delay_days: int | None
    impact_mode: str | None
    candidates: list[ReportCandidate]
    selected_activity_id: str | None
    selection_reasons: list[str]
    evidence: list[ReportEvidence]
    baseline_duration: int | None
    impact_duration: int | None
    project_delay_days: int | None
    target_total_float: int | None
    is_target_critical: bool | None
    critical_path: list[str] = field(default_factory=list)
    scenarios: list[ReportScenario] = field(default_factory=list)
    rule_passed: bool | None = None
    rule_requires_human: bool | None = None
    rule_violations: list[dict] = field(default_factory=list)
    review_warnings: list[dict] = field(default_factory=list)
    review_needs_human: bool | None = None
    review_summary: str = ""


def _fmt(value: object) -> str:
    return "-" if value is None else str(value)


def render_markdown_report(ctx: ReportContext) -> str:
    lines: list[str] = []
    lines.append("# P6 Schedule Recovery 분석 보고서")
    lines.append("")
    lines.append(f"- 프로젝트: {ctx.project_name}")
    lines.append(f"- 스냅샷: {ctx.snapshot_label}")
    lines.append(f"- 생성 시각: {ctx.generated_at.isoformat()}")
    lines.append(f"- 분석 상태: **{ctx.status}**")
    lines.append("")

    lines.append("## 1. 현장 이슈")
    lines.append("")
    lines.append(f"> {ctx.issue_text}")
    lines.append("")

    lines.append("## 2. 이슈 구조화")
    lines.append("")
    lines.append("| 항목 | 값 |")
    lines.append("|---|---|")
    lines.append(f"| issue type | {_fmt(ctx.issue_type)} |")
    lines.append(f"| 위치 | {_fmt(ctx.location)} |")
    lines.append(f"| 공종 | {_fmt(ctx.trade)} |")
    lines.append(f"| 지연일 | {_fmt(ctx.delay_days)} |")
    lines.append(f"| impact mode | {_fmt(ctx.impact_mode)} |")
    lines.append("")
    if ctx.delay_days is None:
        lines.append("> ⚠️ 지연일 정보가 이슈 텍스트에 명시되지 않았습니다. human review가 필요합니다.")
        lines.append("")

    lines.append("## 3. Activity 매핑")
    lines.append("")
    lines.append("| Activity | 이름 | SQL score | Agent confidence | 선택 |")
    lines.append("|---|---|---|---|---|")
    for c in ctx.candidates:
        selected = "✅" if c.is_selected else ""
        conf = "-" if c.agent_confidence is None else f"{c.agent_confidence:.2f}"
        lines.append(f"| {c.activity_id} | {c.name} | {c.sql_score:.3f} | {conf} | {selected} |")
    lines.append("")
    if ctx.selected_activity_id:
        lines.append(f"선택된 Activity: **{ctx.selected_activity_id}**")
    else:
        lines.append("**NEEDS_ACTIVITY_SELECTION** — 자동 선택 조건을 만족하지 못했습니다:")
        for reason in ctx.selection_reasons:
            lines.append(f"- {reason}")
    lines.append("")

    lines.append("## 4. RAG 근거 문서")
    lines.append("")
    if ctx.evidence:
        for e in ctx.evidence:
            lines.append(
                f"- [chunk {e.chunk_id}] ({e.source_name}, 공종: {e.trade or '-'}, 위치: {e.location or '-'})"
            )
            lines.append(f"  > {e.content.strip()}")
    else:
        lines.append("관련 근거 없음. 근거 부족 상태이며 human review가 필요합니다.")
    lines.append("")

    lines.append("## 5. 일정 영향 (CPM)")
    lines.append("")
    if ctx.baseline_duration is not None:
        lines.append("| 항목 | 값 |")
        lines.append("|---|---|")
        lines.append(f"| baseline 공기 | {_fmt(ctx.baseline_duration)} |")
        lines.append(f"| impact 공기 | {_fmt(ctx.impact_duration)} |")
        lines.append(f"| 프로젝트 지연 | {_fmt(ctx.project_delay_days)} |")
        lines.append(f"| 대상 Total Float | {_fmt(ctx.target_total_float)} |")
        lines.append(f"| 대상 critical 여부 | {_fmt(ctx.is_target_critical)} |")
        lines.append("")
        if ctx.critical_path:
            lines.append(f"Critical Path: {' → '.join(ctx.critical_path)}")
            lines.append("")
    else:
        lines.append("일정 영향은 Activity 선택 후 계산됩니다.")
        lines.append("")

    lines.append("## 6. 복구 시나리오")
    lines.append("")
    if ctx.scenarios:
        lines.append("| # | action | 대상 | reduction | 조정값 | 시나리오 공기 | recovered days | 적용가능 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for s in ctx.scenarios:
            ok = "예" if s.applicable else "아니오"
            lines.append(
                f"| {s.index + 1} | {s.action} | {s.target_activity_id} | {s.reduction_days} | "
                f"{s.adjusted_value_days} | {s.scenario_project_duration} | {s.recovered_days} | {ok} |"
            )
        lines.append("")
        for s in ctx.scenarios:
            cites = ", ".join(str(c) for c in s.evidence_chunk_ids) if s.evidence_chunk_ids else "없음"
            lines.append(f"- 시나리오 {s.index + 1}: {s.rationale} (근거 chunk: {cites})")
        lines.append("")
    else:
        lines.append("복구 시나리오는 Activity 선택 후 생성됩니다.")
        lines.append("")

    lines.append("## 7. 규칙 검증 (Rule Validator)")
    lines.append("")
    if ctx.rule_passed is not None:
        lines.append(f"- 통과: {ctx.rule_passed}")
        lines.append(f"- human confirmation 필요: {ctx.rule_requires_human}")
        if ctx.rule_violations:
            lines.append("- 위반 사항:")
            for v in ctx.rule_violations:
                lines.append(f"  - `{v.get('code')}`: {v.get('message')}")
        lines.append("")
    else:
        lines.append("규칙 검증은 Activity 선택 후 수행됩니다.")
        lines.append("")

    lines.append("## 8. 독립 검토 (Review Agent)")
    lines.append("")
    if ctx.review_needs_human is not None:
        lines.append(f"- human review 필요: {ctx.review_needs_human}")
        if ctx.review_summary:
            lines.append(f"- 요약: {ctx.review_summary}")
        if ctx.review_warnings:
            lines.append("- 경고:")
            for w in ctx.review_warnings:
                lines.append(f"  - [{w.get('category')}] {w.get('message')}")
        lines.append("")
    else:
        lines.append("독립 검토는 Activity 선택 후 수행됩니다.")
        lines.append("")

    lines.append("## 9. 최종 판단 (사람)")
    lines.append("")
    lines.append("다음 결정은 반드시 사람이 수행합니다: P6 반영 여부, 복구 시나리오 선택, "
                 "safety/quality/cost 승인, contract/EOT 판단.")
    lines.append("")

    return "\n".join(lines)
