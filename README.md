# Adaptive Jailbreak Experiment Harness

This repository contains a small experiment harness for controlled iterative prompting experiments. Model text is treated as inert data: the harness sends configured prompts to configured adapters, scores the text response, and writes local output. It never executes generated text or delegates it to tools.

## Quick Start

Run the deterministic smoke experiment:

```bash
python -m adaptive_jailbreak.cli run --config experiments/synthetic_smoke.yaml
python -m adaptive_jailbreak.cli summarize outputs/synthetic_smoke/trajectory.jsonl
python -m adaptive_jailbreak.cli replay outputs/synthetic_smoke/trajectory.jsonl
```

Each experiment run writes `trajectory.jsonl`, `trajectory.md`, and `manifest.json` under the configured output directory. The JSONL file is the machine-readable record stream; the Markdown file is regenerated automatically from it after each appended iteration.

## Single-File Experiments

An experiment is now one YAML file under `experiments/`. The config includes model settings, runner settings, the task allowlist, and task definitions inline.

- `experiments/example.yaml`: editable template for new experiments.
- `experiments/synthetic_smoke.yaml`: dummy-adapter plumbing check.
- `experiments/system_prompt_leak.yaml`: local Qwen system-prompt leak benchmark.

To create a new experiment, copy `experiments/example.yaml`, change `experiment.experiment_id`, `experiment.output_dir`, model settings, and the tasks under `tasks.items`.

## Local Models

Install optional local-model dependencies before using `adapter: local`:

```bash
pip install -e .[local]
python -m adaptive_jailbreak.cli run --config experiments/system_prompt_leak.yaml
```

## Safety Controls

- Keep tasks synthetic unless an experiment intentionally changes `tasks.synthetic_only`.
- Keep `tasks.allowed_task_ids` limited to the tasks in the same experiment file.
- Set `experiment.local_only: true` to reject API adapters.
- Never execute target outputs or attacker prompts.
