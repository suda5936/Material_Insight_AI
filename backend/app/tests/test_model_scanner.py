import json
from pathlib import Path

from app.models.object import DesignObjectInput, ProjectContext
from app.models.scan import ScanModelRequest
from app.services.model_scanner import load_default_model_scanner


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample_objects"


def load_sample(name: str) -> DesignObjectInput:
    payload = json.loads((SAMPLE_DIR / name).read_text(encoding="utf-8"))
    return DesignObjectInput.model_validate(payload)


def test_scan_model_summarizes_issue_counts_and_prioritizes_results() -> None:
    request = ScanModelRequest(
        project=ProjectContext(project_id="PRJ-SCAN"),
        objects=[
            load_sample("wall_meeting_room_missing_material.json"),
            load_sample("floor_office_valid.json"),
            load_sample("slab_load_bearing.json"),
            load_sample("object_unknown_context.json"),
        ],
    )

    response = load_default_model_scanner().scan(request)

    assert response.project_id == "PRJ-SCAN"
    assert response.summary.total_objects == 4
    assert response.summary.objects_with_issues == 3
    assert response.summary.issue_counts["material_missing"] == 1
    assert response.summary.issue_counts["expert_review_required"] == 1
    assert response.results[0].required_action == "expert_review"
    assert response.results[0].severity == "high"
