from typing import Dict, List, Literal

from pydantic import Field

from app.models.common import APIModel
from app.models.object import DesignObjectInput, ProjectContext
from app.models.rule import RuleResult


class ScanModelRequest(APIModel):
    project: ProjectContext
    objects: List[DesignObjectInput]


class ScanObjectResult(APIModel):
    object_id: str
    object_type: str | None = None
    space_type: str | None = None
    severity: Literal["low", "medium", "high", "critical"]
    issue_count: int
    issues: List[RuleResult] = Field(default_factory=list)
    required_action: Literal[
        "none",
        "designer_review",
        "senior_review",
        "expert_review",
        "need_more_input",
    ]


class ScanSummary(APIModel):
    total_objects: int
    objects_with_issues: int
    issue_counts: Dict[str, int] = Field(default_factory=dict)
    severity_counts: Dict[str, int] = Field(default_factory=dict)
    required_action_counts: Dict[str, int] = Field(default_factory=dict)


class ScanModelResponse(APIModel):
    project_id: str
    summary: ScanSummary
    results: List[ScanObjectResult] = Field(default_factory=list)
