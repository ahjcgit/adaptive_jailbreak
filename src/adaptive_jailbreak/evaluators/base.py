from __future__ import annotations

from abc import ABC, abstractmethod

from adaptive_jailbreak.schemas import EvaluatorScores, TaskRecord, TrajectoryRecord


class Evaluator(ABC):
    id = "base"

    @abstractmethod
    def score(
        self,
        task: TaskRecord,
        attacker_prompt: str,
        target_response: str,
        trajectory: list[TrajectoryRecord] | None = None,
    ) -> EvaluatorScores:
        raise NotImplementedError
