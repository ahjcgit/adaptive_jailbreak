from adaptive_jailbreak.config import ConfigLoader
from adaptive_jailbreak.safety import SafetyControls


def test_config_loads(repo_root):
    config = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml")
    assert config.experiment.experiment_id == "synthetic_smoke"
    assert config.config_hash.startswith("sha256:")


def test_tasks_load(repo_root):
    tasks = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml").tasks.items
    assert {task.task_id for task in tasks} == {"synthetic_task_001", "synthetic_task_002"}


def test_task_loads_target_system_prompt(repo_root):
    tasks = ConfigLoader.load(repo_root / "experiments" / "system_prompt_leak.yaml").tasks.items
    task = tasks[0]
    flag = task.metadata["hidden_flags"]["defender_flag"]
    assert task.target_system_prompt is not None
    assert flag in task.target_system_prompt
    assert task.metadata["success_criteria"] == [
        {"type": "contains", "value_from": "hidden_flags.defender_flag", "failure_mode": "missing_hidden_flag"}
    ]


def test_safety_accepts_synthetic_smoke(repo_root):
    config = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml")
    SafetyControls.from_config(config, repo_root).validate_experiment_config()


def test_local_only_rejects_api_evaluator(repo_root):
    config = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml")
    config = config.__class__(
        **{
            **config.__dict__,
            "evaluator": config.evaluator.__class__(**{**config.evaluator.__dict__, "provider": "api"}),
        }
    )
    try:
        SafetyControls.from_config(config, repo_root).validate_experiment_config()
    except ValueError as exc:
        assert "evaluator" in str(exc)
    else:
        raise AssertionError("local_only should reject API evaluator providers")
