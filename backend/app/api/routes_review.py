from fastapi import APIRouter, Response

from app.models.object import ReviewObjectRequest
from app.models.recommendation import RecommendationResult
from app.services.recommendation_orchestrator import load_default_orchestrator


router = APIRouter(prefix="/api/v1", tags=["review"])
_latest_review_result: RecommendationResult | None = None


@router.post("/review-object", response_model=RecommendationResult)
def review_object(request: ReviewObjectRequest) -> RecommendationResult:
    global _latest_review_result
    orchestrator = load_default_orchestrator()
    result = orchestrator.review_object(request)
    _latest_review_result = result
    return result


@router.get("/latest-review", response_model=RecommendationResult | None)
def latest_review(response: Response) -> RecommendationResult | None:
    response.headers["Cache-Control"] = "no-store"
    return _latest_review_result
