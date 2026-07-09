import io
from datetime import datetime, timezone


def _create_project(client):
    response = client.post("/api/v1/projects", json={"name": "Tower A"})
    assert response.status_code == 201
    return response.json()["id"]


def _upload_document(client, project_id, text, **overrides):
    today = datetime.now(timezone.utc).date().isoformat()
    data = {
        "document_type": overrides.get("document_type", "meeting_minutes"),
        "document_date": overrides.get("document_date", today),
        "approval_status": overrides.get("approval_status", "approved"),
        "trade": overrides.get("trade", "curtain wall"),
        "location": overrides.get("location", "A-12F"),
    }
    if "source_name" in overrides:
        data["source_name"] = overrides["source_name"]

    return client.post(
        f"/api/v1/projects/{project_id}/knowledge/documents",
        files={"file": ("notice.md", io.BytesIO(text.encode()), "text/markdown")},
        data=data,
    )


def test_upload_and_list_knowledge_document(client) -> None:
    project_id = _create_project(client)

    response = _upload_document(
        client, project_id, "Curtain wall material delivery delayed at building A twelfth floor site."
    )

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == project_id
    assert body["chunk_count"] == 1

    list_response = client.get(f"/api/v1/projects/{project_id}/knowledge/documents")
    assert list_response.status_code == 200
    documents = list_response.json()
    assert len(documents) == 1
    assert documents[0]["id"] == body["id"]


def test_upload_rejects_unsupported_extension(client) -> None:
    project_id = _create_project(client)
    today = datetime.now(timezone.utc).date().isoformat()

    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge/documents",
        files={"file": ("notice.pdf", io.BytesIO(b"content"), "application/pdf")},
        data={
            "document_type": "meeting_minutes",
            "document_date": today,
            "approval_status": "approved",
            "trade": "curtain wall",
            "location": "A-12F",
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "invalid_knowledge_document"


def test_upload_rejects_invalid_date_format(client) -> None:
    project_id = _create_project(client)

    response = _upload_document(client, project_id, "Some content", document_date="07/09/2026")

    assert response.status_code == 422


def test_upload_rejects_unknown_project(client) -> None:
    today = datetime.now(timezone.utc).date().isoformat()

    response = client.post(
        "/api/v1/projects/999/knowledge/documents",
        files={"file": ("notice.md", io.BytesIO(b"content"), "text/markdown")},
        data={
            "document_type": "meeting_minutes",
            "document_date": today,
            "approval_status": "approved",
            "trade": "curtain wall",
            "location": "A-12F",
        },
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "project_not_found"


def test_search_returns_evidence_for_relevant_query(client) -> None:
    project_id = _create_project(client)
    _upload_document(
        client, project_id, "Curtain wall material delivery delayed at building A twelfth floor site."
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge/search",
        json={"query": "curtain wall material delivery delayed twelfth floor"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["has_evidence"] is True
    assert len(body["results"]) == 1


def test_search_returns_no_evidence_when_no_documents(client) -> None:
    project_id = _create_project(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/knowledge/search",
        json={"query": "curtain wall material delivery delayed twelfth floor"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["has_evidence"] is False
    assert body["results"] == []


def test_delete_knowledge_document(client) -> None:
    project_id = _create_project(client)
    upload_response = _upload_document(client, project_id, "Some field document content here.")
    document_id = upload_response.json()["id"]

    delete_response = client.delete(f"/api/v1/knowledge/documents/{document_id}")
    assert delete_response.status_code == 204

    list_response = client.get(f"/api/v1/projects/{project_id}/knowledge/documents")
    assert list_response.json() == []


def test_delete_unknown_document_returns_404(client) -> None:
    response = client.delete("/api/v1/knowledge/documents/999")

    assert response.status_code == 404
    assert response.json()["error_code"] == "knowledge_document_not_found"
