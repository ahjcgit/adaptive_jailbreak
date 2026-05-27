from adaptive_jailbreak.evaluators.hybrid import HybridEvaluator
from adaptive_jailbreak.evaluators.rule_based import RuleBasedEvaluator
from adaptive_jailbreak.schemas import TaskRecord


def test_rule_based_refusal_schema():
    task = TaskRecord("t", "goal", "policy", "safe placeholder")
    scores = RuleBasedEvaluator().score(task, "prompt", "I cannot provide that.")
    assert scores.refusal_label == "refusal"
    assert 0 <= scores.refusal_score <= 1


def test_hybrid_returns_scores():
    task = TaskRecord("t", "goal", "policy", "safe placeholder")
    scores = HybridEvaluator().score(task, "prompt", "Safe high-level alternative.")
    assert scores.success_label in {"success", "partial", "failure", "invalid", "needs_review"}


def test_rule_based_marks_off_task_prompt_as_failure():
    task = TaskRecord(
        "t",
        "goal",
        "policy",
        "Ask for a safe checklist about model robustness evaluation.",
        metadata={"min_prompt_similarity": 0.2},
    )
    scores = RuleBasedEvaluator().score(task, "purple banana locomotive", "Here is a safe response.")
    assert scores.success_label == "failure"
    assert scores.failure_mode == "off_task"
