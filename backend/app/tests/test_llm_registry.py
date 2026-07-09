import pytest

from app.services.llm.registry import LLMProviderRegistry, build_default_registry
from app.services.llm.types import LLMMessage, LLMProviderError, LLMRole
from app.tests.fakes import FakeLLMProvider


async def test_registry_uses_primary_provider_when_healthy() -> None:
    primary = FakeLLMProvider(name="primary", response_content="ok")
    registry = LLMProviderRegistry({LLMRole.REVIEWER: primary}, {})

    response = await registry.complete(LLMRole.REVIEWER, [LLMMessage(role="user", content="hi")])

    assert response.provider_name == "primary"
    assert len(primary.calls) == 1


async def test_registry_falls_back_when_primary_fails() -> None:
    primary = FakeLLMProvider(name="primary", fail=True)
    fallback = FakeLLMProvider(name="fallback", response_content="ok")
    registry = LLMProviderRegistry({LLMRole.REVIEWER: primary}, {LLMRole.REVIEWER: fallback})

    response = await registry.complete(LLMRole.REVIEWER, [LLMMessage(role="user", content="hi")])

    assert response.provider_name == "fallback"


async def test_registry_raises_when_primary_fails_without_fallback() -> None:
    primary = FakeLLMProvider(name="primary", fail=True)
    registry = LLMProviderRegistry({LLMRole.ISSUE_MAPPER: primary}, {})

    with pytest.raises(LLMProviderError):
        await registry.complete(LLMRole.ISSUE_MAPPER, [LLMMessage(role="user", content="hi")])


def test_build_default_registry_wires_all_roles() -> None:
    registry = build_default_registry()

    assert registry.get(LLMRole.ISSUE_MAPPER).name == "vllm-gemma"
    assert registry.get(LLMRole.RECOVERY_PLANNER).name == "openai"
    assert registry.get(LLMRole.REVIEWER).name == "vllm-gemma"
