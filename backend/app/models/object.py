from typing import Any, Dict, Optional

from pydantic import Field

from app.models.common import APIModel


class GeometrySummary(APIModel):
    object_kind: Optional[str] = None
    length_mm: Optional[float] = None
    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    bbox: Dict[str, Any] = Field(default_factory=dict)


class DesignObjectInput(APIModel):
    object_id: str
    object_type: Optional[str] = None
    layer: Optional[str] = None
    name: Optional[str] = None
    material: Optional[str] = None
    thickness_mm: Optional[float] = None
    space_type: Optional[str] = None
    review_status: Optional[str] = None
    geometry: GeometrySummary = Field(default_factory=GeometrySummary)
    user_attributes: Dict[str, Any] = Field(default_factory=dict)


class ProjectContext(APIModel):
    project_id: str
    project_type: Optional[str] = None
    design_stage: Optional[str] = None
    building_use: Optional[str] = None
    region: Optional[str] = None
    priority: Optional[str] = None


class ReviewObjectRequest(APIModel):
    project: ProjectContext
    object: DesignObjectInput
