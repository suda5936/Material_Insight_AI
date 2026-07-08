import json
from pathlib import Path

from app.models.object import ReviewObjectRequest


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
