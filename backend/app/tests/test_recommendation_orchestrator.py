import json
from pathlib import Path

from app.models.object import DesignObjectInput, ProjectContext, ReviewObjectRequest
from app.models.recommendation import RecommendationResult
from app.core.config import Settings
from app.services.llm_client import LLMClientError
from app.services.local_retriever import load_default_retriever
from app.services.recommendation_orchestrator import (
    RecommendationOrchestrator,
    load_default_orchestrator,
    load_default_retriever_for_settings,
)
from app.services.rule_engine import load_default_rule_engine


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_sample_request() -> ReviewObjectRequest:
    sample_path = PROJECT_ROOT / "backend" / "data" / "sample_review_object_request.json"
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    return ReviewObjectRequest.model_validate(payload)


def test_orchestrator_returns_review_required_with_adopted_sources() -> None:
    result = load_default_orchestrator().review_object(load_sample_request())

    assert result.object_id == "W-012"
    assert result.status == "review_required"
    assert result.required_action == "designer_review"
    assert "material_missing" in result.detected_issues
    assert "thickness_review_required" in result.detected_issues
    assert result.sources
    assert result.sources[0].document_id == "SPEC-INT-024"


def test_orchestrator_marks_no_evidence_when_threshold_fails() -> None:
    request = ReviewObjectRequest(
        project=ProjectContext(project_id="PRJ-TEST"),
        object=DesignObjectInput(
            object_id="X-998",
            object_type=None,
            space_type="garden",
            material="soil",
        ),
    )

    result = load_default_orchestrator().review_object(request)

    assert result.status == "review_required"
    assert result.required_action == "need_more_input"
    assert result.sources == []
    assert result.confidence < 0.5
    assert any("No relevant document" in item for item in result.disclaimers)


class SofteningLLMClient:
    def generate_recommendation(self, request, rule_results, sources, fallback):
        return RecommendationResult(
            recommendation_id="WRONG",
            object_id="WRONG",
            status="ok",
            severity="low",
            summary="LLM summary can be used, but protected fields are constrained.",
            detected_issues=[],
            material_candidates=[],
            thickness_guidance={},
            performance_notes=[],
            required_action="none",
            confidence=0.99,
            sources=[],
            disclaimers=[],
        )


class FailingLLMClient:
    def generate_recommendation(self, request, rule_results, sources, fallback):
        raise LLMClientError("provider unavailable")


def test_orchestrator_does_not_allow_llm_to_soften_rule_results() -> None:
    orchestrator = RecommendationOrchestrator(
        rule_engine=load_default_rule_engine(),
        retriever=load_default_retriever(),
        llm_client=SofteningLLMClient(),
    )

    result = orchestrator.review_object(load_sample_request())

    assert result.object_id == "W-012"
    assert result.status == "review_required"
    assert result.severity == "medium"
    assert result.required_action == "designer_review"
    assert "material_missing" in result.detected_issues
    assert result.sources


def test_orchestrator_returns_fallback_when_llm_fails() -> None:
    orchestrator = RecommendationOrchestrator(
        rule_engine=load_default_rule_engine(),
        retriever=load_default_retriever(),
        llm_client=FailingLLMClient(),
    )

    result = orchestrator.review_object(load_sample_request())

    assert result.status == "review_required"
    assert any("fallback result returned" in item for item in result.disclaimers)


def test_retriever_provider_setting_rejects_unknown_provider() -> None:
    settings = Settings(DATABASE_URL="", RAG_RETRIEVER_PROVIDER="unknown")

    try:
        load_default_retriever_for_settings(settings)
    except ValueError as exc:
        assert "Unsupported RAG retriever provider" in str(exc)
    else:
        raise AssertionError("Expected unsupported retriever provider to fail.")
