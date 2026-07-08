import json
from pathlib import Path

from app.models.object import DesignObjectInput
from app.services.rule_engine import load_default_rule_engine


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample_objects"


def load_sample(name: str) -> DesignObjectInput:
    payload = json.loads((SAMPLE_DIR / name).read_text(encoding="utf-8"))
    return DesignObjectInput.model_validate(payload)


def issue_codes_for(name: str) -> set[str]:
    engine = load_default_rule_engine()
    return {result.issue_code for result in engine.evaluate(load_sample(name))}


def test_sample_object_count_is_ten() -> None:
    assert len(list(SAMPLE_DIR.glob("*.json"))) == 10


def test_w012_detects_material_and_thickness_review() -> None:
    issue_codes = issue_codes_for("wall_meeting_room_missing_material.json")

    assert "material_missing" in issue_codes
    assert "thickness_review_required" in issue_codes


def test_unknown_object_requests_more_input() -> None:
    issue_codes = issue_codes_for("object_unknown_context.json")

    assert "object_type_missing" in issue_codes
    assert "space_type_missing" in issue_codes
    assert "material_missing" not in issue_codes


def test_structural_slab_requires_expert_review() -> None:
    engine = load_default_rule_engine()
    results = engine.evaluate(load_sample("slab_load_bearing.json"))

    assert any(result.issue_code == "expert_review_required" for result in results)
    assert any(result.requires_expert_review for result in results)


def test_valid_floor_has_no_rule_issues() -> None:
    assert issue_codes_for("floor_office_valid.json") == set()
