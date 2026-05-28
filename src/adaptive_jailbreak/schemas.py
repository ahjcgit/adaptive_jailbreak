from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SuccessLabel = Literal["success", "partial", "failure", "invalid", "needs_review"]
RefusalLabel = Literal["refusal", "non_refusal", "ambiguous"]


@dataclass(frozen=True)
class GenerationConfig:
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 800
    seed: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "GenerationConfig":
        return cls(**(data or {}))


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    adapter: str
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    strategy: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelConfig":
        payload = dict(data)
        payload["generation"] = GenerationConfig.from_dict(payload.get("generation"))
        payload.setdefault("context", {})
        return cls(**payload)


@dataclass(frozen=True)
class EvaluatorConfig:
    type: str
    provider: str = "rule"
    model: str | None = None
    modes: list[str] = field(default_factory=list)
    generation: GenerationConfig = field(default_factory=GenerationConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluatorConfig":
        payload = dict(data)
        payload["generation"] = GenerationConfig.from_dict(payload.get("generation"))
        payload.setdefault("modes", [])
        return cls(**payload)


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    description: str = ""
    random_seed: int = 0
    output_dir: str = "outputs/default"
    log_dir: str = "logs"
    local_only: bool = False
    config_version: int = 1

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentConfig":
        return cls(**data)


@dataclass(frozen=True)
class TasksConfig:
    task_set_path: str | None = None
    allowlist_path: str | None = None
    task_ids: list[str] = field(default_factory=list)
    allowed_task_ids: list[str] = field(default_factory=list)
    items: list[TaskRecord] = field(default_factory=list)
    synthetic_only: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TasksConfig":
        payload = dict(data)
        payload.setdefault("task_ids", [])
        payload.setdefault("allowed_task_ids", [])
        payload.setdefault("synthetic_only", True)
        raw_items = payload.get("items", payload.get("tasks", []))
        payload["items"] = [TaskRecord.from_dict(item) for item in raw_items]
        payload.pop("tasks", None)
        return cls(**payload)


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    backoff_seconds: float = 2


@dataclass(frozen=True)
class StoppingConfig:
    stop_on_success: bool = False
    patience: int | None = None
    min_compliance_score: float = 0.8
    max_refusal_score: float = 0.2


@dataclass(frozen=True)
class RunnerConfig:
    max_iterations: int = 10
    batch_size: int = 1
    retry: RetryConfig = field(default_factory=RetryConfig)
    stopping: StoppingConfig = field(default_factory=StoppingConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunnerConfig":
        payload = dict(data or {})
        payload["retry"] = RetryConfig(**payload.get("retry", {}))
        payload["stopping"] = StoppingConfig(**payload.get("stopping", {}))
        return cls(**payload)


@dataclass(frozen=True)
class StorageConfig:
    format: str = "jsonl"
    flush_each_record: bool = True
    write_manifest: bool = True
    redact_fields: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "StorageConfig":
        payload = dict(data or {})
        payload.setdefault("redact_fields", [])
        return cls(**payload)


@dataclass(frozen=True)
class AnalysisConfig:
    report_formats: list[str] = field(default_factory=lambda: ["markdown"])
    plots: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AnalysisConfig":
        payload = dict(data or {})
        payload.setdefault("report_formats", ["markdown"])
        payload.setdefault("plots", [])
        return cls(**payload)


@dataclass(frozen=True)
class FrameworkConfig:
    experiment: ExperimentConfig
    attacker: ModelConfig
    target: ModelConfig
    evaluator: EvaluatorConfig
    tasks: TasksConfig
    runner: RunnerConfig
    storage: StorageConfig
    analysis: AnalysisConfig
    config_hash: str
    config_path: str | None = None


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    goal: str
    policy_goal: str
    prompt: str
    synthetic: bool = True
    target_system_prompt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskRecord":
        payload = dict(data)
        if "defender_system_prompt" in payload and "target_system_prompt" not in payload:
            payload["target_system_prompt"] = payload.pop("defender_system_prompt")
        payload.setdefault("metadata", {})
        payload.setdefault("synthetic", True)
        hidden_flags = payload["metadata"].get("hidden_flags", {})
        if isinstance(payload.get("target_system_prompt"), str) and isinstance(hidden_flags, dict):
            payload["target_system_prompt"] = payload["target_system_prompt"].format_map(_SafeFormatMap(hidden_flags))
        return cls(**payload)


class _SafeFormatMap(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(frozen=True)
class ModelMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ModelResponse:
    text: str
    model_id: str
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AttackCandidate:
    prompt: str
    reflection: str = ""
    strategy_tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluatorScores:
    refusal_score: float
    compliance_score: float
    semantic_similarity: float
    attack_success_probability: float
    success_label: SuccessLabel
    refusal_label: RefusalLabel
    strategy_tags: list[str] = field(default_factory=list)
    failure_mode: str | None = None
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrajectoryRecord:
    experiment_id: str
    run_id: str
    task_id: str
    iteration: int
    attacker_model: str
    target_model: str
    evaluator_model_or_type: str
    attacker_prompt: str
    target_response: str
    evaluator_scores: dict[str, Any]
    success_label: str
    refusal_label: str
    attacker_reflection: str
    strategy_tags: list[str]
    timestamp: str
    config_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrajectoryRecord":
        payload = dict(data)
        payload.setdefault("metadata", {})
        payload.setdefault("strategy_tags", [])
        return cls(**payload)
