from datetime import datetime

from app.models.common import APIModel


class ProjectCreateRequest(APIModel):
    name: str
    description: str | None = None


class ProjectResponse(APIModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime


class SnapshotImportResponse(APIModel):
    snapshot_id: int
    project_id: int
    label: str
    activity_count: int
    relationship_count: int
    is_dag: bool
    warnings: list[str]


class SnapshotHealthResponse(APIModel):
    snapshot_id: int
    project_id: int
    label: str
    imported_at: datetime
    activity_count: int
    relationship_count: int
    is_dag: bool | None
    cycle_activity_ids: list[str]


class SnapshotSummaryResponse(APIModel):
    id: int
    project_id: int
    label: str
    imported_at: datetime
    activity_count: int
    relationship_count: int
    is_dag: bool | None
