"""문서 인제스천(Ingestion / Indexing) 파이프라인.

[수업 정리] RAG의 "인덱싱" 단계 = 문서를 검색 가능한 형태로 적재하는 오프라인 과정.
------------------------------------------------------------------
LangChain 표준 인덱싱 파이프라인:
    Document Loader → TextSplitter → Embeddings → VectorStore.add_documents()

이 파일의 ingest_document() 가 그 파이프라인을 그대로 구현한다:
    업로드 파일(txt/md)  →  chunk_text()      (TextSplitter)
                        →  embed_batch()      (Embeddings)
                        →  KnowledgeChunk 저장 (VectorStore.add_documents)
검색(retrieval.py)이 "질의 시점(online)"이라면, 여기는 "적재 시점(offline)"이다.
필수 metadata(document_type/date/approval/trade/location/source)는 나중에
retrieval 재랭킹과 보고서 citation에 쓰이므로 청크와 함께 저장한다.
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError
from app.db.models import KnowledgeChunk, KnowledgeDocument
from app.services.chunking import chunk_text
from app.services.embeddings import EmbeddingProvider

ALLOWED_EXTENSIONS = {".txt", ".md"}


def _invalid(message: str, details: dict[str, object] | None = None) -> APIError:
    return APIError(
        status_code=422, error_code="invalid_knowledge_document", message=message, details=details
    )


def validate_filename(filename: str) -> None:
    lowered = filename.lower()
    if not any(lowered.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise _invalid(
            "Only .txt and .md files are supported for knowledge documents.",
            details={"filename": filename},
        )


def validate_document_date(document_date: str) -> None:
    try:
        datetime.strptime(document_date, "%Y-%m-%d")
    except ValueError:
        raise _invalid(
            "document_date must be in YYYY-MM-DD format.",
            details={"document_date": document_date},
        ) from None


async def ingest_document(
    db: AsyncSession,
    embedding_provider: EmbeddingProvider,
    project_id: int,
    source_name: str,
    document_type: str,
    document_date: str,
    approval_status: str,
    trade: str,
    location: str,
    raw_text: str,
) -> KnowledgeDocument:
    validate_document_date(document_date)
    if not raw_text.strip():
        raise _invalid("Document content is empty.")

    document = KnowledgeDocument(
        project_id=project_id,
        source_name=source_name,
        document_type=document_type,
        document_date=document_date,
        approval_status=approval_status,
        trade=trade,
        location=location,
        raw_text=raw_text,
    )
    db.add(document)
    await db.flush()

    # 1) Split: 원문을 1200/200 청크로 분할 (TextSplitter)
    chunks = chunk_text(raw_text)
    if chunks:
        # 2) Embed: 청크들을 한 번에 벡터화 (Embeddings.embed_documents)
        embeddings = await embedding_provider.embed_batch(chunks)
        # 3) Store: 청크+벡터를 pgvector 컬럼에 적재 (VectorStore.add_documents)
        for index, (content, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(
                KnowledgeChunk(
                    document_id=document.id,
                    project_id=project_id,
                    chunk_index=index,
                    content=content,
                    embedding=embedding,
                )
            )

    await db.commit()
    await db.refresh(document)
    return document
