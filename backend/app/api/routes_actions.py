from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.schema import Base
from app.db.session import engine, get_db
from app.models.review_action import ReviewActionRequest, ReviewActionResponse
from app.services.review_logger import save_review_action


router = APIRouter(prefix="/api/v1", tags=["review-actions"])


@router.post("/review-actions", response_model=ReviewActionResponse)
def create_review_action(
    request: ReviewActionRequest,
    db: Session = Depends(get_db),
) -> ReviewActionResponse:
    Base.metadata.create_all(bind=engine)
    return save_review_action(db, request)
