from typing import Literal, Optional

from app.models.common import APIModel


class RuleResult(APIModel):
    rule_id: str
    severity: Literal["low", "medium", "high", "critical"]
    issue_code: str
    message: str
    field: Optional[str] = None
    requires_rag: bool = False
    requires_expert_review: bool = False
