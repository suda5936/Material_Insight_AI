"""Rule Validator — 비즈니스 규칙 가드레일(출력 검증).

[수업 정리] LLM 출력에 대한 규칙 기반 Output Guardrail.
------------------------------------------------------------------
guardrails.py가 "입력 위생 + 계산금지 필드"를 본다면, 여기는 "비즈니스 규칙"을 본다:
  - 인용한 activity_id / evidence chunk_id 가 allowlist 안에 있는가 (환각 차단)
  - 복구 action type이 허용 집합(REDUCE_START_BLOCK/REDUCE_ACTIVITY_DURATION)인가
  - 시나리오 개수가 정확히 3개인가
  - confidence가 낮거나 missing_information이 있으면 human confirmation 요구

LangChain에는 이런 도메인 규칙 검증이 내장돼 있지 않아 후처리로 직접 만든다.
이 검증기는 "순수 함수"(LLM 미사용)라 결정론적이고 테스트가 쉽다.
"""

from dataclasses import dataclass, field

from app.services.agents.human_selection import (
    MIN_CONFIDENCE_MARGIN,
    MIN_TOP1_CONFIDENCE,
)
from app.services.agents.schemas import (
    IssueMappingResult,
    RecoveryActionType,
    RecoveryPlanResult,
)

REQUIRED_SCENARIO_COUNT = 3
ALLOWED_ACTIONS = {RecoveryActionType.REDUCE_START_BLOCK, RecoveryActionType.REDUCE_ACTIVITY_DURATION}


@dataclass(frozen=True)
class RuleViolation:
    code: str
    message: str
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleValidationResult:
    passed: bool
    requires_human_confirmation: bool
    violations: list[RuleViolation]

    def to_summary(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "requires_human_confirmation": self.requires_human_confirmation,
            "violations": [
                {"code": v.code, "message": v.message, "details": v.details}
                for v in self.violations
            ],
        }


def validate_agent_outputs(
    mapping: IssueMappingResult,
    plan: RecoveryPlanResult | None,
    allowed_activity_ids: set[str],
    allowed_chunk_ids: set[int],
) -> RuleValidationResult:
    violations: list[RuleViolation] = []

    # --- Mapping: activity id allowlist ---
    for candidate in mapping.ranked_candidates:
        if candidate.activity_id not in allowed_activity_ids:
            violations.append(
                RuleViolation(
                    code="activity_not_in_allowlist",
                    message="Mapping cited an activity_id outside the candidate allowlist.",
                    details={"activity_id": candidate.activity_id},
                )
            )

    # --- Mapping: evidence chunk allowlist ---
    for chunk_id in mapping.evidence_chunk_ids:
        if chunk_id not in allowed_chunk_ids:
            violations.append(
                RuleViolation(
                    code="evidence_not_in_allowlist",
                    message="Mapping cited an evidence chunk_id outside the retrieved allowlist.",
                    details={"chunk_id": chunk_id},
                )
            )

    # --- Plan checks ---
    if plan is not None:
        if len(plan.scenarios) != REQUIRED_SCENARIO_COUNT:
            violations.append(
                RuleViolation(
                    code="invalid_scenario_count",
                    message=f"Recovery plan must contain exactly {REQUIRED_SCENARIO_COUNT} scenarios.",
                    details={"count": len(plan.scenarios)},
                )
            )
        for index, scenario in enumerate(plan.scenarios):
            if scenario.action not in ALLOWED_ACTIONS:
                violations.append(
                    RuleViolation(
                        code="invalid_recovery_action",
                        message="Recovery scenario used a disallowed action type.",
                        details={"index": index, "action": str(scenario.action)},
                    )
                )
            if scenario.target_activity_id not in allowed_activity_ids:
                violations.append(
                    RuleViolation(
                        code="scenario_activity_not_in_allowlist",
                        message="Recovery scenario targeted an activity outside the allowlist.",
                        details={"index": index, "activity_id": scenario.target_activity_id},
                    )
                )
            for chunk_id in scenario.evidence_chunk_ids:
                if chunk_id not in allowed_chunk_ids:
                    violations.append(
                        RuleViolation(
                            code="evidence_not_in_allowlist",
                            message="Recovery scenario cited an evidence chunk_id outside the allowlist.",
                            details={"index": index, "chunk_id": chunk_id},
                        )
                    )

    requires_human_confirmation = _requires_human_confirmation(mapping)

    return RuleValidationResult(
        passed=len(violations) == 0,
        requires_human_confirmation=requires_human_confirmation,
        violations=violations,
    )


def _requires_human_confirmation(mapping: IssueMappingResult) -> bool:
    ordered = sorted(mapping.ranked_candidates, key=lambda c: c.confidence, reverse=True)
    if not ordered:
        return True
    top1 = ordered[0].confidence
    top2 = ordered[1].confidence if len(ordered) > 1 else 0.0
    if top1 < MIN_TOP1_CONFIDENCE:
        return True
    if (top1 - top2) < MIN_CONFIDENCE_MARGIN:
        return True
    if mapping.missing_information:
        return True
    return False
