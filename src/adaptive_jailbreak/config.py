from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from adaptive_jailbreak.schemas import (
    AnalysisConfig,
    EvaluatorConfig,
    ExperimentConfig,
    FrameworkConfig,
    ModelConfig,
    RunnerConfig,
    StorageConfig,
    TaskRecord,
    TasksConfig,
)
from adaptive_jailbreak.utils.hashing import stable_hash


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def read_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


class ConfigLoader:
    @staticmethod
    def load(path: str | Path, default_path: str | Path | None = None) -> FrameworkConfig:
        path = Path(path)
        raw = read_yaml(path)
        if default_path is not None:
            raw = deep_merge(read_yaml(default_path), raw)
        config_hash = stable_hash(raw)
        required = ["experiment", "attacker", "target", "evaluator", "tasks"]
        missing = [key for key in required if key not in raw]
        if missing:
            raise ValueError(f"Missing required config sections: {', '.join(missing)}")
        return FrameworkConfig(
            experiment=ExperimentConfig.from_dict(raw["experiment"]),
            attacker=ModelConfig.from_dict(raw["attacker"]),
            target=ModelConfig.from_dict(raw["target"]),
            evaluator=EvaluatorConfig.from_dict(raw["evaluator"]),
            tasks=TasksConfig.from_dict(raw["tasks"]),
            runner=RunnerConfig.from_dict(raw.get("runner", {})),
            storage=StorageConfig.from_dict(raw.get("storage")),
            analysis=AnalysisConfig.from_dict(raw.get("analysis")),
            config_hash=config_hash,
            config_path=str(path),
        )


def load_tasks(path: str | Path, task_ids: list[str] | None = None) -> list[TaskRecord]:
    raw = read_yaml(path)
    items = raw.get("tasks", [])
    if not isinstance(items, list):
        raise ValueError("Task file must contain a 'tasks' list")
    selected = set(task_ids or [])
    tasks = [TaskRecord.from_dict(item) for item in items]
    if selected:
        tasks = [task for task in tasks if task.task_id in selected]
    return tasks


def load_allowlist(path: str | Path | None) -> set[str]:
    if not path:
        return set()
    raw = read_yaml(path)
    return set(raw.get("allowed_task_ids", []))
