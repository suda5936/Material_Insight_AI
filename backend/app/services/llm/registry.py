"""LLM 라우팅 + Fallback — 모델 선택 레지스트리.

[수업 정리] 역할별 모델 라우팅과 fallback.
------------------------------------------------------------------
서로 다른 작업에 서로 다른 모델을 쓰는 게 실무 패턴이다(비용/성능/정확도 트레이드오프).
  - Mapper(구조화)  → vLLM Gemma  (사내 모델, 저렴)
  - Planner(추론)   → OpenAI      (고품질 추론 필요)
  - Reviewer(검토)  → vLLM Gemma  + 실패 시 OpenAI로 fallback

LangChain 대응:
  - 역할별 모델 선택 ↔ RunnableBranch / configurable_alternatives 로 라우팅
  - fallback        ↔ runnable.with_fallbacks([backup_llm])
LLMProviderRegistry는 이 "라우터 + fallback"을 직접 구현한 것이다.
role → provider 딕셔너리로 라우팅하고, primary 실패 시 fallbacks[role]로 재시도한다.
"""

import logging

from app.core.config import get_settings
from app.services.llm.openai_compatible import OpenAICompatibleProvider
from app.services.llm.types import LLMMessage, LLMProvider, LLMProviderError, LLMResponse, LLMRole

logger = logging.getLogger("app.llm")


class LLMProviderRegistry:
    """역할(LLMRole)별 모델 라우터. LangChain의 configurable_alternatives + with_fallbacks."""

    def __init__(self, providers: dict[LLMRole, LLMProvider], fallbacks: dict[LLMRole, LLMProvider]) -> None:
        self._providers = providers
        self._fallbacks = fallbacks

    def get(self, role: LLMRole) -> LLMProvider:
        return self._providers[role]

    async def complete(
        self,
        role: LLMRole,
        messages: list[LLMMessage],
        temperature: float = 0.0,
    ) -> LLMResponse:
        # 1) 역할에 매핑된 primary 모델 호출
        primary = self._providers[role]
        try:
            return await primary.complete(messages, temperature=temperature)
        except LLMProviderError:
            # 2) primary 실패 시 fallback 모델로 재시도 (with_fallbacks 패턴)
            fallback = self._fallbacks.get(role)
            if fallback is None:
                raise
            logger.warning(
                "Primary provider '%s' failed for role '%s'; falling back to '%s'.",
                primary.name,
                role.value,
                fallback.name,
            )
            return await fallback.complete(messages, temperature=temperature)


def build_default_registry() -> LLMProviderRegistry:
    settings = get_settings()

    openai_provider = OpenAICompatibleProvider(
        name="openai",
        base_url="https://api.openai.com/v1",
        model=settings.openai_model,
        api_key=settings.openai_api_key,
    )
    gemma_provider = OpenAICompatibleProvider(
        name="vllm-gemma",
        base_url=settings.vllm_gemma_base_url,
        model=settings.vllm_gemma_model,
    )

    # Mapper와 Reviewer는 동일한 vLLM Gemma를 사용한다(Qwen 미사용).
    providers: dict[LLMRole, LLMProvider] = {
        LLMRole.ISSUE_MAPPER: gemma_provider,
        LLMRole.RECOVERY_PLANNER: openai_provider,
        LLMRole.REVIEWER: gemma_provider,
    }
    fallbacks: dict[LLMRole, LLMProvider] = {
        LLMRole.REVIEWER: openai_provider,
    }

    return LLMProviderRegistry(providers, fallbacks)


def provide_llm_registry() -> LLMProviderRegistry:
    """FastAPI dependency entry point; override in tests via app.dependency_overrides."""
    return build_default_registry()
