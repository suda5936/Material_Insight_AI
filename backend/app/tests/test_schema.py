import json
from pathlib import Path

from app.models.document import RetrievedDocument
from app.models.object import ReviewObjectRequest
from app.models.review_action import ReviewActionRequest


def test_sample_review_object_request_is_valid() -> None:
    sample_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "sample_review_object_request.json"
    )
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    request = ReviewObjectRequest.model_validate(payload)

    assert request.project.project_id == "PRJ-001"
    assert request.object.object_id == "W-012"
    assert request.object.object_type == "interior_wall"
    assert request.object.space_type == "meeting_room"
    assert request.object.thickness_mm == 75


def test_review_action_request_accepts_object_id_and_sources() -> None:
    request = ReviewActionRequest(
        recommendation_id="REC-0001",
        object_id="W-012",
        user_id="designer-01",
        action="edit",
        edited_values={"material": "gypsum board assembly"},
        sources=[
            RetrievedDocument(
                document_id="SPEC-INT-024",
                title="Meeting room wall specification",
                chunk_text="Adopted source chunk",
                document_type="project_specification",
                score=12.0,
                section="4.2",
                version="2.1",
                source="internal_project_spec",
            )
        ],
        reason="Designer adjusted material after review.",
    )

    assert request.object_id == "W-012"
    assert request.sources[0].document_id == "SPEC-INT-024"
