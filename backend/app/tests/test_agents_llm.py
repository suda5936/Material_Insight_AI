import json

import pytest

from app.services.agents.mapper import IssueMappingAgent
from app.services.agents.planner import RecoveryPlanningAgent
from app.services.agents.reviewer import ReviewAgent
from app.services.agents.schemas import (
    ActivityCandidate,
    AgentOutputError,
    EvidenceChunk,
    ImpactMode,
    RecoveryActionType,
)
from app.services.llm.registry import LLMProviderRegistry
from app.services.llm.types import LLMRole
from app.tests.fakes import FakeLLMProvider


def _mapper_registry(content: str) -> tuple[LLMProviderRegistry, FakeLLMProvider]:
    fake = FakeLLMProvider(name="fake-mapper", response_content=content)
    return LLMProviderRegistry({LLMRole.ISSUE_MAPPER: fake}, {}), fake


def _planner_registry(content: str) -> LLMProviderRegistry:
    fake = FakeLLMProvider(name="fake-planner", response_content=content)
    return LLMProviderRegistry({LLMRole.RECOVERY_PLANNER: fake}, {})


CANDIDATES = [
    ActivityCandidate(activity_id="A100", name="Curtain wall install", is_completed=False),
    ActivityCandidate(activity_id="A200", name="Structure", is_completed=False),
]
EVIDENCE = [EvidenceChunk(chunk_id=1, content="curtain wall delayed", trade="curtain wall", location="A-12F")]


# --- Issue Mapping Agent ---------------------------------------------------------


async def test_mapper_parses_valid_output() -> None:
    content = json.dumps(
        {
            "issue_type": "material_delay",
            "location": "A-12F",
            "trade": "curtain wall",
            "delay_days": 10,
            "impact_mode": "START_BLOCK",
            "ranked_candidates": [{"activity_id": "A100", "confidence": 0.9, "reason": "matches trade"}],
            "evidence_chunk_ids": [1],
            "missing_information": [],
            "overall_confidence": 0.9,
        }
    )
    registry, fake = _mapper_registry(content)
    agent = IssueMappingAgent(registry)

    result = await agent.run("A동 12층 커튼월 자재 10일 지연", CANDIDATES, EVIDENCE)

    assert result.impact_mode == ImpactMode.START_BLOCK
    assert result.delay_days == 10
    assert result.ranked_candidates[0].activity_id == "A100"
    assert len(fake.calls) == 1


async def test_mapper_handles_code_fenced_json() -> None:
    content = "```json\n" + json.dumps(
        {"impact_mode": "DURATION_INCREASE", "ranked_candidates": [], "overall_confidence": 0.5}
    ) + "\n```"
    registry, _ = _mapper_registry(content)
    agent = IssueMappingAgent(registry)

    result = await agent.run("issue", CANDIDATES, EVIDENCE)

    assert result.impact_mode == ImpactMode.DURATION_INCREASE


async def test_mapper_clamps_confidence() -> None:
    content = json.dumps(
        {
            "impact_mode": "START_BLOCK",
            "ranked_candidates": [{"activity_id": "A100", "confidence": 1.7}],
            "overall_confidence": 5.0,
        }
    )
    registry, _ = _mapper_registry(content)
    agent = IssueMappingAgent(registry)

    result = await agent.run("issue", CANDIDATES, EVIDENCE)

    assert result.ranked_candidates[0].confidence == 1.0
    assert result.overall_confidence == 1.0


async def test_mapper_raises_on_unparsable_output() -> None:
    registry, _ = _mapper_registry("totally not json")
    agent = IssueMappingAgent(registry)

    with pytest.raises(AgentOutputError):
        await agent.run("issue", CANDIDATES, EVIDENCE)


# --- Recovery Planning Agent -----------------------------------------------------


def _three_scenarios() -> str:
    return json.dumps(
        {
            "scenarios": [
                {"action": "REDUCE_START_BLOCK", "target_activity_id": "A100", "reduction_days": 3, "evidence_chunk_ids": [1]},
                {"action": "REDUCE_ACTIVITY_DURATION", "target_activity_id": "A100", "reduction_days": 2, "evidence_chunk_ids": []},
                {"action": "REDUCE_START_BLOCK", "target_activity_id": "A100", "reduction_days": 5, "evidence_chunk_ids": []},
            ]
        }
    )


async def test_planner_parses_exactly_three_scenarios() -> None:
    agent = RecoveryPlanningAgent(_planner_registry(_three_scenarios()))

    result = await agent.run("A100", {"project_delay_days": 10}, 10, EVIDENCE)

    assert len(result.scenarios) == 3
    assert result.scenarios[0].action == RecoveryActionType.REDUCE_START_BLOCK


async def test_planner_rejects_wrong_scenario_count() -> None:
    content = json.dumps(
        {"scenarios": [{"action": "REDUCE_START_BLOCK", "target_activity_id": "A100", "reduction_days": 1}]}
    )
    agent = RecoveryPlanningAgent(_planner_registry(content))

    with pytest.raises(AgentOutputError):
        await agent.run("A100", {}, 10, EVIDENCE)


async def test_planner_rejects_invalid_action_type() -> None:
    content = json.dumps(
        {
            "scenarios": [
                {"action": "DELETE_ACTIVITY", "target_activity_id": "A100", "reduction_days": 1},
                {"action": "REDUCE_START_BLOCK", "target_activity_id": "A100", "reduction_days": 1},
                {"action": "REDUCE_START_BLOCK", "target_activity_id": "A100", "reduction_days": 1},
            ]
        }
    )
    agent = RecoveryPlanningAgent(_planner_registry(content))

    with pytest.raises(AgentOutputError):
        await agent.run("A100", {}, 10, EVIDENCE)


# --- Review Agent ----------------------------------------------------------------


async def test_reviewer_parses_valid_output() -> None:
    content = json.dumps(
        {
            "warnings": [{"category": "evidence", "message": "weak evidence"}],
            "needs_human_review": True,
            "summary": "needs human check",
        }
    )
    fake = FakeLLMProvider(name="fake-reviewer", response_content=content)
    registry = LLMProviderRegistry({LLMRole.REVIEWER: fake}, {})
    agent = ReviewAgent(registry)

    result = await agent.run({"a": 1}, {"b": 2}, {"passed": True})

    assert result.needs_human_review is True
    assert result.warnings[0].category == "evidence"


async def test_reviewer_falls_back_to_needs_human_review_on_failure() -> None:
    fake = FakeLLMProvider(name="fake-reviewer", fail=True)
    registry = LLMProviderRegistry({LLMRole.REVIEWER: fake}, {})
    agent = ReviewAgent(registry)

    result = await agent.run({}, {}, {})

    assert result.needs_human_review is True
    assert result.warnings[0].category == "reviewer_unavailable"


async def test_reviewer_falls_back_on_unparsable_output() -> None:
    fake = FakeLLMProvider(name="fake-reviewer", response_content="not json")
    registry = LLMProviderRegistry({LLMRole.REVIEWER: fake}, {})
    agent = ReviewAgent(registry)

    result = await agent.run({}, {}, {})

    assert result.needs_human_review is True
