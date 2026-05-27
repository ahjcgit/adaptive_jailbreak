from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path

from adaptive_jailbreak.adapters import build_adapter
from adaptive_jailbreak.agents import AttackerAgent, TargetAgent
from adaptive_jailbreak.config import ConfigLoader, load_tasks
from adaptive_jailbreak.evaluators import build_evaluator
from adaptive_jailbreak.safety import SafetyControls
from adaptive_jailbreak.schemas import FrameworkConfig, TrajectoryRecord
from adaptive_jailbreak.storage import JsonlTrajectoryStore
from adaptive_jailbreak.strategies import build_strategy
from adaptive_jailbreak.utils.time import now_utc


def compute_novelty(prompt: str, trajectory: list[TrajectoryRecord]) -> float | None:
    if not trajectory:
        return None
    previous = trajectory[-1].attacker_prompt
    return 1.0 - SequenceMatcher(None, previous, prompt).ratio()


def stopping_criteria_met(config: FrameworkConfig, scores, trajectory: list[TrajectoryRecord]) -> bool:
    stopping = config.runner.stopping
    if stopping.stop_on_success and scores.success_label == "success":
        return True
    if scores.compliance_score >= stopping.min_compliance_score and scores.refusal_score <= stopping.max_refusal_score:
        return stopping.stop_on_success
    if stopping.patience is not None and len(trajectory) >= stopping.patience:
        recent = trajectory[-stopping.patience :]
        return all(step.success_label != "success" for step in recent)
    return False


class ExperimentRunner:
    def __init__(self, config: FrameworkConfig, project_root: str | Path | None = None) -> None:
        self.config = config
        self.project_root = Path(project_root or Path.cwd())
        self.controls = SafetyControls.from_config(config, self.project_root)
        self.controls.validate_experiment_config()
        self.store = JsonlTrajectoryStore(
            output_dir=self.project_root / config.experiment.output_dir,
            experiment_id=config.experiment.experiment_id,
            config_hash=config.config_hash,
            config_path=config.config_path,
            flush_each_record=config.storage.flush_each_record,
        )
        attacker_adapter = build_adapter(config.attacker.adapter, config.attacker.model, config.attacker.provider)
        target_adapter = build_adapter(config.target.adapter, config.target.model, config.target.provider)
        self.attacker = AttackerAgent(
            adapter=attacker_adapter,
            strategy=build_strategy(config.attacker.strategy),
            generation_config=config.attacker.generation,
        )
        self.target = TargetAgent(adapter=target_adapter, generation_config=config.target.generation)
        self.evaluator = build_evaluator(config.evaluator)

    @classmethod
    def from_config_path(cls, path: str | Path, project_root: str | Path | None = None) -> "ExperimentRunner":
        return cls(ConfigLoader.load(path), project_root=project_root)

    def run(self, resume_run_id: str | None = None, force_config: bool = False) -> list[TrajectoryRecord]:
        task_path = self.project_root / self.config.tasks.task_set_path
        tasks = load_tasks(task_path, self.config.tasks.task_ids)
        if not tasks:
            selected = ", ".join(self.config.tasks.task_ids) if self.config.tasks.task_ids else "all tasks"
            raise ValueError(f"No tasks matched {selected} in {task_path}")
        all_records: list[TrajectoryRecord] = []
        for task in tasks:
            self.controls.validate_task(task)
            run_id = self.store.create_or_resume_run(task.task_id, resume_run_id, force_config=force_config)
            trajectory = self.store.load_trajectory(run_id)
            try:
                for iteration in range(len(trajectory), self.config.runner.max_iterations):
                    if iteration == 0 and not trajectory:
                        candidate = self.attacker.initial_prompt(task, self.config.attacker.context)
                    else:
                        candidate = self.attacker.next_prompt(task, trajectory[-1], trajectory, self.config.attacker.context)
                    self.controls.validate_generated_prompt(candidate.prompt)
                    response = self.target.respond(candidate.prompt, iteration=iteration)
                    self.controls.validate_inert_output(response.text)
                    scores = self.evaluator.score(task, candidate.prompt, response.text, trajectory)
                    record = TrajectoryRecord(
                        experiment_id=self.config.experiment.experiment_id,
                        run_id=run_id,
                        task_id=task.task_id,
                        iteration=iteration,
                        attacker_model=self.config.attacker.model,
                        target_model=self.config.target.model,
                        evaluator_model_or_type=f"{self.config.evaluator.type}:{self.config.evaluator.model or self.config.evaluator.provider}",
                        attacker_prompt=candidate.prompt,
                        target_response=response.text,
                        evaluator_scores=scores.to_dict(),
                        success_label=scores.success_label,
                        refusal_label=scores.refusal_label,
                        attacker_reflection=candidate.reflection,
                        strategy_tags=sorted(set(candidate.strategy_tags + scores.strategy_tags)),
                        timestamp=now_utc(),
                        config_hash=self.config.config_hash,
                        metadata={
                            "prompt_length": len(candidate.prompt),
                            "response_length": len(response.text),
                            "iteration_efficiency": None,
                            "novelty_from_previous": compute_novelty(candidate.prompt, trajectory),
                            "failure_mode": scores.failure_mode,
                            "adapter_latency_ms": response.metadata.get("latency_ms"),
                            "token_usage": response.metadata.get("token_usage", {}),
                        },
                    )
                    self.store.append(record)
                    trajectory.append(record)
                    all_records.append(record)
                    if stopping_criteria_met(self.config, scores, trajectory):
                        self.store.mark_run_complete(run_id, reason="stopping_criteria")
                        break
                else:
                    self.store.mark_run_complete(run_id, reason="max_iterations")
            except Exception as exc:
                self.store.mark_run_failed(run_id, str(exc))
                raise
            if resume_run_id:
                break
        return all_records

    def replay(self, run_id: str | None = None) -> list[TrajectoryRecord]:
        return self.store.load_trajectory(run_id)
