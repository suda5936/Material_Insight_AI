from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError
from app.db.models import Activity, Project
from app.db.models import Relationship as RelationshipModel
from app.db.models import ScheduleSnapshot
from app.db.session import get_db
from app.models.schedule import (
    SnapshotHealthResponse,
    SnapshotImportResponse,
    SnapshotSummaryResponse,
)
from app.services.schedule_import import (
    detect_cycle,
    parse_activities_csv,
    parse_relationships_csv,
    validate_relationship_references,
)

router = APIRouter(tags=["schedule"])


@router.post(
    "/api/v1/projects/{project_id}/snapshots/import",
    response_model=SnapshotImportResponse,
    status_code=201,
)
async def import_snapshot(
    project_id: int,
    activities_csv: UploadFile = File(...),
    relationships_csv: UploadFile = File(...),
    label: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> SnapshotImportResponse:
    project = await db.get(Project, project_id)
    if project is None:
        raise APIError(
            status_code=404,
            error_code="project_not_found",
            message=f"Project {project_id} was not found.",
        )

    activities_raw = (await activities_csv.read()).decode("utf-8-sig")
    relationships_raw = (await relationships_csv.read()).decode("utf-8-sig")

    activities = parse_activities_csv(activities_raw)
    relationships = parse_relationships_csv(relationships_raw)
    validate_relationship_references(activities, relationships)
    is_dag, cycle_activity_ids = detect_cycle(activities, relationships)

    warnings: list[str] = []
    if not is_dag:
        warnings.append(
            "Schedule network contains a cycle and is not a valid DAG: "
            + ", ".join(cycle_activity_ids)
        )

    snapshot = ScheduleSnapshot(
        project_id=project_id,
        label=label,
        activity_count=len(activities),
        relationship_count=len(relationships),
        is_dag=is_dag,
        cycle_activity_ids=",".join(cycle_activity_ids) if cycle_activity_ids else None,
    )
    db.add(snapshot)
    await db.flush()

    for activity in activities:
        db.add(
            Activity(
                snapshot_id=snapshot.id,
                activity_id=activity.activity_id,
                name=activity.name,
                original_duration=activity.original_duration,
                remaining_duration=activity.remaining_duration,
                is_milestone=activity.is_milestone,
                is_completed=activity.is_completed,
            )
        )
    for relationship in relationships:
        db.add(
            RelationshipModel(
                snapshot_id=snapshot.id,
                predecessor_id=relationship.predecessor_id,
                successor_id=relationship.successor_id,
                type=relationship.type,
                lag=relationship.lag,
            )
        )

    await db.commit()

    return SnapshotImportResponse(
        snapshot_id=snapshot.id,
        project_id=project_id,
        label=label,
        activity_count=len(activities),
        relationship_count=len(relationships),
        is_dag=is_dag,
        warnings=warnings,
    )


@router.get(
    "/api/v1/projects/{project_id}/snapshots",
    response_model=list[SnapshotSummaryResponse],
)
async def list_snapshots(
    project_id: int, db: AsyncSession = Depends(get_db)
) -> list[ScheduleSnapshot]:
    result = await db.execute(
        select(ScheduleSnapshot)
        .where(ScheduleSnapshot.project_id == project_id)
        .order_by(ScheduleSnapshot.imported_at.desc())
    )
    return list(result.scalars().all())


@router.get(
    "/api/v1/snapshots/{snapshot_id}/health",
    response_model=SnapshotHealthResponse,
)
async def get_snapshot_health(
    snapshot_id: int, db: AsyncSession = Depends(get_db)
) -> SnapshotHealthResponse:
    result = await db.execute(
        select(ScheduleSnapshot).where(ScheduleSnapshot.id == snapshot_id)
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        raise APIError(
            status_code=404,
            error_code="snapshot_not_found",
            message=f"Snapshot {snapshot_id} was not found.",
        )

    cycle_activity_ids = (
        snapshot.cycle_activity_ids.split(",") if snapshot.cycle_activity_ids else []
    )

    return SnapshotHealthResponse(
        snapshot_id=snapshot.id,
        project_id=snapshot.project_id,
        label=snapshot.label,
        imported_at=snapshot.imported_at,
        activity_count=snapshot.activity_count,
        relationship_count=snapshot.relationship_count,
        is_dag=snapshot.is_dag,
        cycle_activity_ids=cycle_activity_ids,
    )
