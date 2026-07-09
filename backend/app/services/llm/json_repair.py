"""LLM JSON 출력 파싱/복구 — Output Parser.

[수업 정리] LangChain의 Output Parser 계열.
------------------------------------------------------------------
LLM에게 "JSON만 반환하라"고 해도 실제로는 ```json 코드펜스로 감싸거나 앞뒤에
설명 문장을 붙이는 경우가 많다. LangChain은 이를 위해:
    - JsonOutputParser         : JSON 파싱
    - OutputFixingParser       : 깨진 출력을 LLM으로 재수선
    - StructuredOutputParser   : 스키마 기반 파싱
를 제공한다.

parse_llm_json()은 그 중 "코드펜스 제거 + 첫 균형 JSON 객체 추출" 수준의 견고한
파서를 직접 구현한 것이다(네트워크 재호출 없는 결정론적 복구). 스키마 검증은
그 다음 단계에서 Pydantic(structured output)이 담당한다.
"""

import json
import re

_CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


class LLMJsonParseError(Exception):
    pass


def _strip_code_fences(text: str) -> str:
    return _CODE_FENCE_PATTERN.sub("", text.strip()).strip()


def _extract_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None


def parse_llm_json(text: str) -> dict:
    """Best-effort JSON parsing for LLM output: strips markdown code fences
    and falls back to extracting the first balanced {...} object."""
    cleaned = _strip_code_fences(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    extracted = _extract_first_json_object(cleaned)
    if extracted is not None:
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass

    raise LLMJsonParseError(f"Could not parse JSON from LLM output: {text!r}")
