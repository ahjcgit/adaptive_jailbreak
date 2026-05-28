from adaptive_jailbreak.evaluators.base import Evaluator
from adaptive_jailbreak.evaluators.hybrid import HybridEvaluator
from adaptive_jailbreak.evaluators.rule_based import RuleBasedEvaluator
from adaptive_jailbreak.evaluators.success_criteria import SuccessCriteriaRegistry
from adaptive_jailbreak.schemas import EvaluatorConfig


def build_evaluator(config: EvaluatorConfig) -> Evaluator:
    if config.type == "rule_based":
        return RuleBasedEvaluator()
    if config.type == "hybrid":
        return HybridEvaluator()
    raise ValueError(f"Unknown evaluator type: {config.type}")


__all__ = [
    "Evaluator",
    "HybridEvaluator",
    "RuleBasedEvaluator",
    "SuccessCriteriaRegistry",
    "build_evaluator",
]
