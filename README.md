# Adaptive Jailbreak Research Framework

This repository contains a research-oriented experiment framework for studying iterative adversarial prompting, refusal-boundary behavior, prompt evolution, transferability, and model robustness under controlled conditions.

The framework treats model text as inert data. It never executes generated instructions, opens generated URLs, or delegates generated text to tools. The only intended side effects are explicitly configured model calls and local logging under configured output directories.

## Quick Start

```bash
python -m adaptive_jailbreak.cli run --config configs/local_dummy.yaml
python -m adaptive_jailbreak.cli summarize outputs/pair_like_synthetic_v1/trajectory.jsonl
python -m adaptive_jailbreak.cli replay outputs/pair_like_synthetic_v1/trajectory.jsonl
```

The default configs use deterministic dummy adapters and synthetic tasks. They are suitable for tests, CLI validation, and development without network calls.

## Local Model Smoke Test

Install optional local-model dependencies, then run a two-model smoke test:

```bash
pip install -e .[local]
python scripts/run_local_smoke.py
```

By default the script uses `sshleifer/tiny-gpt2` as the attacker model and `hf-internal-testing/tiny-random-gpt2` as the target model. Override them with:

```bash
python scripts/run_local_smoke.py --attacker-model sshleifer/tiny-gpt2 --target-model distilgpt2 --max-iterations 2
```

Use `--local-files-only` if both model IDs are already cached or are local filesystem paths and you want to avoid Hugging Face downloads.

The script writes a generated config, JSONL trajectory, manifest, and Markdown report under `outputs/<experiment_id>/`.

Format a trajectory JSONL file into a readable per-iteration Markdown view:

```bash
python scripts/format_trajectory.py outputs/<experiment_id>/trajectory.jsonl
```

Or through the CLI:

```bash
pip install -e .
python -m adaptive_jailbreak.cli format outputs/<experiment_id>/trajectory.jsonl --output outputs/<experiment_id>/trajectory.md
```

## Functional Benchmark Prompts

For more meaningful local checks, use `tasks/functional_benchmark.yaml`. These prompts are benign synthetic probes for:

- Safe summary compliance
- Refusal-boundary redirection
- Safe substitute checklist generation
- Prompt drift across attacker iterations

Run them with instruction-capable local models by overriding the default tiny placeholders:

```bash
python scripts/run_local_smoke.py --config configs/local_functional_transformers.yaml --attacker-model Qwen/Qwen2.5-0.5B-Instruct --target-model Qwen/Qwen2.5-0.5B-Instruct --max-iterations 3 --max-new-tokens 128
```

To run just one functional task, add `--task-id functional_safe_summary`. If you omit `--task-id`, the script uses the task list from the config; `configs/local_functional_transformers.yaml` runs all functional benchmark tasks.

Tiny random models are useful only for checking plumbing. Meaningful scores require models that can follow instructions.

## Safety Controls

- Use synthetic benchmark tasks by default.
- Use task allowlists before running experiments.
- Set `experiment.local_only: true` to reject API adapters.
- Never execute target outputs or attacker prompts.
- Keep prompts, responses, evaluator scores, and config hashes in local logs for auditability.
