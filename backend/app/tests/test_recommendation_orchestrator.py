import json
from pathlib import Path

from app.models.object import DesignObjectInput, ProjectContext, ReviewObjectRequest
from app.services.recommendation_orchestrator import load_default_orchestrator


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
