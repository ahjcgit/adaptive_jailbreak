from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path

from adaptive_jailbreak.adapters import build_adapter
from adaptive_jailbreak.agents import AttackerAgent, TargetAgent
from adaptive_jailbreak.config import select_tasks
from adaptive_jailbreak.evaluators import build_evaluator
from adaptive_jailbreak.safety import SafetyControls
from adaptive_jailbreak.schemas import FrameworkConfig, TaskRecord, TrajectoryRecord
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
        attacker_adapter = build_adapter(config.attacker, auth=config.auth)
        target_adapter = build_adapter(config.target, auth=config.auth)
        self.attacker = AttackerAgent(
            adapter=attacker_adapter,
            strategy=build_strategy(config.attacker.strategy),
            generation_config=config.attacker.generation,
        )
        self.target = TargetAgent(adapter=target_adapter, generation_config=config.target.generation)
        self.evaluator = build_evaluator(config.evaluator, auth=config.auth)

    def run(self, resume_run_id: str | None = None, force_config: bool = False) -> list[TrajectoryRecord]:
        tasks = self._load_configured_tasks()
        if not tasks:
            selected = ", ".join(self.config.tasks.task_ids) if self.config.tasks.task_ids else "all tasks"
            raise ValueError(f"No tasks matched {selected}")
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
                        candidate = self.attacker.next_prompt(task, trajectory, self.config.attacker.context)
                    self.controls.validate_generated_prompt(candidate.prompt)
                    response = self.target.respond(
                        candidate.prompt,
                        iteration=iteration,
                        system_prompt=task.target_system_prompt,
                    )
                    raw_target_response = str(response.metadata.get("raw_target_response", response.text))
                    self.controls.validate_inert_output(raw_target_response)
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
                            "attacker_random_seed": self.config.attacker.generation.seed,
                            "defender_random_seed": self.config.target.generation.seed,
                            "prompt_length": len(candidate.prompt),
                            "response_length": len(response.text),
                            "target_response_sanitized": response.metadata.get("target_response_sanitized", False),
                            "graded_response": "target_response",
                            "attack_family": candidate.metadata.get("attack_family"),
                            "attack_state": candidate.metadata.get("attack_state", {}),
                            "structured_reflection": candidate.metadata.get("structured_reflection", {}),
                            "raw_evaluator_feedback": scores.raw_evaluator_feedback,
                            "validated_evaluator_feedback": scores.validated_evaluator_feedback,
                            "validator_warnings": scores.validator_warnings,
                            "novelty_passed": candidate.metadata.get("novelty_passed"),
                            "regeneration_count": candidate.metadata.get("regeneration_count", 0),
                            "final_attacker_input": candidate.prompt,
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

    def _load_configured_tasks(self) -> list[TaskRecord]:
        if self.config.tasks.items:
            return select_tasks(self.config.tasks.items, self.config.tasks.task_ids)
        return []
