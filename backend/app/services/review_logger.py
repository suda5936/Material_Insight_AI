from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.schema import ReviewActionRecord
from app.models.review_action import ReviewActionRequest, ReviewActionResponse


def save_review_action(
    db: Session,
    request: ReviewActionRequest,
) -> ReviewActionResponse:
    record = ReviewActionRecord(
        review_action_id=f"ACT-{uuid4().hex[:12].upper()}",
        recommendation_id=request.recommendation_id,
        object_id=request.object_id,
        user_id=request.user_id,
        action=request.action,
        edited_values=request.edited_values,
        reason=request.reason,
        payload={
            "sources": [source.model_dump(mode="json") for source in request.sources],
        },
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ReviewActionResponse(
        review_action_id=record.review_action_id,
        status="saved",
    )
