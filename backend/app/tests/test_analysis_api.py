import io
import json
from datetime import datetime, timezone

from app.services.llm.registry import provide_llm_registry
from app.tests.fakes import build_fake_registry

ACTIVITIES_CSV = (
    "activity_id,name,original_duration,remaining_duration,is_milestone,is_completed\n"
    "A100,Curtain wall install,10,10,false,false\n"
    "A200,Structure,20,20,false,false\n"
    "A300,Handover,0,0,true,false\n"
)
RELATIONSHIPS_CSV = (
    "predecessor_id,successor_id,type,lag\n"
    "A100,A200,FS,0\n"
    "A200,A300,FS,0\n"
)


def _setup_project_with_snapshot(client) -> int:
    project_id = client.post("/api/v1/projects", json={"name": "Tower A"}).json()["id"]
    client.post(
        f"/api/v1/projects/{project_id}/snapshots/import",
        files={
            "activities_csv": ("a.csv", io.BytesIO(ACTIVITIES_CSV.encode()), "text/csv"),
            "relationships_csv": ("r.csv", io.BytesIO(RELATIONSHIPS_CSV.encode()), "text/csv"),
        },
        data={"label": "baseline"},
    )
    return project_id


def _upload_doc(client, project_id) -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    client.post(
        f"/api/v1/projects/{project_id}/knowledge/documents",
        files={"file": ("notice.md", io.BytesIO("curtain wall material delivery delayed twelfth floor".encode()), "text/markdown")},
        data={
            "document_type": "field_notice",
            "document_date": today,
            "approval_status": "approved",
            "trade": "curtain wall",
            "location": "A-12F",
        },
    )


def _mapping_json(confidence: float) -> str:
    return json.dumps(
        {
            "issue_type": "material_delay",
            "location": "A-12F",
            "trade": "curtain wall",
            "delay_days": 10,
            "impact_mode": "START_BLOCK",
            "ranked_candidates": [
                {"activity_id": "A100", "confidence": confidence, "reason": "matches trade/location"},
                {"activity_id": "A200", "confidence": 0.2, "reason": "structure"},
            ],
            "evidence_chunk_ids": [],
            "missing_information": [],
            "overall_confidence": confidence,
        }
    )


PLAN_JSON = json.dumps(
    {
        "scenarios": [
            {"action": "REDUCE_START_BLOCK", "target_activity_id": "A100", "reduction_days": 4, "rationale": "expedite delivery", "evidence_chunk_ids": []},
            {"action": "REDUCE_ACTIVITY_DURATION", "target_activity_id": "A100", "reduction_days": 3, "rationale": "add crew", "evidence_chunk_ids": []},
            {"action": "REDUCE_START_BLOCK", "target_activity_id": "A100", "reduction_days": 10, "rationale": "full expedite", "evidence_chunk_ids": []},
        ]
    }
)
REVIEW_JSON = json.dumps(
    {"warnings": [{"category": "safety", "message": "confirm safety approval"}], "needs_human_review": True, "summary": "ok"}
)


def _override_registry(client, mapping_json: str) -> None:
    client.app.dependency_overrides[provide_llm_registry] = lambda: build_fake_registry(
        mapping=mapping_json, plan=PLAN_JSON, review=REVIEW_JSON
    )


def test_create_issue(client) -> None:
    project_id = _setup_project_with_snapshot(client)

    response = client.post("/api/v1/issues", json={"project_id": project_id, "raw_text": "커튼월 지연"})

    assert response.status_code == 201
    assert response.json()["project_id"] == project_id


def test_analyze_auto_selects_and_completes(client) -> None:
    project_id = _setup_project_with_snapshot(client)
    _upload_doc(client, project_id)
    _override_registry(client, _mapping_json(0.95))

    issue_id = client.post(
        "/api/v1/issues",
        json={"project_id": project_id, "raw_text": "A동 12층 커튼월 자재 10일 지연"},
    ).json()["id"]

    response = client.post(f"/api/v1/issues/{issue_id}/analyze")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["selected_activity_id"] == "A100"
    assert body["impact_json"]["project_delay_days"] == 10
    assert len(body["scenarios"]) == 3
    # REDUCE_START_BLOCK with reduction 10 fully recovers the 10-day block.
    full_recovery = [s for s in body["scenarios"] if s["reduction_days"] == 10][0]
    assert full_recovery["recovered_days"] == 10
    assert body["rule_validation_json"]["passed"] is True


def test_analyze_needs_selection_then_select_activity(client) -> None:
    project_id = _setup_project_with_snapshot(client)
    _upload_doc(client, project_id)
    _override_registry(client, _mapping_json(0.60))

    issue_id = client.post(
        "/api/v1/issues", json={"project_id": project_id, "raw_text": "커튼월 지연"}
    ).json()["id"]

    analyze_body = client.post(f"/api/v1/issues/{issue_id}/analyze").json()
    assert analyze_body["status"] == "NEEDS_ACTIVITY_SELECTION"
    assert analyze_body["selected_activity_id"] is None
    run_id = analyze_body["id"]

    select_body = client.post(
        f"/api/v1/issues/{issue_id}/select-activity",
        json={"analysis_run_id": run_id, "activity_id": "A100"},
    ).json()

    assert select_body["status"] == "COMPLETED"
    assert select_body["selected_activity_id"] == "A100"
    assert len(select_body["scenarios"]) == 3


def test_select_activity_rejects_unknown_activity(client) -> None:
    project_id = _setup_project_with_snapshot(client)
    _override_registry(client, _mapping_json(0.60))

    issue_id = client.post(
        "/api/v1/issues", json={"project_id": project_id, "raw_text": "커튼월 지연"}
    ).json()["id"]
    run_id = client.post(f"/api/v1/issues/{issue_id}/analyze").json()["id"]

    response = client.post(
        f"/api/v1/issues/{issue_id}/select-activity",
        json={"analysis_run_id": run_id, "activity_id": "GHOST"},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "activity_not_in_snapshot"


def test_get_analysis_run_and_report(client) -> None:
    project_id = _setup_project_with_snapshot(client)
    _upload_doc(client, project_id)
    _override_registry(client, _mapping_json(0.95))

    issue_id = client.post(
        "/api/v1/issues", json={"project_id": project_id, "raw_text": "A동 12층 커튼월 자재 10일 지연"}
    ).json()["id"]
    run_id = client.post(f"/api/v1/issues/{issue_id}/analyze").json()["id"]

    run_response = client.get(f"/api/v1/analysis-runs/{run_id}")
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "COMPLETED"

    report_response = client.get(f"/api/v1/analysis-runs/{run_id}/report.md")
    assert report_response.status_code == 200
    assert "P6 Schedule Recovery 분석 보고서" in report_response.text
    assert "복구 시나리오" in report_response.text


def test_analyze_unknown_issue_returns_404(client) -> None:
    response = client.post("/api/v1/issues/999/analyze")

    assert response.status_code == 404


def test_analyze_without_snapshot_returns_failed_or_error(client) -> None:
    project_id = client.post("/api/v1/projects", json={"name": "Empty"}).json()["id"]
    _override_registry(client, _mapping_json(0.95))
    issue_id = client.post(
        "/api/v1/issues", json={"project_id": project_id, "raw_text": "issue"}
    ).json()["id"]

    response = client.post(f"/api/v1/issues/{issue_id}/analyze")

    assert response.status_code == 422
    assert response.json()["error_code"] == "no_snapshot"
