from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EvaluatorFeedback:
    success: bool = False
    refusal_detected: bool = False
    actionable_content_detected: bool = False
    failure_mode: str = "unknown"
    target_observations: list[str] = field(default_factory=list)
    suggested_next_strategy: str = ""
    do_not_repeat: list[str] = field(default_factory=list)
    confidence: float = 0.0
    rationale: str = ""
    validator_warnings: list[str] = field(default_factory=list)
    parse_error: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "EvaluatorFeedback":
        payload = dict(data or {})
        return cls(
            success=_as_bool(payload.get("success", payload.get("success_label") == "success")),
            refusal_detected=_as_bool(
                payload.get("refusal_detected", payload.get("refusal_label") == "refusal")
            ),
            actionable_content_detected=_as_bool(payload.get("actionable_content_detected", False)),
            failure_mode=str(payload.get("failure_mode") or "unknown"),
            target_observations=_as_string_list(
                payload.get("target_observations", payload.get("observations", []))
            ),
            suggested_next_strategy=str(
                payload.get("suggested_next_strategy")
                or payload.get("next_action_hint")
                or _first_string(payload.get("recommended_families", []))
            ),
            do_not_repeat=_as_string_list(payload.get("do_not_repeat", payload.get("avoid_families", []))),
            confidence=_as_float(payload.get("confidence", 0.0)),
            rationale=str(payload.get("rationale") or payload.get("model_feedback") or ""),
            validator_warnings=_as_string_list(payload.get("validator_warnings", [])),
            parse_error=_as_bool(payload.get("parse_error", False)),
        )

    @classmethod
    def from_rule_based(
        cls,
        *,
        success: bool,
        refusal_detected: bool,
        actionable_content_detected: bool,
        failure_mode: str | None,
        rationale: str,
        suggested_next_strategy: str | None = None,
        parse_error: bool = False,
    ) -> "EvaluatorFeedback":
        observations = []
        if refusal_detected:
            observations.append("Target response matched deterministic refusal evidence.")
        if actionable_content_detected:
            observations.append("Target response matched deterministic actionable-content evidence.")
        if not observations:
            observations.append("No deterministic refusal or actionable-content evidence was confirmed.")
        return cls(
            success=success,
            refusal_detected=refusal_detected,
            actionable_content_detected=actionable_content_detected,
            failure_mode=failure_mode or "unknown",
            target_observations=observations,
            suggested_next_strategy=suggested_next_strategy or "",
            confidence=0.5 if parse_error else 0.7,
            rationale=rationale,
            parse_error=parse_error,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_evaluator_json(text: str) -> dict[str, Any] | None:
    import json
    import re

    stripped = text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        stripped = fenced.group(1).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    candidate = stripped[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        repaired = _repair_json(candidate)
        try:
            parsed = json.loads(repaired)
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def _repair_json(text: str) -> str:
    import re

    repaired = text.replace("\r\n", "\n")
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    return repaired


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "success"}
    return bool(value)


def _as_float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _first_string(value: Any) -> str:
    values = _as_string_list(value)
    return values[0] if values else ""
