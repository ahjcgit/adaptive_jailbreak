from adaptive_jailbreak.config import ConfigLoader, load_tasks
from adaptive_jailbreak.safety import SafetyControls


def test_config_loads(repo_root):
    config = ConfigLoader.load(repo_root / "configs" / "local_dummy.yaml")
    assert config.experiment.experiment_id == "pair_like_synthetic_v1"
    assert config.config_hash.startswith("sha256:")


def test_tasks_load(repo_root):
    tasks = load_tasks(repo_root / "tasks" / "synthetic_benchmark.yaml")
    assert {task.task_id for task in tasks} == {"synthetic_task_001", "synthetic_task_002"}


def test_safety_accepts_local_dummy(repo_root):
    config = ConfigLoader.load(repo_root / "configs" / "local_dummy.yaml")
    SafetyControls.from_config(config, repo_root).validate_experiment_config()


def test_local_only_rejects_api_evaluator(repo_root):
    config = ConfigLoader.load(repo_root / "configs" / "local_dummy.yaml")
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
