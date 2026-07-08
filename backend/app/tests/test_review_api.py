import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_review_object_api_returns_recommendation() -> None:
    sample_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "sample_review_object_request.json"
    )
    payload = json.loads(sample_path.read_text(encoding="utf-8"))

    response = TestClient(app).post("/api/v1/review-object", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["object_id"] == "W-012"
    assert body["status"] == "review_required"
    assert "material_missing" in body["detected_issues"]
    assert body["sources"]
    assert body["sources"][0]["document_id"] == "SPEC-INT-024"
