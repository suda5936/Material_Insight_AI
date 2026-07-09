"""Review Agent — 독립 검토(LLM-as-a-judge) 체인.

[수업 정리] LLM-as-a-judge 패턴 + graceful degradation.
------------------------------------------------------------------
다른 에이전트의 결과(mapping/plan/rule validation)를 "제3의 모델"이 검토해 경고를 낸다.
LangChain으로 치면 평가용 체인 하나를 더 두는 것(평가/critique 체인).

두 가지 학습 포인트:
  1) 검토자는 절대 계산 결과를 수정하지 않는다 — warning만 생성(조언자 역할).
  2) graceful degradation: 검토 모델이 죽거나 이상한 출력을 줘도 파이프라인을
     막지 않고 "needs_human_review=True"로 안전하게 폴백한다. 검토가 실패하면
     '더 보수적으로(사람에게 넘김)' 동작하는 게 안전하기 때문.
  3) 모델 라우팅: REVIEWER=vLLM Gemma, 실패 시 registry가 OpenAI로 fallback.
"""

import logging

from pydantic import ValidationError

from app.prompts.reviewer_prompt import REVIEWER_SYSTEM_PROMPT, build_reviewer_user_prompt
from app.services.agents.schemas import ReviewResult, ReviewWarning
from app.services.llm.json_repair import LLMJsonParseError, parse_llm_json
from app.services.llm.registry import LLMProviderRegistry
from app.services.llm.types import LLMMessage, LLMProviderError, LLMResponse, LLMRole

logger = logging.getLogger("app.agents.reviewer")


class ReviewAgent:
    def __init__(self, registry: LLMProviderRegistry) -> None:
        self._registry = registry
        self.last_response: LLMResponse | None = None

    async def run(
        self,
        mapping_summary: dict,
        plan_summary: dict,
        rule_validation_summary: dict,
    ) -> ReviewResult:
        messages = [
            LLMMessage(role="system", content=REVIEWER_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=build_reviewer_user_prompt(
                    mapping_summary, plan_summary, rule_validation_summary
                ),
            ),
        ]

        # The reviewer must never block the pipeline: if it is unavailable or
        # returns garbage, fall back to a conservative "needs human review".
        try:
            response = await self._registry.complete(LLMRole.REVIEWER, messages)
            self.last_response = response
            payload = parse_llm_json(response.content)
            return ReviewResult.model_validate(payload)
        except (LLMProviderError, LLMJsonParseError, ValidationError) as exc:
            logger.warning("Review agent failed; defaulting to needs_human_review. %s", exc)
            return ReviewResult(
                warnings=[
                    ReviewWarning(
                        category="reviewer_unavailable",
                        message="The review agent could not be completed automatically.",
                    )
                ],
                needs_human_review=True,
                summary="Automatic review unavailable; human review required.",
            )
