from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


SafetyMode = Literal["restricted", "unrestricted"]


@dataclass(frozen=True)
class AdapterConfig:
    backend: str
    model: str | None = None
    base_url: str | None = None
    api_key_env: str | None = None
    timeout_s: float = 60.0


@dataclass(frozen=True)
class PromptCandidate:
    prompt: str
    family: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class ModelResponse:
    text: str
    raw: dict[str, Any] | None = None
    usage: ModelUsage = field(default_factory=ModelUsage)
    finish_reason: str | None = None


@dataclass(frozen=True)
class Timings:
    latency_s: float


@dataclass(frozen=True)
class JudgeResult:
    mode: SafetyMode
    jailbreak_success: bool
    refusal_score: float  # 0 (not refusing) .. 1 (strong refusal)
    structure_score: float  # 0..1
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TrialRecord:
    run_id: str
    trial_idx: int
    mode: SafetyMode

    generator: AdapterConfig
    target: AdapterConfig
    policy: str

    candidate: PromptCandidate

    generator_timing: Timings
    target_timing: Timings
    response: ModelResponse

    judge: JudgeResult

    created_at_unix_s: float


@dataclass
class ExperimentState:
    run_id: str
    mode: SafetyMode
    budget: int
    policy_name: str
    history: list[TrialRecord] = field(default_factory=list)

