from adaptive_jailbreak.adapters import build_adapter
from adaptive_jailbreak.evaluators.base import Evaluator
from adaptive_jailbreak.evaluators.hybrid import HybridEvaluator
from adaptive_jailbreak.evaluators.llm_judge import LLMJudgeEvaluator
from adaptive_jailbreak.evaluators.rule_based import RuleBasedEvaluator
from adaptive_jailbreak.schemas import EvaluatorConfig


def build_evaluator(config: EvaluatorConfig) -> Evaluator:
    if config.type == "rule_based":
        return RuleBasedEvaluator()
    if config.type == "llm_judge":
        adapter = None
        if config.provider and config.provider != "rule":
            adapter = build_adapter(config.provider if config.provider in {"dummy", "local", "api"} else "api", config.model or "judge", config.provider)
        return LLMJudgeEvaluator(adapter=adapter, generation_config=config.generation)
    if config.type == "hybrid":
        judge = None
        if config.provider and config.provider != "dummy":
            adapter = build_adapter(config.provider if config.provider in {"local", "api"} else "api", config.model or "judge", config.provider)
            judge = LLMJudgeEvaluator(adapter=adapter, generation_config=config.generation)
        return HybridEvaluator(judge=judge)
    raise ValueError(f"Unknown evaluator type: {config.type}")


__all__ = ["Evaluator", "HybridEvaluator", "LLMJudgeEvaluator", "RuleBasedEvaluator", "build_evaluator"]
