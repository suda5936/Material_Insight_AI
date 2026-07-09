from datetime import datetime

from app.models.common import APIModel


class IssueCreateRequest(APIModel):
    project_id: int
    raw_text: str


class IssueResponse(APIModel):
    id: int
    project_id: int
    raw_text: str
    created_at: datetime


class SelectActivityRequest(APIModel):
    analysis_run_id: int
    activity_id: str


class ActivityMatchResponse(APIModel):
    activity_id: str
    name: str
    sql_score: float
    agent_confidence: float | None
    agent_reason: str | None
    rank: int
    is_selected: bool


class ScenarioResponse(APIModel):
    scenario_index: int
    action: str
    target_activity_id: str
    reduction_days: int
    adjusted_value_days: int
    scenario_project_duration: int
    recovered_days: int
    applicable: bool
    rationale: str | None
    evidence_chunk_ids: list[int]


class AnalysisRunResponse(APIModel):
    id: int
    issue_id: int
    project_id: int
    snapshot_id: int
    status: str
    selected_activity_id: str | None
    issue_delay_days: int | None
    impact_mode: str | None
    retrieved_chunk_ids: list[int]
    baseline_json: dict | None
    impact_json: dict | None
    rule_validation_json: dict | None
    review_json: dict | None
    error_message: str | None
    activity_matches: list[ActivityMatchResponse]
    scenarios: list[ScenarioResponse]
    created_at: datetime
    updated_at: datetime
