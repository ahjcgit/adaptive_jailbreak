from adaptive_jailbreak.cli import main


def test_cli_dry_run(repo_root, capsys):
    main(["run", "--config", str(repo_root / "experiments" / "synthetic_smoke.yaml"), "--dry-run"])
    assert "Config valid" in capsys.readouterr().out
