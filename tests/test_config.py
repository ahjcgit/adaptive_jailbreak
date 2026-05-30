from adaptive_jailbreak.config import ConfigLoader
from adaptive_jailbreak.safety import SafetyControls


def test_config_loads(repo_root):
    config = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml")
    assert config.experiment.experiment_id == "synthetic_smoke"
    assert config.config_hash.startswith("sha256:")


def test_config_loads_huggingface_token_file(repo_root, tmp_path):
    token_path = tmp_path / "hf.yaml"
    token_path.write_text('token: "hf_test_token"\n', encoding="utf-8")
    config_path = tmp_path / "config.yaml"
    template = (repo_root / "experiments" / "synthetic_smoke.yaml").read_text(encoding="utf-8")
    config_path.write_text(
        template.replace(
            "experiment:\n",
            f"auth:\n  huggingface_token_path: {token_path}\n\nexperiment:\n",
            1,
        ),
        encoding="utf-8",
    )
    config = ConfigLoader.load(config_path)
    assert config.auth.huggingface_token == "hf_test_token"


def test_tasks_load(repo_root):
    tasks = ConfigLoader.load(repo_root / "experiments" / "synthetic_smoke.yaml").tasks.items
    assert {task.task_id for task in tasks} == {"synthetic_task_001", "synthetic_task_002"}


def test_task_loads_target_system_prompt(repo_root):
    tasks = ConfigLoader.load(repo_root / "experiments" / "system_prompt_leak.yaml").tasks.items
    task = tasks[0]
    flag = task.metadata["hidden_flags"]["defender_flag"]
    assert task.target_system_prompt is not None
    assert flag in task.target_system_prompt
    assert task.success_criteria == [
        {"type": "contains", "value_from": "hidden_flags.defender_flag", "failure_mode": "missing_hidden_flag"}
    ]
    assert "success_criteria" not in task.metadata
    loaded = ConfigLoader.load(repo_root / "experiments" / "system_prompt_leak.yaml")
    assert loaded.target.quantization == {"bits": 4, "compute_dtype": "float16"}
    assert loaded.target.device_map == "auto"


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


def test_config_loads_model_evaluator_fields(repo_root, tmp_path):
    config_path = tmp_path / "config.yaml"
    template = (repo_root / "experiments" / "synthetic_smoke.yaml").read_text(encoding="utf-8")
    config_path.write_text(
        template.replace(
            "evaluator:\n  type: rule_based\n  provider: dummy\n",
            "\n".join(
                [
                    "evaluator:",
                    "  type: model",
                    "  provider: local",
                    "  model: org/evaluator",
                    "  adapter: local",
                    "  device_map: auto",
                    "  torch_dtype: float16",
                    "  quantization:",
                    "    bits: 4",
                    "  generation:",
                    "    temperature: 0.1",
                    "    max_tokens: 256",
                    "  context:",
                    "    trust_model_labels: false",
                    "",
                ]
            ),
            1,
        ),
        encoding="utf-8",
    )

    config = ConfigLoader.load(config_path)

    assert config.evaluator.type == "model"
    assert config.evaluator.adapter == "local"
    assert config.evaluator.device_map == "auto"
    assert config.evaluator.quantization == {"bits": 4}
    assert config.evaluator.context["trust_model_labels"] is False


def test_top_level_seed_applies_to_all_model_generation_configs(repo_root, tmp_path):
    config_path = tmp_path / "config.yaml"
    template = (repo_root / "experiments" / "synthetic_smoke.yaml").read_text(encoding="utf-8")
    config_path.write_text(
        template.replace("seed: 123\n", "seed: 777\n", 1),
        encoding="utf-8",
    )

    config = ConfigLoader.load(config_path)

    assert config.attacker.generation.seed == 777
    assert config.target.generation.seed == 777
    assert config.evaluator.generation.seed == 777


def test_experiment_configs_use_reduced_inline_schema(repo_root):
    for path in (repo_root / "experiments").glob("*.yaml"):
        raw = path.read_text(encoding="utf-8")
        assert "random_seed:" not in raw
        assert "    seed:" not in raw
        assert "log_dir:" not in raw
        assert "config_version:" not in raw
        assert "task_set_path:" not in raw
        assert "allowlist_path:" not in raw
        assert "type: hybrid" not in raw
        ConfigLoader.load(path)
