from typing import Dict, List, Literal

from pydantic import Field

from app.models.common import APIModel
from app.models.document import RetrievedDocument


class RecommendationResult(APIModel):
    recommendation_id: str
    object_id: str
    status: Literal["ok", "review_required", "blocked", "error"]
    severity: Literal["low", "medium", "high", "critical"]
    summary: str
    detected_issues: List[str] = Field(default_factory=list)
    material_candidates: List[str] = Field(default_factory=list)
    thickness_guidance: Dict[str, object] = Field(default_factory=dict)
    performance_notes: List[str] = Field(default_factory=list)
    required_action: Literal[
        "none",
        "designer_review",
        "senior_review",
        "expert_review",
        "need_more_input",
    ]
    confidence: float
    sources: List[RetrievedDocument] = Field(default_factory=list)
    disclaimers: List[str] = Field(default_factory=list)
