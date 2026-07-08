from fastapi import APIRouter

from app.models.object import ReviewObjectRequest
from app.models.recommendation import RecommendationResult
from app.services.recommendation_orchestrator import load_default_orchestrator


router = APIRouter(prefix="/api/v1", tags=["review"])


@router.post("/review-object", response_model=RecommendationResult)
def review_object(request: ReviewObjectRequest) -> RecommendationResult:
    orchestrator = load_default_orchestrator()
    return orchestrator.review_object(request)
