from fastapi.testclient import TestClient

from app.main import app


def test_rhino_object_sync_stores_and_returns_objects_by_project() -> None:
    client = TestClient(app)
    payload = {
        "project": {
            "project_id": "PRJ-RHINO-001",
            "project_type": "interior",
        },
        "objects": [
            {
                "object_id": "RHINO-WALL-001",
                "rhino_id": "6f4f8628-c221-4bde-ae6f-bbb69f13f5c7",
                "name": "Imported wall",
                "layer": "Layer_2-NewInteriorWall",
                "object_kind": "Brep",
                "material": "gypsum_board",
                "object_type": "interior_wall",
                "space_type": "meeting_room",
                "thickness_mm": 75,
                "review_status": "pending",
                "is_visible": True,
                "is_locked": False,
                "bbox": {
                    "min": [0, 0, 0],
                    "max": [3000, 120, 2700],
                },
                "user_attributes": {
                    "acoustic_required": True,
                },
            }
        ],
    }

    sync_response = client.post("/api/v1/rhino/objects", json=payload)
    list_response = client.get(
        "/api/v1/rhino/objects",
        params={"project_id": "PRJ-RHINO-001"},
    )

    assert sync_response.status_code == 200
    assert sync_response.json() == {
        "project_id": "PRJ-RHINO-001",
        "object_count": 1,
    }
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["project_id"] == "PRJ-RHINO-001"
    assert body["objects"][0]["object_id"] == "RHINO-WALL-001"
    assert body["objects"][0]["object_type"] == "interior_wall"
    assert body["objects"][0]["user_attributes"]["acoustic_required"] is True


def test_unknown_project_returns_empty_rhino_object_list() -> None:
    response = TestClient(app).get(
        "/api/v1/rhino/objects",
        params={"project_id": "PRJ-NO-OBJECTS"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "project_id": "PRJ-NO-OBJECTS",
        "objects": [],
    }


def test_rhino_selection_state_is_stored_by_project() -> None:
    client = TestClient(app)

    first = client.post(
        "/api/v1/rhino/selection",
        json={"project_id": "PRJ-SELECT-A", "object_id": "OBJ-A"},
    )
    second = client.post(
        "/api/v1/rhino/selection",
        json={"project_id": "PRJ-SELECT-B", "object_id": "OBJ-B"},
    )
    first_lookup = client.get(
        "/api/v1/rhino/selection",
        params={"project_id": "PRJ-SELECT-A"},
    )
    second_lookup = client.get(
        "/api/v1/rhino/selection",
        params={"project_id": "PRJ-SELECT-B"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first_lookup.json() == {
        "project_id": "PRJ-SELECT-A",
        "object_id": "OBJ-A",
    }
    assert second_lookup.json() == {
        "project_id": "PRJ-SELECT-B",
        "object_id": "OBJ-B",
    }


def test_rhino_selection_is_cleared_when_resynced_objects_do_not_include_it() -> None:
    client = TestClient(app)
    project_id = "PRJ-STALE-SELECTION"

    client.post(
        "/api/v1/rhino/objects",
        json={
            "project": {"project_id": project_id},
            "objects": [{"object_id": "OBJ-OLD"}],
        },
    )
    client.post(
        "/api/v1/rhino/selection",
        json={"project_id": project_id, "object_id": "OBJ-OLD"},
    )
    client.post(
        "/api/v1/rhino/objects",
        json={
            "project": {"project_id": project_id},
            "objects": [{"object_id": "OBJ-NEW"}],
        },
    )

    response = client.get(
        "/api/v1/rhino/selection",
        params={"project_id": project_id},
    )

    assert response.status_code == 200
    assert response.json() == {
        "project_id": project_id,
        "object_id": None,
    }
