"""Human-in-the-loop 게이트 — LangGraph의 interrupt에 해당.

[수업 정리] Human-in-the-loop (HITL).
------------------------------------------------------------------
자동화가 확신이 없을 때 사람에게 넘기는 패턴. LangGraph 대응:
    - graph에 interrupt_before=["select_activity"] 를 걸어 특정 노드 앞에서 멈춤
    - checkpointer로 상태를 저장하고, 사람이 입력을 준 뒤 재개(resume)

여기서는 그 개념을 상태값으로 구현한다: 설계 9절 조건(top1≥0.85, margin≥0.10,
미완료, snapshot 존재)을 "모두" 만족해야 AUTO_SELECTED, 아니면
NEEDS_ACTIVITY_SELECTION 상태로 멈춰 사람의 select-activity 입력을 기다린다.
오케스트레이터가 이 판정으로 파이프라인을 "중단(interrupt)"할지 결정한다.
"""

from dataclasses import dataclass
from enum import Enum

from app.services.agents.schemas import ActivityCandidate, RankedCandidate

# Thresholds from design section 9 (Human-in-the-loop).
MIN_TOP1_CONFIDENCE = 0.85
MIN_CONFIDENCE_MARGIN = 0.10


class ActivitySelectionStatus(str, Enum):
    AUTO_SELECTED = "AUTO_SELECTED"
    NEEDS_ACTIVITY_SELECTION = "NEEDS_ACTIVITY_SELECTION"


@dataclass(frozen=True)
class ActivitySelectionDecision:
    status: ActivitySelectionStatus
    selected_activity_id: str | None
    top1_confidence: float
    confidence_margin: float
    reasons: list[str]


def decide_activity_selection(
    ranked_candidates: list[RankedCandidate],
    snapshot_activities: list[ActivityCandidate],
) -> ActivitySelectionDecision:
    """Apply the section-9 gate. Auto-selection requires ALL conditions to hold,
    otherwise the run must fall back to NEEDS_ACTIVITY_SELECTION."""
    activity_index = {a.activity_id: a for a in snapshot_activities}

    ordered = sorted(ranked_candidates, key=lambda c: c.confidence, reverse=True)
    reasons: list[str] = []

    if not ordered:
        return ActivitySelectionDecision(
            status=ActivitySelectionStatus.NEEDS_ACTIVITY_SELECTION,
            selected_activity_id=None,
            top1_confidence=0.0,
            confidence_margin=0.0,
            reasons=["No activity candidates were ranked."],
        )

    top1 = ordered[0]
    top1_confidence = top1.confidence
    top2_confidence = ordered[1].confidence if len(ordered) > 1 else 0.0
    margin = top1_confidence - top2_confidence

    if top1_confidence < MIN_TOP1_CONFIDENCE:
        reasons.append(
            f"Top-1 confidence {top1_confidence:.2f} is below {MIN_TOP1_CONFIDENCE:.2f}."
        )
    if margin < MIN_CONFIDENCE_MARGIN:
        reasons.append(
            f"Confidence margin {margin:.2f} is below {MIN_CONFIDENCE_MARGIN:.2f}."
        )

    snapshot_activity = activity_index.get(top1.activity_id)
    if snapshot_activity is None:
        reasons.append(
            f"Activity '{top1.activity_id}' does not exist in the current snapshot."
        )
    elif snapshot_activity.is_completed:
        reasons.append(f"Activity '{top1.activity_id}' is already completed.")

    if reasons:
        return ActivitySelectionDecision(
            status=ActivitySelectionStatus.NEEDS_ACTIVITY_SELECTION,
            selected_activity_id=None,
            top1_confidence=top1_confidence,
            confidence_margin=margin,
            reasons=reasons,
        )

    return ActivitySelectionDecision(
        status=ActivitySelectionStatus.AUTO_SELECTED,
        selected_activity_id=top1.activity_id,
        top1_confidence=top1_confidence,
        confidence_margin=margin,
        reasons=["All auto-selection conditions satisfied."],
    )
