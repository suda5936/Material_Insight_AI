import json
from pathlib import Path

from app.models.object import ReviewObjectRequest


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_rhino_plugin_review_object_payload_contract() -> None:
    payload_path = BACKEND_ROOT / "data" / "rhino_plugin_review_object_payload.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    request = ReviewObjectRequest.model_validate(payload)

    assert request.project.project_id == "PRJ-001"
    assert request.object.object_id == "W-012"
    assert request.object.object_type == "interior_wall"
    assert request.object.space_type == "meeting_room"
    assert request.object.thickness_mm == 75
    assert request.object.geometry.object_kind == "Brep"
    assert request.object.user_attributes["acoustic_required"] is True


def test_rhino_plugin_can_send_thickness_as_string() -> None:
    payload_path = BACKEND_ROOT / "data" / "rhino_plugin_review_object_payload.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    payload["object"]["thickness_mm"] = "75"

    request = ReviewObjectRequest.model_validate(payload)

    assert request.object.thickness_mm == 75
