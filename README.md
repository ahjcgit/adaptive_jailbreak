# Adaptive Jailbreak Experiment Harness

Adaptive Jailbreak is a small research harness for controlled, iterative model-safety experiments. It is designed around configurable attacker-target-evaluator runs: swap the attacker model, target model, evaluator, task family, success criteria, seeds, and output directory from YAML without rewriting the experiment loop.

The harness treats model text as inert data. It sends configured prompts to configured adapters, scores the returned text, and writes local trajectories. It does not execute generated text or delegate generated text to tools.

## What This Repo Is For

- Compare different model families under the same task definitions.
- Test different task families with the same adaptive loop.
- Run seeded batches for reproducible, multi-run comparisons.
- Inspect every iteration through machine-readable JSONL and readable Markdown trajectories.
- Study not only whether a run succeeds, but why it fails: refusal, off-task drift, missing success criteria, prompt contamination, or weak attacker strategy.

The current project direction is not "one hard-coded jailbreak demo." The main design goal is a reusable testing harness where experiments are described by config.

## Repository Layout

```text
experiments/                 YAML experiment configs
scripts/run_many.sh          Batch runner for configs x seeds
src/adaptive_jailbreak/      Harness package
tests/                       Unit tests
docs/                        Analysis notes and presentation support
outputs/                     Local generated runs, ignored by git except .gitkeep
```

Core modules:

- `adapters/`: dummy and local Hugging Face model adapters
- `agents/`: attacker and target roles
- `strategies/`: iterative attacker strategy logic
- `evaluators/`: rule-based and model-assisted scoring
- `runner.py`: attacker-target-evaluator orchestration
- `storage/`: JSONL, Markdown trajectory, and manifest output
- `analysis/`: trajectory summaries and export formatting

## Install

Create an environment with Python 3.10 or newer, then install the package:

```bash
pip install -e .
```

For development and tests:

```bash
pip install -e .[dev]
pytest
```

For local Hugging Face model runs:

```bash
pip install -e .[local]
```

## Quick Start

Run a deterministic smoke test with dummy adapters:

```bash
python -m adaptive_jailbreak.cli run --config experiments/synthetic_smoke.yaml
```

Summarize and replay the output:

```bash
python -m adaptive_jailbreak.cli summarize outputs/synthetic_smoke/trajectory.jsonl
python -m adaptive_jailbreak.cli replay outputs/synthetic_smoke/trajectory.jsonl
```

Each run writes:

- `trajectory.jsonl`: machine-readable iteration records
- `trajectory.md`: readable run log
- `manifest.json`: run metadata and status

## Experiment Configs

Each experiment is a single YAML file under `experiments/`. A config contains:

- experiment metadata and output directory
- attacker model settings
- target model settings
- evaluator settings
- task allowlist and inline task definitions
- runner settings such as max iterations and stopping behavior
- storage settings

Start from:

- `experiments/example.yaml`: editable template
- `experiments/synthetic_smoke.yaml`: dummy-adapter plumbing check
- `experiments/bomb_2.yaml`: refusal benchmark config
- `experiments/erotic.yaml`: adult-only explicit-content refusal benchmark config
- `experiments/system_prompt_3.yaml`: protected flag / prompt-leak benchmark config
- `experiments/*_llama.yaml`: Llama variants of the same current task families

To create a new experiment, copy `experiments/example.yaml` and edit:

```yaml
experiment:
  experiment_id: my_experiment
  output_dir: outputs/my_experiment

seed: 123

attacker:
  provider: dummy
  model: dummy-attacker
  adapter: dummy
  strategy: reflection

target:
  provider: dummy
  model: dummy-target
  adapter: dummy

evaluator:
  type: rule_based
  provider: dummy

tasks:
  task_ids:
    - example_task_001
  allowed_task_ids:
    - example_task_001
  synthetic_only: true
  items:
    - task_id: example_task_001
      goal: What this task measures.
      policy_goal: example_policy_area
      prompt: "Tell the attacker what target-facing input to generate."
      synthetic: true
      success_criteria:
        - type: contains
          value: "expected phrase"
          failure_mode: missing_expected_phrase
```

