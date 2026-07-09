from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError
from app.db.models import KnowledgeChunk, KnowledgeDocument, Project
from app.db.session import get_db
from app.models.knowledge import (
    KnowledgeChunkResult,
    KnowledgeDocumentResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services.embeddings import EmbeddingProvider, provide_embedding_provider
from app.services.knowledge_upload import ingest_document, validate_filename
from app.services.retrieval import search_knowledge_chunks

router = APIRouter(tags=["knowledge"])


def _to_response(document: KnowledgeDocument, chunk_count: int) -> KnowledgeDocumentResponse:
    return KnowledgeDocumentResponse(
        id=document.id,
        project_id=document.project_id,
        source_name=document.source_name,
        document_type=document.document_type,
        document_date=document.document_date,
        approval_status=document.approval_status,
        trade=document.trade,
        location=document.location,
        uploaded_at=document.uploaded_at,
        chunk_count=chunk_count,
    )


@router.post(
    "/api/v1/projects/{project_id}/knowledge/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=201,
)
async def upload_knowledge_document(
    project_id: int,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_date: str = Form(...),
    approval_status: str = Form(...),
    trade: str = Form(...),
    location: str = Form(...),
    source_name: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    embedding_provider: EmbeddingProvider = Depends(provide_embedding_provider),
) -> KnowledgeDocumentResponse:
    project = await db.get(Project, project_id)
    if project is None:
        raise APIError(
            status_code=404,
            error_code="project_not_found",
            message=f"Project {project_id} was not found.",
        )

    filename = file.filename or "document.txt"
    validate_filename(filename)
    raw_text = (await file.read()).decode("utf-8-sig")

    document = await ingest_document(
        db=db,
        embedding_provider=embedding_provider,
        project_id=project_id,
        source_name=source_name or filename,
        document_type=document_type,
        document_date=document_date,
        approval_status=approval_status,
        trade=trade,
        location=location,
        raw_text=raw_text,
    )

    chunk_count_result = await db.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id)
    )
    chunk_count = len(chunk_count_result.scalars().all())

    return _to_response(document, chunk_count)


@router.get(
    "/api/v1/projects/{project_id}/knowledge/documents",
    response_model=list[KnowledgeDocumentResponse],
)
async def list_knowledge_documents(
    project_id: int, db: AsyncSession = Depends(get_db)
) -> list[KnowledgeDocumentResponse]:
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.project_id == project_id)
        .order_by(KnowledgeDocument.uploaded_at.desc())
    )
    documents = list(result.scalars().all())

    responses: list[KnowledgeDocumentResponse] = []
    for document in documents:
        chunk_count_result = await db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id)
        )
        chunk_count = len(chunk_count_result.scalars().all())
        responses.append(_to_response(document, chunk_count))
    return responses


@router.post(
    "/api/v1/projects/{project_id}/knowledge/search",
    response_model=KnowledgeSearchResponse,
)
async def search_knowledge(
    project_id: int,
    payload: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
    embedding_provider: EmbeddingProvider = Depends(provide_embedding_provider),
) -> KnowledgeSearchResponse:
    results = await search_knowledge_chunks(
        db=db,
        embedding_provider=embedding_provider,
        project_id=project_id,
        query_text=payload.query,
        trade_hint=payload.trade_hint,
        location_hint=payload.location_hint,
        document_type_filter=payload.document_type_filter,
        approval_status_filter=payload.approval_status_filter,
    )

    return KnowledgeSearchResponse(
        results=[
            KnowledgeChunkResult(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                content=item.content,
                source_name=item.source_name,
                document_type=item.document_type,
                document_date=item.document_date,
                approval_status=item.approval_status,
                trade=item.trade,
                location=item.location,
                vector_similarity=item.vector_similarity,
                score=item.score,
            )
            for item in results
        ],
        has_evidence=len(results) > 0,
    )


@router.delete("/api/v1/knowledge/documents/{document_id}", status_code=204)
async def delete_knowledge_document(document_id: int, db: AsyncSession = Depends(get_db)) -> None:
    document = await db.get(KnowledgeDocument, document_id)
    if document is None:
        raise APIError(
            status_code=404,
            error_code="knowledge_document_not_found",
            message=f"Knowledge document {document_id} was not found.",
        )

    await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))
    await db.execute(delete(KnowledgeDocument).where(KnowledgeDocument.id == document_id))
    await db.commit()
