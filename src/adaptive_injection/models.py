from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass(slots=True)
class PromptSeed:
    seed_id: str
    family: str
    prompt: str
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PromptCandidate:
    candidate_id: str
    seed_id: str
    seed_family: str
    prompt_text: str
    mutation_chain: list[str] = field(default_factory=list)
    turn_idx: int = 1
    parent_candidate_id: str | None = None
    features: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TargetResponse:
    text: str
    latency_ms: int
    token_usage: int | None = None
    raw: dict[str, Any] | None = None


@dataclass(slots=True)
class JudgeResult:
    score: int
    label: str
    confidence: float
    rationale: str
    policy_category: str = "unknown"
    features: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DefenseConfig:
    system_hardening: bool = False
    input_moderation: bool = False
    output_moderation: bool = False
    self_critique: bool = False
    response_normalization: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TrialRecord:
    trial_id: str
    run_id: str
    parent_trial_id: str | None
    step_idx: int
    turn_idx: int
    target: str
    defense_config: dict[str, Any]
    attack_policy: str
    seed_family: str
    seed_id: str
    mutation_applied: list[str]
    prompt_text: str
    target_response: str
    judge_score: int
    judge_label: str
    judge_confidence: float
    latency_ms: int
    token_usage: int | None
    cost_estimate: float
    blocked_by_input_guard: bool = False
    blocked_by_output_guard: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExperimentConfig:
    run_id: str
    seeds_path: str
    benign_path: str
    artifact_dir: str
    budget: int
    max_turns: int
    attack_policy: str
    target_name: str
    defense: DefenseConfig
    seed: int = 0


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
