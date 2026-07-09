"""문서 청킹(Text Splitting).

[수업 정리] RAG 파이프라인 1단계 = Document Splitting.
------------------------------------------------------------------
LangChain에서는 `TextSplitter`(예: RecursiveCharacterTextSplitter,
CharacterTextSplitter)가 이 역할을 한다.
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    chunks = splitter.split_text(raw_text)

왜 자르나?
  - 임베딩 모델/LLM 컨텍스트에는 입력 길이 한계가 있다.
  - 검색 정밀도를 위해 문서를 "의미 단위"로 쪼개 각각 임베딩한다.
아래 chunk_text()는 그 개념을 직접 구현한 것으로,
  - chunk_size(1200자), overlap(200자) 은 설계 10절 값이며 config에서 온다.
  - overlap = 인접 청크 경계에서 문맥이 잘리는 걸 막는 "겹침" 구간.
"""

from app.core.config import get_settings


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    # LangChain TextSplitter.split_text() 에 대응. stride = size - overlap 만큼
    # 창을 이동시키며 자른다(고정 크기 슬라이딩 윈도우 방식).
    settings = get_settings()
    size = chunk_size if chunk_size is not None else settings.rag_chunk_size_chars
    step_overlap = overlap if overlap is not None else settings.rag_chunk_overlap_chars

    if size <= 0:
        raise ValueError("chunk_size must be positive.")
    if step_overlap < 0 or step_overlap >= size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    stripped = text.strip()
    if not stripped:
        return []

    stride = size - step_overlap
    chunks: list[str] = []
    start = 0
    text_len = len(stripped)
    while start < text_len:
        end = min(start + size, text_len)
        chunks.append(stripped[start:end])
        if end == text_len:
            break
        start += stride

    return chunks
