"""Issue Mapping Agent — 프롬프트→LLM→파서 체인(LCEL).

[수업 정리] LangChain의 체인(Chain) = prompt | llm | parser.
------------------------------------------------------------------
LCEL(LangChain Expression Language) 로 표현하면 이 에이전트는 사실상:
    chain = mapper_prompt | gemma_llm | PydanticOutputParser(IssueMappingResult)
    result = chain.invoke({"issue": ..., "candidates": ..., "evidence": ...})

run() 안의 순서가 정확히 그 체인이다:
    1) 프롬프트 구성 (system + user)      ← PromptTemplate
    2) registry.complete(ISSUE_MAPPER)   ← LLM 호출(라우팅으로 vLLM Gemma 선택)
    3) parse_llm_json → Pydantic 검증     ← OutputParser

[에이전트 제한 = 프롬프트 하드룰] 후보/근거 밖 ID 생성 금지, critical/지연일 계산 금지.
이건 프롬프트로 "요청"하고, 실제 "강제"는 Rule Validator/guardrails가 한다(신뢰하되 검증).
"""

from pydantic import ValidationError

from app.prompts.mapper_prompt import MAPPER_SYSTEM_PROMPT, build_mapper_user_prompt
from app.services.agents.schemas import (
    ActivityCandidate,
    AgentOutputError,
    EvidenceChunk,
    IssueMappingResult,
)
from app.services.llm.json_repair import LLMJsonParseError, parse_llm_json
from app.services.llm.registry import LLMProviderRegistry
from app.services.llm.types import LLMMessage, LLMResponse, LLMRole


class IssueMappingAgent:
    def __init__(self, registry: LLMProviderRegistry) -> None:
        self._registry = registry
        self.last_response: LLMResponse | None = None

    async def run(
        self,
        issue_text: str,
        candidates: list[ActivityCandidate],
        evidence: list[EvidenceChunk],
    ) -> IssueMappingResult:
        messages = [
            LLMMessage(role="system", content=MAPPER_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=build_mapper_user_prompt(issue_text, candidates, evidence),
            ),
        ]
        # LLM 호출 (registry가 ISSUE_MAPPER 역할 → vLLM Gemma로 라우팅)
        response = await self._registry.complete(LLMRole.ISSUE_MAPPER, messages)
        self.last_response = response  # 원문 보존(agent_runs trace + 출력 가드레일용)

        # OutputParser 1단계: 코드펜스 제거 등 JSON 복구
        try:
            payload = parse_llm_json(response.content)
        except LLMJsonParseError as exc:
            raise AgentOutputError(f"Issue mapper returned unparsable JSON: {exc}") from exc

        # OutputParser 2단계: Pydantic 스키마 검증(structured output)
        try:
            return IssueMappingResult.model_validate(payload)
        except ValidationError as exc:
            raise AgentOutputError(f"Issue mapper output failed validation: {exc}") from exc
