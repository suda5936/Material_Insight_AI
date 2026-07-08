import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.object import ReviewObjectRequest


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
BACKEND_PAYLOAD_PATH = BACKEND_ROOT / "data" / "rhino_plugin_review_object_payload.json"
PLUGIN_PAYLOAD_PATH = (
    PROJECT_ROOT
    / "plugin"
    / "RhinoMaterialInsight"
    / "Samples"
    / "review_object_payload.json"
)
PLUGIN_MODEL_PATH = (
    PROJECT_ROOT
    / "plugin"
    / "RhinoMaterialInsight"
    / "Models"
    / "MaterialInsightModels.cs"
)


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("payload_path", [BACKEND_PAYLOAD_PATH, PLUGIN_PAYLOAD_PATH])
def test_rhino_plugin_review_object_payload_contract(payload_path: Path) -> None:
    payload = load_payload(payload_path)

    request = ReviewObjectRequest.model_validate(payload)

    assert request.project.project_id == "PRJ-001"
    assert request.object.object_id == "W-012"
    assert request.object.object_type == "interior_wall"
    assert request.object.space_type == "meeting_room"
    assert request.object.thickness_mm == 75
    assert request.object.geometry.object_kind == "Brep"
    assert request.object.geometry.bbox["min"] == [0.0, 0.0, 0.0]
    assert request.object.geometry.bbox["max"] == [4200.0, 100.0, 3000.0]
    assert request.object.user_attributes["acoustic_required"] is True


def test_rhino_plugin_can_send_thickness_as_string() -> None:
    payload = load_payload(BACKEND_PAYLOAD_PATH)
    payload["object"]["thickness_mm"] = "75"

    request = ReviewObjectRequest.model_validate(payload)

    assert request.object.thickness_mm == 75


def test_rhino_plugin_minimal_payload_keeps_optional_fields_optional() -> None:
    request = ReviewObjectRequest.model_validate(
        {
            "project": {"project_id": "PRJ-MIN"},
            "object": {"object_id": "RHINO-GUID-001"},
        }
    )

    assert request.project.project_id == "PRJ-MIN"
    assert request.object.object_id == "RHINO-GUID-001"
    assert request.object.object_type is None
    assert request.object.geometry.bbox == {}
    assert request.object.user_attributes == {}


def test_rhino_plugin_payload_rejects_unknown_contract_fields() -> None:
    payload = load_payload(BACKEND_PAYLOAD_PATH)
    payload["object"]["rhino_official_json"] = {"unexpected": True}

    with pytest.raises(ValidationError):
        ReviewObjectRequest.model_validate(payload)


def test_plugin_csharp_dto_emits_backend_snake_case_field_names() -> None:
    source = PLUGIN_MODEL_PATH.read_text(encoding="utf-8")
    expected_json_names = [
        "project_id",
        "project_type",
        "design_stage",
        "building_use",
        "object_id",
        "object_type",
        "thickness_mm",
        "space_type",
        "review_status",
        "object_kind",
        "area_m2",
        "volume_m3",
        "user_attributes",
        "recommendation_id",
        "detected_issues",
        "material_candidates",
        "required_action",
    ]

    for json_name in expected_json_names:
        assert f'JsonPropertyName("{json_name}")' in source
