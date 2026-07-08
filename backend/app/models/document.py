from typing import Literal, Optional

from app.models.common import APIModel


class RetrievedDocument(APIModel):
    document_id: str
    title: str
    chunk_text: str
    document_type: str
    score: float
    section: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[str] = None
    status: Literal["active", "inactive", "deprecated"] = "active"
    source: Optional[str] = None
