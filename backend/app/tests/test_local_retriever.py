import json
from pathlib import Path

from app.models.object import DesignObjectInput
from app.services.local_retriever import load_default_retriever
from app.services.rule_engine import load_default_rule_engine


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample_objects"


def load_sample(name: str) -> DesignObjectInput:
    payload = json.loads((SAMPLE_DIR / name).read_text(encoding="utf-8"))
    return DesignObjectInput.model_validate(payload)


def search_for_sample(name: str):
    design_object = load_sample(name)
    rule_results = load_default_rule_engine().evaluate(design_object)
    return load_default_retriever().search_relevant(design_object, rule_results, limit=5)


def test_w012_retrieves_meeting_room_wall_spec_first() -> None:
    results = search_for_sample("wall_meeting_room_missing_material.json")

    assert results
    assert results[0].document_id == "SPEC-INT-024"
    assert results[0].section == "4.2 회의실 구획벽"
    assert results[0].version == "2.1"
    assert results[0].source == "internal_project_spec"


def test_floor_restroom_retrieves_floor_catalog() -> None:
    results = search_for_sample("floor_restroom_carpet.json")

    assert results
    assert results[0].document_id == "CAT-FLOOR-010"


def test_unrelated_object_can_return_no_documents() -> None:
    design_object = DesignObjectInput(
        object_id="X-999",
        object_type="landscape_tree",
        space_type="garden",
        material="soil",
    )
    results = load_default_retriever().search_relevant(design_object, [], limit=5)

    assert results == []


def test_low_score_candidates_are_not_adopted_as_sources() -> None:
    design_object = DesignObjectInput(
        object_id="X-998",
        object_type="interior_wall",
        space_type="garden",
        material="soil",
    )
    retriever = load_default_retriever()

    candidates = retriever.search(design_object, [], limit=5)
    relevant = retriever.search_relevant(design_object, [], limit=5, min_score=8.0)

    assert candidates
    assert relevant == []
