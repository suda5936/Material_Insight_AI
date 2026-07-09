from fastapi import APIRouter, Response

from app.models.rhino_sync import (
    RhinoObjectListResponse,
    RhinoObjectSummary,
    RhinoObjectSyncRequest,
    RhinoObjectSyncResponse,
    RhinoSelectionRequest,
    RhinoSelectionState,
)


router = APIRouter(prefix="/api/v1/rhino", tags=["rhino-sync"])

_object_store: dict[str, list[RhinoObjectSummary]] = {}
_selection_store: dict[str, str] = {}


@router.post("/objects", response_model=RhinoObjectSyncResponse)
def sync_rhino_objects(request: RhinoObjectSyncRequest) -> RhinoObjectSyncResponse:
    project_id = request.project.project_id
    _object_store[project_id] = list(request.objects)
    if project_id in _selection_store:
        object_ids = {obj.object_id for obj in request.objects}
        if _selection_store[project_id] not in object_ids:
            del _selection_store[project_id]

    return RhinoObjectSyncResponse(
        project_id=project_id,
        object_count=len(request.objects),
    )


@router.get("/objects", response_model=RhinoObjectListResponse)
def list_rhino_objects(project_id: str, response: Response) -> RhinoObjectListResponse:
    response.headers["Cache-Control"] = "no-store"
    return RhinoObjectListResponse(
        project_id=project_id,
        objects=_object_store.get(project_id, []),
    )


@router.post("/selection", response_model=RhinoSelectionState)
def set_rhino_selection(request: RhinoSelectionRequest) -> RhinoSelectionState:
    _selection_store[request.project_id] = request.object_id
    return RhinoSelectionState(
        project_id=request.project_id,
        object_id=request.object_id,
    )


@router.get("/selection", response_model=RhinoSelectionState)
def get_rhino_selection(project_id: str, response: Response) -> RhinoSelectionState:
    response.headers["Cache-Control"] = "no-store"
    return RhinoSelectionState(
        project_id=project_id,
        object_id=_selection_store.get(project_id),
    )
