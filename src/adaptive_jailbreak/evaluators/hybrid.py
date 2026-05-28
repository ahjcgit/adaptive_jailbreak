from __future__ import annotations

from adaptive_jailbreak.evaluators.base import Evaluator
from adaptive_jailbreak.evaluators.rule_based import RuleBasedEvaluator
from adaptive_jailbreak.schemas import EvaluatorScores, TaskRecord, TrajectoryRecord


class HybridEvaluator(Evaluator):
    id = "hybrid"

    def __init__(self, rule_based: RuleBasedEvaluator | None = None) -> None:
        self.rule_based = rule_based or RuleBasedEvaluator()

    def score(
        self,
        task: TaskRecord,
        attacker_prompt: str,
        target_response: str,
        trajectory: list[TrajectoryRecord] | None = None,
    ) -> EvaluatorScores:
        base = self.rule_based.score(task, attacker_prompt, target_response, trajectory)
        return EvaluatorScores(
            **{**base.to_dict(), "rationale": f"Hybrid evaluator using rule-based checks. {base.rationale}"}
        )
