from app.services.agents.human_selection import (
    ActivitySelectionStatus,
    decide_activity_selection,
)
from app.services.agents.schemas import ActivityCandidate, RankedCandidate


def _snapshot(*ids_completed: tuple[str, bool]) -> list[ActivityCandidate]:
    return [
        ActivityCandidate(activity_id=aid, name=aid, is_completed=completed)
        for aid, completed in ids_completed
    ]


def test_auto_selects_when_all_conditions_met() -> None:
    ranked = [
        RankedCandidate(activity_id="A100", confidence=0.92),
        RankedCandidate(activity_id="A200", confidence=0.40),
    ]
    snapshot = _snapshot(("A100", False), ("A200", False))

    decision = decide_activity_selection(ranked, snapshot)

    assert decision.status == ActivitySelectionStatus.AUTO_SELECTED
    assert decision.selected_activity_id == "A100"


def test_needs_selection_when_top1_confidence_too_low() -> None:
    ranked = [
        RankedCandidate(activity_id="A100", confidence=0.80),
        RankedCandidate(activity_id="A200", confidence=0.10),
    ]
    snapshot = _snapshot(("A100", False), ("A200", False))

    decision = decide_activity_selection(ranked, snapshot)

    assert decision.status == ActivitySelectionStatus.NEEDS_ACTIVITY_SELECTION
    assert decision.selected_activity_id is None


def test_needs_selection_when_margin_too_small() -> None:
    ranked = [
        RankedCandidate(activity_id="A100", confidence=0.90),
        RankedCandidate(activity_id="A200", confidence=0.85),
    ]
    snapshot = _snapshot(("A100", False), ("A200", False))

    decision = decide_activity_selection(ranked, snapshot)

    assert decision.status == ActivitySelectionStatus.NEEDS_ACTIVITY_SELECTION


def test_needs_selection_when_top_activity_completed() -> None:
    ranked = [
        RankedCandidate(activity_id="A100", confidence=0.95),
        RankedCandidate(activity_id="A200", confidence=0.20),
    ]
    snapshot = _snapshot(("A100", True), ("A200", False))

    decision = decide_activity_selection(ranked, snapshot)

    assert decision.status == ActivitySelectionStatus.NEEDS_ACTIVITY_SELECTION


def test_needs_selection_when_activity_missing_from_snapshot() -> None:
    ranked = [RankedCandidate(activity_id="GHOST", confidence=0.99)]
    snapshot = _snapshot(("A100", False))

    decision = decide_activity_selection(ranked, snapshot)

    assert decision.status == ActivitySelectionStatus.NEEDS_ACTIVITY_SELECTION


def test_single_high_confidence_candidate_auto_selects() -> None:
    ranked = [RankedCandidate(activity_id="A100", confidence=0.95)]
    snapshot = _snapshot(("A100", False))

    decision = decide_activity_selection(ranked, snapshot)

    assert decision.status == ActivitySelectionStatus.AUTO_SELECTED
    assert decision.selected_activity_id == "A100"


def test_empty_candidates_needs_selection() -> None:
    decision = decide_activity_selection([], _snapshot(("A100", False)))

    assert decision.status == ActivitySelectionStatus.NEEDS_ACTIVITY_SELECTION
