from typing import Any, Dict, Literal, Optional

from pydantic import Field

from app.models.common import APIModel


class ReviewActionRequest(APIModel):
    recommendation_id: str
    user_id: str
    action: Literal["accept", "edit", "hold", "ignore", "request_expert_review"]
    edited_values: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None
