"""Recovery Planning Agent — 추론 체인(prompt→LLM→parser).

[수업 정리] 또 하나의 LCEL 체인이지만 "추론" 성격이 강해 OpenAI로 라우팅한다.
------------------------------------------------------------------
    chain = planner_prompt | openai_llm | PydanticOutputParser(RecoveryPlanResult)

핵심 설계 제약:
  - "정확히 3개" 시나리오 → run()에서 개수를 강제(아니면 AgentOutputError).
  - LLM은 일정 수치(recovered_days 등)를 "계산"하지 않는다. reduction_days 같은
    "제안 입력값"만 낸다. 실제 recovered_days는 결정론적 엔진이 시뮬레이션으로 구한다.
    (프롬프트로 요청 + guardrails 출력검사 + 엔진 재계산의 3중 방어)
  - impact 결과는 이미 계산된 값을 프롬프트로 "주입"한다(엔진 → 프롬프트 컨텍스트).
"""

from pydantic import ValidationError

from app.prompts.planner_prompt import PLANNER_SYSTEM_PROMPT, build_planner_user_prompt
from app.services.agents.schemas import (
    AgentOutputError,
    EvidenceChunk,
    RecoveryPlanResult,
)
from app.services.llm.json_repair import LLMJsonParseError, parse_llm_json
from app.services.llm.registry import LLMProviderRegistry
from app.services.llm.types import LLMMessage, LLMResponse, LLMRole

REQUIRED_SCENARIO_COUNT = 3


class RecoveryPlanningAgent:
    def __init__(self, registry: LLMProviderRegistry) -> None:
        self._registry = registry
        self.last_response: LLMResponse | None = None

    async def run(
        self,
        target_activity_id: str,
        impact_summary: dict,
        issue_delay_days: int | None,
        evidence: list[EvidenceChunk],
    ) -> RecoveryPlanResult:
        messages = [
            LLMMessage(role="system", content=PLANNER_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=build_planner_user_prompt(
                    target_activity_id, impact_summary, issue_delay_days, evidence
                ),
            ),
        ]
        response = await self._registry.complete(LLMRole.RECOVERY_PLANNER, messages)
        self.last_response = response

        try:
            payload = parse_llm_json(response.content)
        except LLMJsonParseError as exc:
            raise AgentOutputError(f"Recovery planner returned unparsable JSON: {exc}") from exc

        try:
            result = RecoveryPlanResult.model_validate(payload)
        except ValidationError as exc:
            raise AgentOutputError(f"Recovery planner output failed validation: {exc}") from exc

        # 설계 8.2: "정확히 3개" 강제. 스키마만으론 개수를 못 막으므로 여기서 검증.
        if len(result.scenarios) != REQUIRED_SCENARIO_COUNT:
            raise AgentOutputError(
                f"Recovery planner must return exactly {REQUIRED_SCENARIO_COUNT} scenarios, "
                f"got {len(result.scenarios)}."
            )

        return result
