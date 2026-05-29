from __future__ import annotations

from pathlib import Path

from adaptive_jailbreak.schemas import FrameworkConfig, TaskRecord


class SafetyControls:
    def __init__(self, config: FrameworkConfig, project_root: str | Path | None = None) -> None:
        self.config = config
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.allowlist = set(config.tasks.allowed_task_ids)

    @classmethod
    def from_config(cls, config: FrameworkConfig, project_root: str | Path | None = None) -> "SafetyControls":
        return cls(config, project_root)

    def validate_experiment_config(self) -> None:
        if self.config.experiment.local_only:
            for name, model in (("attacker", self.config.attacker), ("target", self.config.target)):
                if model.adapter == "api" or model.provider not in {"dummy", "local"}:
                    raise ValueError(f"local_only blocks {name} provider/adapter: {model.provider}/{model.adapter}")
            evaluator_adapter = self.config.evaluator.adapter
            if evaluator_adapter == "api" or self.config.evaluator.provider not in {"dummy", "rule", "local"}:
                raise ValueError(
                    f"local_only blocks evaluator provider/adapter: "
                    f"{self.config.evaluator.provider}/{evaluator_adapter}"
                )
        if self.config.runner.max_iterations <= 0:
            raise ValueError("runner.max_iterations must be positive")
        self._validate_output_path(self.config.experiment.output_dir)

    def _validate_output_path(self, path: str) -> None:
        resolved = self._project_path(path).resolve()
        if self.project_root not in resolved.parents and resolved != self.project_root:
            raise ValueError(f"Output path escapes project root: {path}")

    def _project_path(self, path: str | Path) -> Path:
        path = Path(path)
        return path if path.is_absolute() else self.project_root / path

    def validate_task(self, task: TaskRecord) -> None:
        if self.allowlist and task.task_id not in self.allowlist:
            raise ValueError(f"Task is not allowlisted: {task.task_id}")
        if self.config.tasks.synthetic_only and not task.synthetic:
            raise ValueError(f"Task rejected by synthetic_only mode: {task.task_id}")

    def validate_generated_prompt(self, prompt: str) -> None:
        if "\x00" in prompt:
            raise ValueError("Generated prompt contains a null byte")

    def validate_inert_output(self, text: str) -> None:
        if "\x00" in text:
            raise ValueError("Model output contains a null byte")
