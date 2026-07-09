"""가드레일(Guardrails) 시스템.

[수업 정리] 가드레일이란?
------------------------------------------------------------------
LLM 애플리케이션에서 "가드레일"은 모델 입출력 주위에 두르는 **안전/검증 계층**이다.
LangChain 자체에는 완성형 가드레일이 내장돼 있지 않고, 보통 아래 도구/개념을 조합한다.
  - NeMo Guardrails, Guardrails-AI, Rebuff(prompt-injection 탐지) 같은 외부 라이브러리
  - LangChain의 OutputParser / PydanticOutputParser 로 "출력 형식" 강제
  - 커스텀 RunnableLambda 로 입력/출력 검사 노드를 체인 중간에 삽입

가드레일은 크게 두 종류다.
  1) Input Guardrail  : LLM에 넣기 "전" 사용자 입력을 검사 (빈 값, 길이, prompt injection)
  2) Output Guardrail : LLM이 뱉은 "후" 출력을 검사 (형식, 금지 내용, 환각 방지)

이 파일은 두 가드레일을 프레임워크 없이 직접 구현한 것이다.
프로젝트의 다른 방어선(Rule Validator, evidence allowlist, human-in-the-loop)과 함께
"다층 방어(defense in depth)"를 이룬다.
  - guardrails.py      : 입력 위생 + LLM이 일정수치를 계산하지 못하게 막는 출력 검사
  - agents/rule_validator.py : 비즈니스 규칙(allowlist, action type, confidence) 검사
  - agents/human_selection.py: 사람 확인이 필요한 경우 자동 진행 차단
"""

import re
from dataclasses import dataclass

# 설계 11절: LLM이 절대 "계산"하면 안 되는 일정 수치 필드들.
# 일정 계산은 결정론적 CPM 엔진(schedule_engine.py)만 수행한다.
# LLM 출력 JSON에 이런 키가 나타나면 = 모델이 계산을 시도한 것 → 가드레일이 차단.
FORBIDDEN_COMPUTED_FIELDS = {
    "es",
    "ef",
    "ls",
    "lf",
    "total_float",
    "float",
    "project_duration",
    "project_delay",
    "project_delay_days",
    "recovered_days",
    "critical_path",
    "is_critical",
}

# prompt injection 휴리스틱 패턴.
# [수업 정리] prompt injection = 사용자 입력에 "이전 지시를 무시하라" 같은 문구를 심어
# 시스템 프롬프트를 무력화하려는 공격. 완벽 탐지는 불가능하며, 여기서는 대표 패턴만 잡는
# 얕은(heuristic) 방어다. 실제 서비스라면 Rebuff/LLM-judge 등을 함께 쓴다.
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(above|system)", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"이전\s*지시\w*\s*(을|를)?\s*무시", re.IGNORECASE),
    re.compile(r"시스템\s*프롬프트", re.IGNORECASE),
]

MAX_ISSUE_LENGTH = 4000
MIN_ISSUE_LENGTH = 5


@dataclass(frozen=True)
class GuardrailViolation:
    code: str
    message: str


@dataclass(frozen=True)
class GuardrailResult:
    passed: bool
    violations: list[GuardrailViolation]

    def to_summary(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "violations": [{"code": v.code, "message": v.message} for v in self.violations],
        }


# --- Input Guardrail -------------------------------------------------------------


def check_issue_input(issue_text: str) -> GuardrailResult:
    """LLM(Issue Mapping Agent)에 넣기 전에 사용자 자연어 이슈를 검사한다.

    LangChain으로 치면 체인 맨 앞에 두는 RunnableLambda 검증 노드에 해당한다.
        chain = check_input | prompt | llm | parser
    """
    violations: list[GuardrailViolation] = []
    text = (issue_text or "").strip()

    if len(text) < MIN_ISSUE_LENGTH:
        violations.append(
            GuardrailViolation("issue_too_short", "이슈 내용이 너무 짧습니다.")
        )
    if len(text) > MAX_ISSUE_LENGTH:
        violations.append(
            GuardrailViolation(
                "issue_too_long", f"이슈 내용이 최대 길이({MAX_ISSUE_LENGTH}자)를 초과했습니다."
            )
        )
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            violations.append(
                GuardrailViolation(
                    "prompt_injection_suspected",
                    "프롬프트 인젝션으로 의심되는 문구가 감지되었습니다.",
                )
            )
            break

    return GuardrailResult(passed=len(violations) == 0, violations=violations)


# --- Output Guardrail ------------------------------------------------------------


def _forbidden_keys_in(payload: object) -> list[str]:
    """중첩 dict/list를 재귀 순회하며 금지된 계산 필드 키를 찾는다."""
    found: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(key, str) and key.strip().lower() in FORBIDDEN_COMPUTED_FIELDS:
                found.append(key)
            found.extend(_forbidden_keys_in(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_forbidden_keys_in(item))
    return found


def check_agent_output_no_computed_fields(raw_payload: dict) -> GuardrailResult:
    """에이전트가 반환한 원본 JSON에 "계산 결과" 필드가 섞여 있지 않은지 검사한다.

    [왜 필요한가] Pydantic 스키마는 extra="ignore"라 모델이 몰래 넣은 total_float 같은
    키를 그냥 버릴 뿐 "차단"하진 않는다. 가드레일은 원본 payload 단계에서 이를 적발해
    "LLM은 일정 수치를 계산하지 않는다"는 설계 불변식을 강제한다(defense in depth).
    """
    forbidden = _forbidden_keys_in(raw_payload)
    if forbidden:
        return GuardrailResult(
            passed=False,
            violations=[
                GuardrailViolation(
                    "llm_attempted_schedule_calculation",
                    f"LLM 출력에 계산 금지 필드가 포함됨: {sorted(set(forbidden))}",
                )
            ],
        )
    return GuardrailResult(passed=True, violations=[])
