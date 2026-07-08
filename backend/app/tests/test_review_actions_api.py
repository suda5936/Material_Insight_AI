from fastapi.testclient import TestClient

from app.main import app


def test_review_actions_api_saves_action() -> None:
    payload = {
        "recommendation_id": "REC-TEST-001",
        "object_id": "W-012",
        "user_id": "designer-01",
        "action": "edit",
        "edited_values": {
            "material": "gypsum board assembly",
            "thickness_mm": 125,
        },
        "sources": [
            {
                "document_id": "SPEC-INT-024",
                "title": "Meeting room wall specification",
                "chunk_text": "Adopted source chunk",
                "document_type": "project_specification",
                "score": 12.0,
                "section": "4.2",
                "version": "2.1",
                "source": "internal_project_spec",
            }
        ],
        "reason": "Designer accepted the recommendation after review.",
    }

    response = TestClient(app).post("/api/v1/review-actions", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["review_action_id"].startswith("ACT-")
    assert body["status"] == "saved"
