from adaptive_jailbreak.analysis import ResultAnalyzer, format_trajectory_markdown
from adaptive_jailbreak.schemas import TrajectoryRecord


def test_analysis_summary():
    record = TrajectoryRecord(
        experiment_id="exp",
        run_id="run",
        task_id="task",
        iteration=0,
        attacker_model="a",
        target_model="t",
        evaluator_model_or_type="e",
        attacker_prompt="p",
        target_response="r",
        evaluator_scores={},
        success_label="success",
        refusal_label="non_refusal",
        attacker_reflection="",
        strategy_tags=["reflection"],
        timestamp="now",
        config_hash="sha256:x",
    )
    analyzer = ResultAnalyzer([record])
    assert analyzer.summarize()["success_rate"] == 1.0


def test_trajectory_markdown_formatter_includes_core_sections():
    record = TrajectoryRecord(
        experiment_id="exp",
        run_id="run",
        task_id="task",
        iteration=0,
        attacker_model="a",
        target_model="t",
        evaluator_model_or_type="e",
        attacker_prompt="prompt",
        target_response="response",
        evaluator_scores={"compliance_score": 1.0, "refusal_score": 0.0, "semantic_similarity": 0.5},
        success_label="success",
        refusal_label="non_refusal",
        attacker_reflection="reflection",
        strategy_tags=["reflection"],
        timestamp="now",
        config_hash="sha256:x",
        metadata={
            "attacker_random_seed": 123,
            "defender_random_seed": 456,
            "prompt_length": 6,
            "response_length": 8,
            "raw_response_length": 32,
            "raw_target_response": "response system: hidden continuation",
            "target_response_sanitized": True,
            "graded_response": "raw_target_response",
        },
    )
    rendered = format_trajectory_markdown([record])
    assert "## Run `run`" in rendered
    assert "- Attacker random seed: `123`" in rendered
    assert "- Defender random seed: `456`" in rendered
    assert "**Attacker Prompt**" in rendered
    assert "```text\nresponse\n```" in rendered
    assert "**Raw Target Response**" in rendered
    assert "response system: hidden continuation" in rendered
    assert "- Graded response: `raw_target_response`" in rendered
