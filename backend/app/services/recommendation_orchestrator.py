from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence
from uuid import uuid4

from app.models.document import RetrievedDocument
from app.models.object import ReviewObjectRequest
from app.models.recommendation import RecommendationResult
from app.models.rule import RuleResult
from app.services.local_retriever import LocalRetriever, load_default_retriever
from app.services.rule_engine import RuleEngine, load_default_rule_engine


SEVERITY_RANK: Dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


@dataclass(frozen=True)
class RecommendationOrchestrator:
    rule_engine: RuleEngine
    retriever: LocalRetriever
    retrieval_limit: int = 5

    def review_object(self, request: ReviewObjectRequest) -> RecommendationResult:
        design_object = request.object
        rule_results = self.rule_engine.evaluate(design_object)
        sources = self.retriever.search_relevant(
            design_object,
            rule_results,
            limit=self.retrieval_limit,
        )

        return RecommendationResult(
            recommendation_id=f"REC-{uuid4().hex[:12].upper()}",
            object_id=design_object.object_id,
            status=_status_for(rule_results),
            severity=_highest_severity(rule_results),
            summary=_build_summary(rule_results, sources),
            detected_issues=[result.issue_code for result in rule_results],
            material_candidates=_material_candidates(rule_results, sources),
            thickness_guidance=_thickness_guidance(request, rule_results, sources),
            performance_notes=_performance_notes(rule_results, sources),
            required_action=_required_action_for(rule_results, sources),
            confidence=_confidence(rule_results, sources),
            sources=sources,
            disclaimers=_disclaimers(rule_results, sources),
        )


def load_default_orchestrator() -> RecommendationOrchestrator:
    return RecommendationOrchestrator(
        rule_engine=load_default_rule_engine(),
        retriever=load_default_retriever(),
    )


def _highest_severity(rule_results: Sequence[RuleResult]) -> str:
    if not rule_results:
        return "low"
    return max(rule_results, key=lambda result: SEVERITY_RANK[result.severity]).severity


def _status_for(rule_results: Sequence[RuleResult]) -> str:
    if any(result.requires_expert_review for result in rule_results):
        return "blocked"
    if rule_results:
        return "review_required"
    return "ok"


def _required_action_for(
    rule_results: Sequence[RuleResult],
    sources: Sequence[RetrievedDocument],
) -> str:
    if any(result.requires_expert_review for result in rule_results):
        return "expert_review"
    if _has_missing_context(rule_results):
        return "need_more_input"
    if rule_results:
        return "designer_review" if sources else "senior_review"
    return "none"


def _build_summary(
    rule_results: Sequence[RuleResult],
    sources: Sequence[RetrievedDocument],
) -> str:
    if not rule_results:
        return "No rule issues were detected for this object."

    issues = ", ".join(result.issue_code for result in rule_results)
    if sources:
        source_ids = ", ".join(document.document_id for document in sources[:3])
        return (
            f"Rule Engine detected: {issues}. "
            f"Relevant source documents were adopted: {source_ids}."
        )
    return (
        f"Rule Engine detected: {issues}. "
        "No relevant source document passed the retrieval threshold."
    )


def _material_candidates(
    rule_results: Sequence[RuleResult],
    sources: Sequence[RetrievedDocument],
) -> List[str]:
    issue_codes = {result.issue_code for result in rule_results}
    source_text = " ".join(
        f"{document.title} {document.section or ''} {document.chunk_text}"
        for document in sources
    ).lower()

    if "material_missing" not in issue_codes or not sources:
        return []
    if "gypsum" in source_text:
        return [
            "gypsum board assembly",
            "acoustic board assembly",
        ]
    return ["material option from adopted source documents"]


def _thickness_guidance(
    request: ReviewObjectRequest,
    rule_results: Sequence[RuleResult],
    sources: Sequence[RetrievedDocument],
) -> Dict[str, object]:
    issue_codes = {result.issue_code for result in rule_results}
    if not ({"thickness_missing", "thickness_review_required"} & issue_codes):
        return {}

    guidance: Dict[str, object] = {
        "current_mm": request.object.thickness_mm,
        "message": "Review wall thickness before accepting the recommendation.",
    }
    if sources:
        guidance["basis"] = "Adopted source documents are available."
    else:
        guidance["basis"] = "No source document passed the retrieval threshold."
    return guidance


def _performance_notes(
    rule_results: Sequence[RuleResult],
    sources: Sequence[RetrievedDocument],
) -> List[str]:
    issue_codes = {result.issue_code for result in rule_results}
    notes: List[str] = []
    if "acoustic_review_required" in issue_codes:
        notes.append("Acoustic performance should be reviewed for this object.")
    if "material_performance_review_required" in issue_codes:
        notes.append("Material performance should be checked against the space use.")
    if rule_results and not sources:
        notes.append("No source document passed the relevance threshold.")
    return notes


def _confidence(
    rule_results: Sequence[RuleResult],
    sources: Sequence[RetrievedDocument],
) -> float:
    if not rule_results:
        return 0.75
    if sources:
        return 0.72
    return 0.45


def _disclaimers(
    rule_results: Sequence[RuleResult],
    sources: Sequence[RetrievedDocument],
) -> List[str]:
    disclaimers = [
        "This result supports designer review and does not automatically modify Rhino objects.",
        "Structural, fire, and code compliance decisions require human confirmation.",
    ]
    if rule_results and not sources:
        disclaimers.append(
            "No relevant document passed the retrieval threshold; do not treat this as evidence-based guidance."
        )
    return disclaimers


def _has_missing_context(rule_results: Sequence[RuleResult]) -> bool:
    issue_codes = {result.issue_code for result in rule_results}
    return bool({"object_type_missing", "space_type_missing"} & issue_codes)
