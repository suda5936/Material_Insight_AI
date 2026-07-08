import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample_objects"


def load_sample(name: str) -> dict:
    return json.loads((SAMPLE_DIR / name).read_text(encoding="utf-8"))


def test_scan_model_api_returns_summary() -> None:
    payload = {
        "project": {"project_id": "PRJ-SCAN"},
        "objects": [
            load_sample("wall_meeting_room_missing_material.json"),
            load_sample("floor_office_valid.json"),
            load_sample("wall_corridor_missing_thickness.json"),
        ],
    }

    response = TestClient(app).post("/api/v1/scan-model", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "PRJ-SCAN"
    assert body["summary"]["total_objects"] == 3
    assert body["summary"]["objects_with_issues"] == 2
    assert body["results"][0]["issue_count"] >= body["results"][-1]["issue_count"]