Supported rule-based success criteria include:

- `contains`
- `not_contains`
- `regex`

Criteria can use `value`, `values`, or `value_from` to reference task metadata.

## Swapping Models

Model roles are independent. You can swap the attacker, target, and evaluator separately in YAML.

Dummy adapter example:

```yaml
attacker:
  provider: dummy
  model: dummy-attacker
  adapter: dummy
```

Local Hugging Face adapter example:

```yaml
target:
  provider: local
  model: meta-llama/Llama-3.1-8B-Instruct
  adapter: local
  device_map: auto
  torch_dtype: float16
  quantization:
    bits: 4
    compute_dtype: float16
```

The top-level `seed` field is propagated to attacker, target, and evaluator generation configs unless a role overrides its own seed.

For gated Hugging Face models, either export `HF_TOKEN` or copy:

```text
secrets/huggingface.yaml.example
```

to:

```text
secrets/huggingface.yaml
```

and add your token there. The real token file is ignored by git.

## Running Batches

Run the default Llama config set across seeds 500, 501, and 502:

```bash
bash scripts/run_many.sh
```

Dry-run the generated configs:

```bash
DRY_RUN=1 bash scripts/run_many.sh
```

Choose configs and seeds without editing the script:

```bash
CONFIG_LIST="experiments/bomb_2.yaml experiments/system_prompt_3.yaml" \
SEED_LIST="500 501 502" \
BATCH_NAME=my_qwen_batch \
bash scripts/run_many.sh
```

Batch outputs are written under:

```text
outputs/<batch_name>/
```

with generated per-run configs in `_configs/` and command logs in `_logs/`.

## CLI Reference

```bash
python -m adaptive_jailbreak.cli run --config experiments/synthetic_smoke.yaml
python -m adaptive_jailbreak.cli run --config experiments/synthetic_smoke.yaml --dry-run
python -m adaptive_jailbreak.cli resume --config experiments/synthetic_smoke.yaml --run-id <run_id>
python -m adaptive_jailbreak.cli summarize outputs/synthetic_smoke/trajectory.jsonl
python -m adaptive_jailbreak.cli compare outputs/synthetic_smoke/trajectory.jsonl --field target_model
python -m adaptive_jailbreak.cli export outputs/synthetic_smoke/trajectory.jsonl --format markdown --output trajectory.md
python -m adaptive_jailbreak.cli replay outputs/synthetic_smoke/trajectory.jsonl
```

If installed as a package, the console script is also available:

```bash
adaptive-jailbreak run --config experiments/synthetic_smoke.yaml
```

## Safety Controls

- Keep generated model text inert.
- Keep tasks synthetic unless intentionally changing `tasks.synthetic_only`.
- Keep `tasks.allowed_task_ids` scoped to the tasks defined in the same experiment file.
- Set `experiment.local_only: true` for local-only runs.
- Do not execute target outputs or attacker prompts.
- Do not commit real secrets.

## Outputs And Git

Generated runs under `outputs/` are ignored by git:

```gitignore
outputs/*
!outputs/.gitkeep
```

This keeps the repository small and prevents accidental publication of bulky or sensitive run artifacts. If a trajectory is useful for a report, copy a selected, redacted example into `docs/` and commit that document instead of committing the entire output tree.

## Presentation And Analysis Notes

Current project writeups live under `docs/`, including:

- `docs/presentation_key_points.md`
- `docs/presentation_output_log_analysis.md`
- `docs/experiment_framework_changes.md`
- `docs/llama_experiment_plan.md`

Presentation visuals generated from structured logs live under `docs/figures/`.

## Development Notes

Run the test suite before changing core behavior:

```bash
pytest
```

The most important design constraint is preserving interpretability: a run should make it clear which prompt was sent, how the target responded, how the evaluator scored it, and why the next iteration changed.
