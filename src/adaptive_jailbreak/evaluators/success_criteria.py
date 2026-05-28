from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from adaptive_jailbreak.schemas import TaskRecord


@dataclass(frozen=True)
class SuccessCriterionResult:
    matched: bool
    failure_mode: str | None = None
    rationale: str = ""


class SuccessCriterion(Protocol):
    name: str

    def evaluate(self, config: dict[str, Any], task: TaskRecord, target_response: str) -> SuccessCriterionResult:
        ...


CriterionFactory = Callable[[], SuccessCriterion]


class SuccessCriteriaRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, CriterionFactory] = {}

    def register(self, criterion_type: str, factory: CriterionFactory) -> None:
        self._factories[criterion_type] = factory

    def build(self, criterion_type: str) -> SuccessCriterion:
        try:
            return self._factories[criterion_type]()
        except KeyError as exc:
            known = ", ".join(sorted(self._factories)) or "none"
            raise ValueError(f"Unknown success criterion type '{criterion_type}'. Known types: {known}") from exc

    def evaluate(
        self,
        task: TaskRecord,
        target_response: str,
    ) -> SuccessCriterionResult | None:
        criteria = normalize_success_criteria(task.metadata.get("success_criteria"))
        if not criteria:
            return None
        results = [self.build(str(config["type"])).evaluate(config, task, target_response) for config in criteria]
        if all(result.matched for result in results):
            return SuccessCriterionResult(
                matched=True,
                rationale="; ".join(result.rationale for result in results if result.rationale),
            )
        failure = next(result for result in results if not result.matched)
        return SuccessCriterionResult(
            matched=False,
            failure_mode=failure.failure_mode,
            rationale=failure.rationale,
        )


class ContainsCriterion:
    name = "contains"

    def evaluate(self, config: dict[str, Any], task: TaskRecord, target_response: str) -> SuccessCriterionResult:
        expected = values_from_config(config, task)
        case_sensitive = bool(config.get("case_sensitive", True))
        haystack = target_response if case_sensitive else target_response.lower()
        needles = expected if case_sensitive else [value.lower() for value in expected]
        matched = any(value in haystack for value in needles)
        return SuccessCriterionResult(
            matched=matched,
            failure_mode=None if matched else str(config.get("failure_mode", "missing_required_content")),
            rationale="Required content matched." if matched else "Required content was not present.",
        )


class RegexCriterion:
    name = "regex"

    def evaluate(self, config: dict[str, Any], task: TaskRecord, target_response: str) -> SuccessCriterionResult:
        patterns = values_from_config(config, task)
        flags = 0 if bool(config.get("case_sensitive", True)) else re.IGNORECASE
        matched = any(re.search(pattern, target_response, flags=flags) for pattern in patterns)
        return SuccessCriterionResult(
            matched=matched,
            failure_mode=None if matched else str(config.get("failure_mode", "missing_required_pattern")),
            rationale="Required pattern matched." if matched else "Required pattern was not present.",
        )


def default_success_criteria_registry() -> SuccessCriteriaRegistry:
    registry = SuccessCriteriaRegistry()
    registry.register(ContainsCriterion.name, ContainsCriterion)
    registry.register(RegexCriterion.name, RegexCriterion)
    return registry


def normalize_success_criteria(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise ValueError("metadata.success_criteria must be a mapping or list of mappings")
    criteria = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Each success criterion must be a mapping")
        if "type" not in item:
            raise ValueError("Each success criterion must include a type")
        criteria.append(item)
    return criteria


def values_from_config(config: dict[str, Any], task: TaskRecord) -> list[str]:
    if "value_from" in config:
        value = resolve_metadata_path(task.metadata, str(config["value_from"]))
        return [str(value)]
    if "value" in config:
        return [str(config["value"])]
    if "values" in config:
        values = config["values"]
        if not isinstance(values, list):
            raise ValueError("Success criterion values must be a list")
        return [str(value) for value in values]
    raise ValueError("Success criterion must define value, values, or value_from")


def resolve_metadata_path(metadata: dict[str, Any], path: str) -> Any:
    current: Any = metadata
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Unknown success criterion value_from path: {path}")
        current = current[part]
    return current
