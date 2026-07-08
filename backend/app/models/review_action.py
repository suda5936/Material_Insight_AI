from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from app.models.common import APIModel
from app.models.document import RetrievedDocument


class ReviewActionRequest(APIModel):
    recommendation_id: str
    object_id: Optional[str] = None
    user_id: str
    action: Literal["accept", "edit", "hold", "ignore", "request_expert_review"]
    edited_values: Dict[str, Any] = Field(default_factory=dict)
    sources: List[RetrievedDocument] = Field(default_factory=list)
    reason: Optional[str] = None


class ReviewActionResponse(APIModel):
    review_action_id: str
    status: Literal["saved"]
