import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.models.recommendation import RecommendationResult
from app.services.llm_client import LLMClientError, build_llm_client
from app.services.recommendation_orchestrator import load_default_orchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_sample_request():
    from app.models.object import ReviewObjectRequest

    sample_path = PROJECT_ROOT / "backend" / "data" / "sample_review_object_request.json"
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    return ReviewObjectRequest.model_validate(payload)


def test_build_llm_client_rejects_unknown_provider() -> None:
    settings = Settings(DATABASE_URL="", LLM_PROVIDER="unknown")

    with pytest.raises(LLMClientError):
        build_llm_client(settings)


def test_default_mock_llm_preserves_phase4_fallback() -> None:
    result = load_default_orchestrator().review_object(load_sample_request())

    assert result.status == "review_required"
    assert "material_missing" in result.detected_issues
    assert result.sources


def test_recommendation_result_schema_accepts_llm_shape() -> None:
    result = RecommendationResult(
        recommendation_id="REC-TEST",
        object_id="W-012",
        status="review_required",
        severity="medium",
        summary="Rule issues were detected and source documents were adopted.",
        detected_issues=["material_missing"],
        material_candidates=["gypsum board assembly"],
        thickness_guidance={"current_mm": 75},
        performance_notes=["Review acoustic performance."],
        required_action="designer_review",
        confidence=0.7,
        sources=[],
        disclaimers=[],
    )

    assert result.recommendation_id == "REC-TEST"
