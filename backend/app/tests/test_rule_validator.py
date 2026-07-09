from app.services.agents.rule_validator import validate_agent_outputs
from app.services.agents.schemas import (
    IssueMappingResult,
    RankedCandidate,
    RecoveryPlanResult,
    RecoveryScenario,
)


def _valid_mapping() -> IssueMappingResult:
    return IssueMappingResult(
        issue_type="material_delay",
        impact_mode="START_BLOCK",
        ranked_candidates=[
            RankedCandidate(activity_id="A100", confidence=0.92),
            RankedCandidate(activity_id="A200", confidence=0.30),
        ],
        evidence_chunk_ids=[1, 2],
        missing_information=[],
        overall_confidence=0.9,
    )


def _valid_plan() -> RecoveryPlanResult:
    return RecoveryPlanResult(
        scenarios=[
            RecoveryScenario(action="REDUCE_START_BLOCK", target_activity_id="A100", reduction_days=3, evidence_chunk_ids=[1]),
            RecoveryScenario(action="REDUCE_ACTIVITY_DURATION", target_activity_id="A100", reduction_days=2, evidence_chunk_ids=[2]),
            RecoveryScenario(action="REDUCE_START_BLOCK", target_activity_id="A100", reduction_days=5, evidence_chunk_ids=[]),
        ]
    )


def test_valid_outputs_pass() -> None:
    result = validate_agent_outputs(
        _valid_mapping(), _valid_plan(), allowed_activity_ids={"A100", "A200"}, allowed_chunk_ids={1, 2}
    )

    assert result.passed is True
    assert result.requires_human_confirmation is False
    assert result.violations == []


def test_activity_outside_allowlist_flagged() -> None:
    mapping = _valid_mapping()
    mapping.ranked_candidates.append(RankedCandidate(activity_id="GHOST", confidence=0.1))

    result = validate_agent_outputs(
        mapping, _valid_plan(), allowed_activity_ids={"A100", "A200"}, allowed_chunk_ids={1, 2}
    )

    assert result.passed is False
    assert any(v.code == "activity_not_in_allowlist" for v in result.violations)


def test_evidence_outside_allowlist_flagged() -> None:
    mapping = _valid_mapping()
    mapping.evidence_chunk_ids = [1, 99]

    result = validate_agent_outputs(
        mapping, _valid_plan(), allowed_activity_ids={"A100", "A200"}, allowed_chunk_ids={1, 2}
    )

    assert result.passed is False
    assert any(v.code == "evidence_not_in_allowlist" for v in result.violations)


def test_wrong_scenario_count_flagged() -> None:
    plan = RecoveryPlanResult(
        scenarios=[
            RecoveryScenario(action="REDUCE_START_BLOCK", target_activity_id="A100", reduction_days=1),
        ]
    )

    result = validate_agent_outputs(
        _valid_mapping(), plan, allowed_activity_ids={"A100", "A200"}, allowed_chunk_ids={1, 2}
    )

    assert result.passed is False
    assert any(v.code == "invalid_scenario_count" for v in result.violations)


def test_scenario_activity_outside_allowlist_flagged() -> None:
    plan = _valid_plan()
    plan.scenarios[0].target_activity_id = "GHOST"

    result = validate_agent_outputs(
        _valid_mapping(), plan, allowed_activity_ids={"A100", "A200"}, allowed_chunk_ids={1, 2}
    )

    assert any(v.code == "scenario_activity_not_in_allowlist" for v in result.violations)


def test_low_confidence_requires_human_confirmation() -> None:
    mapping = _valid_mapping()
    mapping.ranked_candidates = [
        RankedCandidate(activity_id="A100", confidence=0.60),
        RankedCandidate(activity_id="A200", confidence=0.55),
    ]

    result = validate_agent_outputs(
        mapping, _valid_plan(), allowed_activity_ids={"A100", "A200"}, allowed_chunk_ids={1, 2}
    )

    assert result.requires_human_confirmation is True


def test_missing_information_requires_human_confirmation() -> None:
    mapping = _valid_mapping()
    mapping.missing_information = ["delay duration unknown"]

    result = validate_agent_outputs(
        mapping, _valid_plan(), allowed_activity_ids={"A100", "A200"}, allowed_chunk_ids={1, 2}
    )

    assert result.requires_human_confirmation is True


def test_summary_serializes_violations() -> None:
    mapping = _valid_mapping()
    mapping.evidence_chunk_ids = [99]

    result = validate_agent_outputs(
        mapping, None, allowed_activity_ids={"A100", "A200"}, allowed_chunk_ids={1, 2}
    )
    summary = result.to_summary()

    assert summary["passed"] is False
    assert summary["violations"][0]["code"] == "evidence_not_in_allowlist"
