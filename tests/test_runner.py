from adaptive_jailbreak.config import ConfigLoader
from adaptive_jailbreak.runner import ExperimentRunner, stopping_criteria_met
from adaptive_jailbreak.schemas import (
    AnalysisConfig,
    EvaluatorConfig,
    EvaluatorScores,
    ExperimentConfig,
    FrameworkConfig,
    ModelConfig,
    RunnerConfig,
    StorageConfig,
    TasksConfig,
)


def test_runner_end_to_end(repo_root, tmp_path):
    config = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml")
    config = config.__class__(
        **{
            **config.__dict__,
            "experiment": config.experiment.__class__(**{**config.experiment.__dict__, "output_dir": "outputs/test_out"}),
        }
    )
    runner = ExperimentRunner(config, project_root=tmp_path)
    records = runner.run()
    assert records
    assert runner.store.trajectory_path.exists()


def test_runner_rejects_empty_task_selection(repo_root, tmp_path):
    config = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml")
    config = config.__class__(
        **{
            **config.__dict__,
            "experiment": config.experiment.__class__(**{**config.experiment.__dict__, "output_dir": "outputs/test_out"}),
            "tasks": config.tasks.__class__(
                **{
                    **config.tasks.__dict__,
                    "task_ids": ["missing_task"],
                }
            ),
        }
    )
    runner = ExperimentRunner(config, project_root=tmp_path)
    try:
        runner.run()
    except ValueError as exc:
        assert "No tasks matched" in str(exc)
    else:
        raise AssertionError("runner should reject empty task selections")


def test_stopping_criteria_does_not_treat_non_refusal_as_success(repo_root):
    config = FrameworkConfig(
        experiment=ExperimentConfig(experiment_id="test"),
        attacker=ModelConfig(provider="dummy", model="dummy-attacker", adapter="dummy", strategy="reflection"),
        target=ModelConfig(provider="dummy", model="dummy-target", adapter="dummy"),
        evaluator=EvaluatorConfig(type="rule_based"),
        tasks=TasksConfig(),
        runner=RunnerConfig(
            stopping=RunnerConfig.from_dict({"stopping": {"stop_on_success": True}}).stopping,
        ),
        storage=StorageConfig(),
        analysis=AnalysisConfig(),
        config_hash="sha256:test",
    )
    scores = EvaluatorScores(
        refusal_score=0.0,
        compliance_score=1.0,
        semantic_similarity=0.0,
        attack_success_probability=0.0,
        success_label="failure",
        refusal_label="non_refusal",
        failure_mode="missing_hidden_flag",
    )
    assert stopping_criteria_met(config, scores, []) is False
