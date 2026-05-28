from adaptive_jailbreak.config import ConfigLoader
from adaptive_jailbreak.runner import ExperimentRunner


def test_resume_does_not_duplicate_completed_iterations(repo_root, tmp_path):
    config = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml")
    config = config.__class__(
        **{
            **config.__dict__,
            "experiment": config.experiment.__class__(**{**config.experiment.__dict__, "output_dir": "outputs/test_out"}),
        }
    )
    runner = ExperimentRunner(config, project_root=tmp_path)
    first = runner.run()
    run_id = first[0].run_id
    second = runner.run(resume_run_id=run_id)
    assert second == []
    assert len(runner.store.load_trajectory(run_id)) == config.runner.max_iterations
