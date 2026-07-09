from typing import Any, Dict, List, Optional

from pydantic import Field

from app.models.common import APIModel
from app.models.object import ProjectContext


class RhinoObjectSummary(APIModel):
    object_id: str
    rhino_id: Optional[str] = None
    name: Optional[str] = None
    layer: Optional[str] = None
    object_kind: Optional[str] = None
    material: Optional[str] = None
    object_type: Optional[str] = None
    space_type: Optional[str] = None
    thickness_mm: Optional[float] = None
    review_status: Optional[str] = None
    is_visible: bool = True
    is_locked: bool = False
    bbox: Dict[str, Any] = Field(default_factory=dict)
    user_attributes: Dict[str, Any] = Field(default_factory=dict)


class RhinoObjectSyncRequest(APIModel):
    project: ProjectContext
    objects: List[RhinoObjectSummary] = Field(default_factory=list)


class RhinoObjectSyncResponse(APIModel):
    project_id: str
    object_count: int


class RhinoObjectListResponse(APIModel):
    project_id: str
    objects: List[RhinoObjectSummary] = Field(default_factory=list)


class RhinoSelectionRequest(APIModel):
    project_id: str
    object_id: str


class RhinoSelectionState(APIModel):
    project_id: str
    object_id: Optional[str] = None
