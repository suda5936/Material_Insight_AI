"""LLM 공통 타입 — Chat Model 추상화.

[수업 정리] LangChain의 채팅 모델 인터페이스.
------------------------------------------------------------------
LangChain 대응:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import SystemMessage, HumanMessage
    response = chat_model.invoke([SystemMessage(...), HumanMessage(...)])

여기서 직접 정의한 것:
    - LLMMessage           ↔ SystemMessage / HumanMessage / AIMessage (role 필드로 구분)
    - LLMProvider.complete ↔ BaseChatModel.invoke
    - LLMResponse          ↔ AIMessage (+ 어떤 provider/model이 답했는지 메타)
    - LLMRole              ↔ 우리 파이프라인에서 "어떤 역할의 모델을 쓸지" 구분하는 키
추상 클래스로 두어 OpenAI/vLLM 등 어떤 백엔드든 같은 방식으로 호출한다(전략 패턴).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class LLMRole(str, Enum):
    """에이전트 역할 → 모델 매핑 키. registry가 이 키로 provider를 선택한다."""

    ISSUE_MAPPER = "issue_mapper"
    RECOVERY_PLANNER = "recovery_planner"
    REVIEWER = "reviewer"


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider_name: str


class LLMProviderError(Exception):
    pass


class LLMProvider(ABC):
    """LangChain BaseChatModel 에 해당하는 추상 채팅 모델."""

    name: str

    @abstractmethod
    async def complete(  # ↔ BaseChatModel.invoke
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
    ) -> LLMResponse: ...
