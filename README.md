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

To create a new experiment, copy `experiments/example.yaml`, change `experiment.experiment_id`, `experiment.output_dir`, model settings, and the tasks under `tasks.items`. Tasks are defined inline; external task files and external allowlists are not part of the current pipeline.

Each task can define its own success criteria directly in the experiment YAML:

```yaml
tasks:
  items:
    - task_id: example_task_001
      prompt: "Tell the attacker what input to generate."
      success_criteria:
        - type: contains
          value: "expected phrase"
          failure_mode: missing_expected_phrase
```

Supported rule-based criteria include `contains`, `not_contains`, and `regex`. Criteria may use `value`, `values`, or `value_from` to reference a path under the task's `metadata`.

## Local Models

Install optional local-model dependencies before using `adapter: local`:

```bash
pip install -e .[local]
CUDA_VISIBLE_DEVICES=0 python -m adaptive_jailbreak.cli run --config experiments/system_prompt_leak.yaml
```

Use `nvidia-smi` to confirm the RTX 4080 index first. In your current setup the traceback shows the GTX 1070 Ti as `GPU1`, so `CUDA_VISIBLE_DEVICES=0` should expose only the RTX 4080 to PyTorch and prevent Accelerate from placing any model layers on the unsupported GTX 1070 Ti.

For gated Hugging Face models, either export `HF_TOKEN` or copy
`secrets/huggingface.yaml.example` to `secrets/huggingface.yaml` and paste
your token there. The real `secrets/huggingface.yaml` file is ignored by git.

Quantized Hugging Face loads are configured per model:

```yaml
target:
  provider: local
  model: Qwen/Qwen2.5-7B-Instruct
  adapter: local
  device_map: auto
  torch_dtype: float16
  quantization:
    bits: 4
    compute_dtype: float16
```

Use `bits: 8` for 8-bit loading, or leave `bits:` empty for an unquantized load.

## Safety Controls

- Keep tasks synthetic unless an experiment intentionally changes `tasks.synthetic_only`.
- Keep `tasks.allowed_task_ids` limited to the tasks in the same experiment file.
- Set `experiment.local_only: true` to reject API adapters.
- Never execute target outputs or attacker prompts.
