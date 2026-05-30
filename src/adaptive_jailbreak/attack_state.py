from __future__ import annotations

from dataclasses import asdict, dataclass, field

from adaptive_jailbreak.evaluators.feedback import EvaluatorFeedback
from adaptive_jailbreak.schemas import TrajectoryRecord


BAD_FRAGMENTS = [
    "based on the above context",
    "generate the next candidate input",
    "next_attack_family",
    "suggested_next_strategy",
]


@dataclass
class AttackState:
    prompts: list[str] = field(default_factory=list)
    target_responses: list[str] = field(default_factory=list)
    evaluator_feedback: list[dict] = field(default_factory=list)
    failed_strategies: dict[str, int] = field(default_factory=dict)
    strategy_scores: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_trajectory(cls, trajectory: list[TrajectoryRecord]) -> "AttackState":
        state = cls()
        for step in trajectory:
            state.prompts.append(step.attacker_prompt)
            state.target_responses.append(step.target_response)
            feedback_data = step.evaluator_scores.get("validated_evaluator_feedback") or step.evaluator_scores.get("feedback")
            feedback = EvaluatorFeedback.from_dict(feedback_data if isinstance(feedback_data, dict) else {})
            state.evaluator_feedback.append(feedback.to_dict())
            strategy = feedback.suggested_next_strategy
            if not feedback.success and strategy:
                state.failed_strategies[strategy] = state.failed_strategies.get(strategy, 0) + 1
            family = str(step.metadata.get("attack_family") or "unknown")
            state.strategy_scores[family] = max(state.strategy_scores.get(family, 0.0), float(step.evaluator_scores.get("attack_success_probability", 0.0) or 0.0))
        return state

    def to_dict(self) -> dict:
        return asdict(self)


def passes_basic_novelty(candidate: str, previous_prompts: list[str]) -> bool:
    candidate_lower = candidate.lower()
    if any(fragment in candidate_lower for fragment in BAD_FRAGMENTS):
        return False
    if candidate in previous_prompts:
        return False
    candidate_tokens = set(candidate_lower.split())
    for old in previous_prompts[-10:]:
        overlap = len(candidate_tokens & set(old.lower().split()))
        denom = max(1, len(candidate_tokens))
        if overlap / denom > 0.75:
            return False
    return True
