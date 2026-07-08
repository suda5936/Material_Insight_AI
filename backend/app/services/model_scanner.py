from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from app.models.object import DesignObjectInput
from app.models.rule import RuleResult
from app.models.scan import ScanModelRequest, ScanModelResponse, ScanObjectResult, ScanSummary
from app.services.rule_engine import RuleEngine, load_default_rule_engine


SEVERITY_RANK: Dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}
ACTION_RANK: Dict[str, int] = {
    "none": 0,
    "designer_review": 1,
    "senior_review": 2,
    "need_more_input": 3,
    "expert_review": 4,
}


@dataclass(frozen=True)
class ModelScanner:
    rule_engine: RuleEngine

    def scan(self, request: ScanModelRequest) -> ScanModelResponse:
        results = [
            _scan_object(design_object, self.rule_engine.evaluate(design_object))
            for design_object in request.objects
        ]
        results.sort(
            key=lambda result: (
                ACTION_RANK[result.required_action],
                SEVERITY_RANK[result.severity],
                result.issue_count,
                result.object_id,
            ),
            reverse=True,
        )
        return ScanModelResponse(
            project_id=request.project.project_id,
            summary=_build_summary(request.objects, results),
            results=results,
        )


def load_default_model_scanner() -> ModelScanner:
    return ModelScanner(rule_engine=load_default_rule_engine())


def _scan_object(
    design_object: DesignObjectInput,
    rule_results: Sequence[RuleResult],
) -> ScanObjectResult:
    return ScanObjectResult(
        object_id=design_object.object_id,
        object_type=design_object.object_type,
        space_type=design_object.space_type,
        severity=_highest_severity(rule_results),
        issue_count=len(rule_results),
        issues=list(rule_results),
        required_action=_required_action(rule_results),
    )


def _build_summary(
    objects: Sequence[DesignObjectInput],
    results: Sequence[ScanObjectResult],
) -> ScanSummary:
    issue_counts: Dict[str, int] = {}
    severity_counts: Dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    required_action_counts: Dict[str, int] = {}

    for result in results:
        if result.issue_count > 0:
            severity_counts[result.severity] += 1
        required_action_counts[result.required_action] = (
            required_action_counts.get(result.required_action, 0) + 1
        )
        for issue in result.issues:
            issue_counts[issue.issue_code] = issue_counts.get(issue.issue_code, 0) + 1

    return ScanSummary(
        total_objects=len(objects),
        objects_with_issues=sum(1 for result in results if result.issue_count > 0),
        issue_counts=dict(sorted(issue_counts.items())),
        severity_counts=severity_counts,
        required_action_counts=dict(sorted(required_action_counts.items())),
    )


def _highest_severity(rule_results: Sequence[RuleResult]) -> str:
    if not rule_results:
        return "low"
    return max(rule_results, key=lambda result: SEVERITY_RANK[result.severity]).severity


def _required_action(rule_results: Sequence[RuleResult]) -> str:
    if any(result.requires_expert_review for result in rule_results):
        return "expert_review"

    issue_codes = {result.issue_code for result in rule_results}
    if {"object_type_missing", "space_type_missing"} & issue_codes:
        return "need_more_input"
    if rule_results:
        return "designer_review"
    return "none"
