"""검색(Retrieval) — RAG의 R.

[수업 정리] RAG 파이프라인 4단계 = Retrieval (VectorStore + Retriever).
------------------------------------------------------------------
사용자 질의를 임베딩한 뒤, 벡터 스토어에서 코사인 유사도가 높은 청크를 꺼내온다.

LangChain 대응:
    # VectorStore: 우리는 PostgreSQL + pgvector 를 벡터 스토어로 사용
    from langchain_postgres import PGVector
    store = PGVector(embeddings=emb, collection_name=..., connection=...)
    # Retriever: 벡터 스토어를 "검색기"로 감싼 것
    retriever = store.as_retriever(search_kwargs={"k": 8})
    docs = retriever.invoke("커튼월 자재 지연")

아래 search_knowledge_chunks() 가 바로 retriever.invoke() 에 해당한다. 다만 우리는
LangChain 대신 설계 10절의 검색 로직을 직접 구현했다:
    1) project_id 로 스코프 제한 (metadata filter)      ← 멀티테넌시 격리
    2) 벡터 유사도 상위 K개(=20) 후보 추출               ← 기본 similarity search
    3) threshold 미만 컷                                  ← 근거 없음 판정
    4) metadata boost 재랭킹 (trade/location/승인/최신성) ← 커스텀 Retriever/rerank
    5) 최종 top 8 반환
이처럼 "벡터 유사도 + 메타데이터 가중치"로 다시 정렬하는 것은 LangChain의
ContextualCompressionRetriever / EnsembleRetriever 로 하는 재랭킹과 같은 목적이다.
"""

import math
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import get_settings
from app.db.models import KnowledgeChunk, KnowledgeDocument
from app.services.embeddings import EmbeddingProvider

APPROVAL_STATUS_WEIGHTS: dict[str, float] = {
    "approved": 1.0,
    "pending": 0.5,
    "draft": 0.25,
    "rejected": 0.0,
}


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: int
    document_id: int
    content: str
    source_name: str
    document_type: str
    document_date: str
    approval_status: str
    trade: str
    location: str
    vector_similarity: float
    score: float


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _recency_weight(document_date: str, today: date) -> float:
    try:
        parsed = datetime.strptime(document_date, "%Y-%m-%d").date()
    except ValueError:
        return 0.0
    age_days = (today - parsed).days
    if age_days < 0:
        return 1.0
    if age_days <= 30:
        return 1.0
    if age_days <= 180:
        return 0.5
    return 0.0


def _match_weight(hint: str | None, value: str) -> float:
    if not hint:
        return 0.0
    return 1.0 if hint.strip().lower() == value.strip().lower() else 0.0


async def search_knowledge_chunks(
    db: AsyncSession,
    embedding_provider: EmbeddingProvider,
    project_id: int,
    query_text: str,
    trade_hint: str | None = None,
    location_hint: str | None = None,
    document_type_filter: str | None = None,
    approval_status_filter: str | None = None,
) -> list[RetrievedChunk]:
    settings = get_settings()

    stmt = (
        select(KnowledgeChunk)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .options(joinedload(KnowledgeChunk.document))
        .where(KnowledgeChunk.project_id == project_id)
    )
    if document_type_filter:
        stmt = stmt.where(KnowledgeDocument.document_type == document_type_filter)
    if approval_status_filter:
        stmt = stmt.where(KnowledgeDocument.approval_status == approval_status_filter)

    result = await db.execute(stmt)
    candidates = list(result.scalars().unique().all())
    if not candidates:
        return []

    # 질의를 임베딩(embed_query) → 각 청크 벡터와 코사인 유사도 계산.
    # LangChain의 similarity_search 는 이 벡터 비교를 내부에서 수행한다.
    query_embedding = await embedding_provider.embed_one(query_text)

    scored: list[tuple[KnowledgeChunk, float]] = [
        (chunk, cosine_similarity(query_embedding, list(chunk.embedding))) for chunk in candidates
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    top_20 = scored[: settings.rag_vector_top_k]  # 1차 벡터 검색 상위 K

    # threshold 컷: 충분히 유사한 근거가 없으면 빈 결과 → 상위 계층에서 "관련 근거 없음" 처리.
    # (RAG에서 "모르면 모른다고 답하게" 하는 핵심 안전장치)
    above_threshold = [pair for pair in top_20 if pair[1] >= settings.rag_min_score]
    if not above_threshold:
        return []

    today = datetime.now(timezone.utc).date()
    boosted: list[RetrievedChunk] = []
    for chunk, similarity in above_threshold:
        document = chunk.document
        trade_match = _match_weight(trade_hint, document.trade)
        location_match = _match_weight(location_hint, document.location)
        approval_weight = APPROVAL_STATUS_WEIGHTS.get(document.approval_status.strip().lower(), 0.0)
        recency_weight = _recency_weight(document.document_date, today)

        # metadata boost 재랭킹(설계 10절 점수식). 순수 벡터 유사도만으로는
        # "같은 공종/위치/최신/승인" 문서를 우대할 수 없으므로 메타데이터 가중치를 더한다.
        # LangChain으로 치면 base retriever 위에 얹는 커스텀 rerank 단계.
        composite_score = (
            0.70 * similarity
            + 0.10 * trade_match
            + 0.10 * location_match
            + 0.05 * approval_weight
            + 0.05 * recency_weight
        )

        boosted.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=document.id,
                content=chunk.content,
                source_name=document.source_name,
                document_type=document.document_type,
                document_date=document.document_date,
                approval_status=document.approval_status,
                trade=document.trade,
                location=document.location,
                vector_similarity=similarity,
                score=composite_score,
            )
        )

    boosted.sort(key=lambda item: item.score, reverse=True)
    return boosted[: settings.rag_final_top_k]
