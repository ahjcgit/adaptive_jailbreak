import json

from adaptive_jailbreak.cli import build_parser, main
from adaptive_jailbreak.schemas import TrajectoryRecord


def test_cli_dry_run(repo_root, capsys):
    main(["run", "--config", str(repo_root / "experiments" / "synthetic_smoke.yaml"), "--dry-run"])
    assert "Config valid" in capsys.readouterr().out


def test_cli_keeps_read_only_output_tools(tmp_path, capsys):
    trajectory = tmp_path / "trajectory.jsonl"
    output = tmp_path / "trajectory.md"
    record = TrajectoryRecord(
        experiment_id="exp",
        run_id="run",
        task_id="task",
        iteration=0,
        attacker_model="a",
        target_model="t",
        evaluator_model_or_type="rule",
        attacker_prompt="prompt",
        target_response="response",
        evaluator_scores={"compliance_score": 1.0, "refusal_score": 0.0},
        success_label="success",
        refusal_label="non_refusal",
        attacker_reflection="reflection",
        strategy_tags=["reflection"],
        timestamp="now",
        config_hash="sha256:x",
    )
    trajectory.write_text(json.dumps(record.to_dict()) + "\n", encoding="utf-8")

    main(["summarize", str(trajectory)])
    assert '"records": 1' in capsys.readouterr().out

    main(["compare", str(trajectory), "--field", "target_model"])
    assert '"t"' in capsys.readouterr().out

    main(["export", str(trajectory), "--format", "markdown", "--output", str(output)])
    assert "**Attacker Prompt**" in output.read_text(encoding="utf-8")

    main(["replay", str(trajectory)])
    assert "prompt: prompt" in capsys.readouterr().out


def test_cli_format_command_removed():
    parser = build_parser()
    commands = set(parser._subparsers._group_actions[0].choices)
    assert "format" not in commands
    assert "evaluate" not in commands
