"""근거(Evidence) allowlist 검증.

[수업 정리] RAG 환각(hallucination) 방지 = "인용 근거를 검색 결과로 제한".
------------------------------------------------------------------
RAG의 목적은 LLM이 "검색된 문서에 근거해서만" 답하게 하는 것이다. 그런데 LLM은
검색되지 않은 chunk_id를 지어낼 수 있다(환각). 이 함수는 에이전트가 인용한 chunk_id가
반드시 retriever가 실제로 돌려준 집합(allowlist) 안에 있는지 검증한다.

LangChain에는 이걸 강제하는 내장 장치가 없어 보통 후처리로 직접 검사한다.
이 프로젝트에서는 Rule Validator + 이 함수가 함께 "인용 무결성"을 보장한다.
"""

from app.core.errors import APIError


def validate_evidence_chunk_ids(claimed_chunk_ids: list[int], allowed_chunk_ids: list[int]) -> None:
    allowed = set(allowed_chunk_ids)
    unknown = [chunk_id for chunk_id in claimed_chunk_ids if chunk_id not in allowed]
    if unknown:
        raise APIError(
            status_code=422,
            error_code="evidence_not_in_allowlist",
            message="Agent cited evidence chunk ids outside the retrieved allowlist.",
            details={"unknown_chunk_ids": unknown, "allowed_chunk_ids": sorted(allowed)},
        )
