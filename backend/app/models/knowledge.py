from datetime import datetime

from app.models.common import APIModel


class KnowledgeDocumentResponse(APIModel):
    id: int
    project_id: int
    source_name: str
    document_type: str
    document_date: str
    approval_status: str
    trade: str
    location: str
    uploaded_at: datetime
    chunk_count: int


class KnowledgeSearchRequest(APIModel):
    query: str
    trade_hint: str | None = None
    location_hint: str | None = None
    document_type_filter: str | None = None
    approval_status_filter: str | None = None


class KnowledgeChunkResult(APIModel):
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


class KnowledgeSearchResponse(APIModel):
    results: list[KnowledgeChunkResult]
    has_evidence: bool
