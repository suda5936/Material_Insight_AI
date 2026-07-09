"""에이전트 입출력 스키마 — Structured Output.

[수업 정리] LangChain의 구조화 출력(Structured Output).
------------------------------------------------------------------
LLM이 자유 텍스트가 아니라 "정해진 스키마의 JSON"을 뱉게 하고, 그걸 Pydantic으로
검증/파싱하는 패턴. LangChain 대응:
    from langchain_core.output_parsers import PydanticOutputParser
    parser = PydanticOutputParser(pydantic_object=IssueMappingResult)
    # 또는 llm.with_structured_output(IssueMappingResult)

여기서 정의한 Pydantic 모델들이 각 에이전트의 "출력 계약(contract)"이다.
포인트:
  - extra="ignore" : LLM이 여분 키를 넣어도 무시(파싱 견고성). 단, 계산 금지 필드
    차단은 guardrails.py가 별도로 담당한다(스키마는 버리기만 하지 막지는 못하므로).
  - Enum(ImpactMode/RecoveryActionType) : 허용된 값만 통과시키는 1차 방어선.
  - field_validator : confidence를 [0,1]로 clamp 하는 등 값 위생 처리.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentOutputError(Exception):
    """Raised when an agent's LLM output cannot be coerced into the expected shape."""


class ImpactMode(str, Enum):
    START_BLOCK = "START_BLOCK"
    DURATION_INCREASE = "DURATION_INCREASE"


class RecoveryActionType(str, Enum):
    REDUCE_START_BLOCK = "REDUCE_START_BLOCK"
    REDUCE_ACTIVITY_DURATION = "REDUCE_ACTIVITY_DURATION"


class _LenientModel(BaseModel):
    """LLM outputs may carry extra keys; ignore them rather than failing."""

    model_config = ConfigDict(extra="ignore")


# --- Inputs shared across agents -------------------------------------------------


class ActivityCandidate(_LenientModel):
    activity_id: str
    name: str
    is_completed: bool = False


class EvidenceChunk(_LenientModel):
    chunk_id: int
    content: str
    source_name: str = ""
    trade: str = ""
    location: str = ""


# --- Issue Mapping Agent ---------------------------------------------------------


class RankedCandidate(_LenientModel):
    activity_id: str
    confidence: float
    reason: str = ""

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class IssueMappingResult(_LenientModel):
    issue_type: str = ""
    location: str | None = None
    trade: str | None = None
    delay_days: int | None = None
    impact_mode: ImpactMode = ImpactMode.START_BLOCK
    ranked_candidates: list[RankedCandidate] = Field(default_factory=list)
    evidence_chunk_ids: list[int] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    overall_confidence: float = 0.0

    @field_validator("overall_confidence")
    @classmethod
    def clamp_overall(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


# --- Recovery Planning Agent -----------------------------------------------------


class RecoveryScenario(_LenientModel):
    action: RecoveryActionType
    target_activity_id: str
    reduction_days: int
    rationale: str = ""
    evidence_chunk_ids: list[int] = Field(default_factory=list)

    @field_validator("reduction_days")
    @classmethod
    def non_negative_reduction(cls, value: int) -> int:
        if value < 0:
            raise ValueError("reduction_days must not be negative.")
        return value


class RecoveryPlanResult(_LenientModel):
    scenarios: list[RecoveryScenario] = Field(default_factory=list)


# --- Review Agent ----------------------------------------------------------------


class ReviewWarning(_LenientModel):
    category: str
    message: str


class ReviewResult(_LenientModel):
    warnings: list[ReviewWarning] = Field(default_factory=list)
    needs_human_review: bool = False
    summary: str = ""
