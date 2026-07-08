from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

import yaml

from app.models.object import DesignObjectInput
from app.models.rule import RuleResult


class RuleEngineError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuleEngine:
    rules: List[Dict[str, Any]]

    @classmethod
    def from_yaml(cls, path: Path) -> "RuleEngine":
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        rules = raw.get("rules")
        if not isinstance(rules, list):
            raise RuleEngineError("Rule file must contain a 'rules' list.")
        return cls(rules=rules)

    def evaluate(self, design_object: DesignObjectInput) -> List[RuleResult]:
        payload = design_object.model_dump()
        results: List[RuleResult] = []
        for rule in self.rules:
            if not self._target_matches(rule, design_object.object_type):
                continue
            condition = rule.get("condition", {})
            if self._condition_matches(condition, payload):
                results.append(self._build_result(rule))
        return results

    def evaluate_many(
        self, design_objects: Iterable[DesignObjectInput]
    ) -> Dict[str, List[RuleResult]]:
        return {
            design_object.object_id: self.evaluate(design_object)
            for design_object in design_objects
        }

    def _target_matches(self, rule: Mapping[str, Any], object_type: Optional[str]) -> bool:
        target = rule.get("target_object_type")
        if target is None:
            return True
        if isinstance(target, str):
            return target == object_type
        if isinstance(target, list):
            return object_type in target
        raise RuleEngineError(f"Invalid target_object_type in {rule.get('rule_id')}")

    def _condition_matches(self, condition: Mapping[str, Any], payload: Dict[str, Any]) -> bool:
        if "all" in condition:
            return all(self._condition_matches(item, payload) for item in condition["all"])
        if "any" in condition:
            return any(self._condition_matches(item, payload) for item in condition["any"])

        field = condition.get("field")
        operator = condition.get("operator")
        expected = condition.get("value")
        actual = _get_field_value(payload, field)
        return _evaluate_operator(actual=actual, operator=operator, expected=expected)

    def _build_result(self, rule: Mapping[str, Any]) -> RuleResult:
        result = rule.get("result", {})
        return RuleResult(
            rule_id=str(rule["rule_id"]),
            severity=result["severity"],
            issue_code=result["issue_code"],
            message=result["message"],
            field=result.get("field"),
            requires_rag=bool(result.get("requires_rag", False)),
            requires_expert_review=bool(result.get("requires_expert_review", False)),
        )


def load_default_rule_engine() -> RuleEngine:
    return RuleEngine.from_yaml(default_rules_path())


def default_rules_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "rules" / "material_insight_rules.yaml"


def _get_field_value(payload: Dict[str, Any], field_path: Optional[str]) -> Any:
    if not field_path:
        raise RuleEngineError("Rule condition requires a field.")

    current: Any = payload
    for part in field_path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _evaluate_operator(actual: Any, operator: Optional[str], expected: Any = None) -> bool:
    if operator == "is_null":
        return actual is None or actual == ""
    if operator == "is_not_null":
        return actual is not None and actual != ""
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "less_than":
        return actual is not None and float(actual) < float(expected)
    if operator == "greater_than":
        return actual is not None and float(actual) > float(expected)
    if operator == "contains":
        return actual is not None and str(expected).lower() in str(actual).lower()
    raise RuleEngineError(f"Unsupported rule operator: {operator}")
