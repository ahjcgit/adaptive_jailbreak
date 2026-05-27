from adaptive_jailbreak.config import ConfigLoader
from adaptive_jailbreak.runner import ExperimentRunner


def test_runner_end_to_end(repo_root, tmp_path):
    config = ConfigLoader.load(repo_root / "configs" / "local_dummy.yaml")
    config = config.__class__(
        **{
            **config.__dict__,
            "experiment": config.experiment.__class__(
                **{**config.experiment.__dict__, "output_dir": "outputs/test_out", "log_dir": "logs"}
            ),
            "tasks": config.tasks.__class__(
                **{
                    **config.tasks.__dict__,
                    "task_set_path": str(repo_root / "tasks" / "synthetic_benchmark.yaml"),
                    "allowlist_path": str(repo_root / "tasks" / "allowlist.yaml"),
                }
            ),
        }
    )
    runner = ExperimentRunner(config, project_root=tmp_path)
    records = runner.run()
    assert records
    assert runner.store.trajectory_path.exists()


def test_runner_rejects_empty_task_selection(repo_root, tmp_path):
    config = ConfigLoader.load(repo_root / "configs" / "local_dummy.yaml")
    config = config.__class__(
        **{
            **config.__dict__,
            "experiment": config.experiment.__class__(
                **{**config.experiment.__dict__, "output_dir": "outputs/test_out", "log_dir": "logs"}
            ),
            "tasks": config.tasks.__class__(
                **{
                    **config.tasks.__dict__,
                    "task_set_path": str(repo_root / "tasks" / "synthetic_benchmark.yaml"),
                    "allowlist_path": str(repo_root / "tasks" / "allowlist.yaml"),
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
