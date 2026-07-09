import io

ACTIVITIES_CSV = (
    "activity_id,name,original_duration,remaining_duration,is_milestone,is_completed\n"
    "A100,Foundation,10,10,false,false\n"
    "A200,Structure,20,20,false,false\n"
    "A300,Handover,0,0,true,false\n"
)

RELATIONSHIPS_CSV = (
    "predecessor_id,successor_id,type,lag\n"
    "A100,A200,FS,0\n"
    "A200,A300,FS,2\n"
)


def _create_project(client):
    response = client.post("/api/v1/projects", json={"name": "Tower A", "description": "demo"})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_list_projects(client) -> None:
    project_id = _create_project(client)

    response = client.get("/api/v1/projects")

    assert response.status_code == 200
    projects = response.json()
    assert any(project["id"] == project_id for project in projects)


def test_import_snapshot_and_health(client) -> None:
    project_id = _create_project(client)

    response = client.post(
        f"/api/v1/projects/{project_id}/snapshots/import",
        files={
            "activities_csv": ("activities.csv", io.BytesIO(ACTIVITIES_CSV.encode()), "text/csv"),
            "relationships_csv": (
                "relationships.csv",
                io.BytesIO(RELATIONSHIPS_CSV.encode()),
                "text/csv",
            ),
        },
        data={"label": "baseline v1"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["activity_count"] == 3
    assert body["relationship_count"] == 2
    assert body["is_dag"] is True
    assert body["warnings"] == []

    snapshot_id = body["snapshot_id"]
    health_response = client.get(f"/api/v1/snapshots/{snapshot_id}/health")

    assert health_response.status_code == 200
    health = health_response.json()
    assert health["activity_count"] == 3
    assert health["relationship_count"] == 2
    assert health["is_dag"] is True
    assert health["cycle_activity_ids"] == []


def test_import_snapshot_rejects_unknown_project(client) -> None:
    response = client.post(
        "/api/v1/projects/999/snapshots/import",
        files={
            "activities_csv": ("activities.csv", io.BytesIO(ACTIVITIES_CSV.encode()), "text/csv"),
            "relationships_csv": (
                "relationships.csv",
                io.BytesIO(RELATIONSHIPS_CSV.encode()),
                "text/csv",
            ),
        },
        data={"label": "baseline v1"},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "project_not_found"


def test_import_snapshot_reports_cycle_as_warning(client) -> None:
    project_id = _create_project(client)
    cyclic_relationships = (
        "predecessor_id,successor_id,type,lag\n"
        "A100,A200,FS,0\n"
        "A200,A300,FS,0\n"
        "A300,A100,FS,0\n"
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/snapshots/import",
        files={
            "activities_csv": ("activities.csv", io.BytesIO(ACTIVITIES_CSV.encode()), "text/csv"),
            "relationships_csv": (
                "relationships.csv",
                io.BytesIO(cyclic_relationships.encode()),
                "text/csv",
            ),
        },
        data={"label": "cyclic"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["is_dag"] is False
    assert len(body["warnings"]) == 1


def test_get_health_for_missing_snapshot_returns_404(client) -> None:
    response = client.get("/api/v1/snapshots/999/health")

    assert response.status_code == 404
