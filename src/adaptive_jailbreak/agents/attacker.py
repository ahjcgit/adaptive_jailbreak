from __future__ import annotations

from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.schemas import AttackCandidate, GenerationConfig, TaskRecord, TrajectoryRecord
from adaptive_jailbreak.strategies.base import AttackStrategy


class AttackerAgent:
    def __init__(self, adapter: ModelAdapter, strategy: AttackStrategy, generation_config: GenerationConfig) -> None:
        self.adapter = adapter
        self.strategy = strategy
        self.generation_config = generation_config

    def initial_prompt(self, task: TaskRecord, context: dict | None = None) -> AttackCandidate:
        return self.strategy.initial_prompt(task, self.adapter, self.generation_config, context or {})

    def next_prompt(
        self,
        task: TaskRecord,
        trajectory: list[TrajectoryRecord],
        context: dict | None = None,
    ) -> AttackCandidate:
        return self.strategy.next_prompt(task, trajectory, self.adapter, self.generation_config, context or {})
