from adaptive_jailbreak.evaluators.base import Evaluator
from adaptive_jailbreak.evaluators.feedback import EvaluatorFeedback
from adaptive_jailbreak.evaluators.model import ModelEvaluator
from adaptive_jailbreak.evaluators.rule_based import RuleBasedEvaluator
from adaptive_jailbreak.evaluators.success_criteria import SuccessCriteriaRegistry
from adaptive_jailbreak.adapters import build_adapter
from adaptive_jailbreak.schemas import AuthConfig, EvaluatorConfig, ModelConfig


def build_evaluator(config: EvaluatorConfig, auth: AuthConfig | None = None) -> Evaluator:
    # "hybrid" is kept as a deprecated compatibility alias for rule-based scoring.
    if config.type in {"rule_based", "hybrid"}:
        return RuleBasedEvaluator()
    if config.type in {"model", "llm"}:
        if config.model is None:
            raise ValueError("Model evaluator requires evaluator.model")
        adapter = build_adapter(_model_config_from_evaluator(config), auth=auth)
        return ModelEvaluator(
            adapter=adapter,
            generation_config=config.generation,
            context=config.context,
            rule_based=RuleBasedEvaluator(),
        )
    raise ValueError(f"Unknown evaluator type: {config.type}")


def _model_config_from_evaluator(config: EvaluatorConfig) -> ModelConfig:
    if config.model is None:
        raise ValueError("Model evaluator requires evaluator.model")
    return ModelConfig(
        provider=config.provider,
        model=config.model,
        adapter=config.adapter or config.provider,
        backend=config.backend,
        revision=config.revision,
        torch_dtype=config.torch_dtype,
        device_map=config.device_map,
        quantization=config.quantization,
        generation=config.generation,
        context=config.context,
    )


__all__ = [
    "Evaluator",
    "EvaluatorFeedback",
    "ModelEvaluator",
    "RuleBasedEvaluator",
    "SuccessCriteriaRegistry",
    "build_evaluator",
]
