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


def test_review_object_api_accepts_rhino_plugin_payload_sample() -> None:
    sample_path = (
        Path(__file__).resolve().parents[3]
        / "plugin"
        / "RhinoMaterialInsight"
        / "Samples"
        / "review_object_payload.json"
    )
    payload = json.loads(sample_path.read_text(encoding="utf-8"))

    response = TestClient(app).post("/api/v1/review-object", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["object_id"] == "W-012"
    assert "material_missing" in body["detected_issues"]


def test_latest_review_returns_most_recent_review_result() -> None:
    sample_path = (
        Path(__file__).resolve().parents[3]
        / "plugin"
        / "RhinoMaterialInsight"
        / "Samples"
        / "review_object_payload.json"
    )
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    client = TestClient(app)

    review_response = client.post("/api/v1/review-object", json=payload)
    latest_response = client.get("/api/v1/latest-review")

    assert review_response.status_code == 200
    assert latest_response.status_code == 200
    assert latest_response.json()["recommendation_id"] == review_response.json()["recommendation_id"]
    assert latest_response.json()["object_id"] == "W-012"
