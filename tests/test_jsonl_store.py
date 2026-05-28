from adaptive_jailbreak.schemas import TrajectoryRecord
from adaptive_jailbreak.storage import JsonlTrajectoryStore


def sample_record(run_id="run_t_0001"):
    return TrajectoryRecord(
        experiment_id="exp",
        run_id=run_id,
        task_id="t",
        iteration=0,
        attacker_model="a",
        target_model="b",
        evaluator_model_or_type="rule",
        attacker_prompt="p",
        target_response="r",
        evaluator_scores={"refusal_score": 0},
        success_label="failure",
        refusal_label="non_refusal",
        attacker_reflection="",
        strategy_tags=[],
        timestamp="2026-01-01T00:00:00Z",
        config_hash="sha256:x",
    )


def test_jsonl_store_append_and_load(tmp_path):
    store = JsonlTrajectoryStore(tmp_path, "exp", "sha256:x")
    run_id = store.create_or_resume_run("t")
    store.append(sample_record(run_id))
    loaded = store.load_trajectory(run_id)
    assert len(loaded) == 1
    assert loaded[0].task_id == "t"
    assert store.trajectory_markdown_path.exists()
    assert "## Run `run_t_0001`" in store.trajectory_markdown_path.read_text(encoding="utf-8")
