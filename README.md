# Adaptive Injection

This repository contains a minimal experiment harness for an adaptive red-teaming pipeline. It is intentionally split into:
- runnable components that exercise the experiment loop end to end,
- placeholder modules for the parts you must connect to your own target model or dataset,
- explicit `TODO(user)` markers where project-specific implementation is still required.

## What is implemented
- Seed prompt loading from JSONL.
- Prompt mutation operators.
- Adaptive search policies: `random` and `bandit`.
- Defense pipeline toggles.
- Local heuristic judge.
- Experiment runner with JSONL, CSV, and summary metrics output.
- Runnable mock target for smoke tests.
- Optional OpenAI-compatible target adapter scaffold.

## What is intentionally a placeholder
- Real jailbreak seed traces and richer prompt families.
- A strong judge model with your actual rubric.
- A real OSS local-model adapter if you want `vllm` or `transformers`.
- A real hosted-model adapter if your API format differs from the included OpenAI-compatible scaffold.
- Multi-turn state logic beyond the basic mutation-chain placeholder.
- Publication-safe redaction and advanced plotting.

## Project layout
```text
src/adaptive_injection/
  analysis/
  datasets/
  defenses/
  generation/
  judges/
  policies/
  runners/
  targets/
data/
  benign/
  seeds/
artifacts/
  logs/
  metrics/
```

## Setup
Create a virtual environment. If editable install works in your environment, you can use it, but the no-network-safe path is to run with `PYTHONPATH=src`.

```bash
python -m venv .venv
source .venv/bin/activate
```

Optional editable install:

```bash
pip install -e . --no-build-isolation
```

## Smoke test
Run the full pipeline with the mock target.

```bash
PYTHONPATH=src python -m adaptive_injection --target mock --policy bandit --budget 12
```

This writes outputs to:
- `artifacts/logs/<run_id>.jsonl`
- `artifacts/logs/<run_id>.csv`
- `artifacts/metrics/<run_id>_summary.json`

## Example experiment commands
Baseline on the mock target:

```bash
PYTHONPATH=src python -m adaptive_injection \
  --target mock \
  --policy random \
  --budget 20 \
  --run-id baseline_random
```

Adaptive search on the mock target:

```bash
PYTHONPATH=src python -m adaptive_injection \
  --target mock \
  --policy bandit \
  --budget 20 \
  --run-id adaptive_bandit
```

Defense ablation on the mock target:

```bash
PYTHONPATH=src python -m adaptive_injection \
  --target mock \
  --policy bandit \
  --budget 20 \
  --system-hardening \
  --input-moderation \
  --self-critique \
  --run-id defended_bandit
```

## Running against a real target
The repository includes `src/adaptive_injection/targets/openai_compatible.py` as a scaffold.

Set environment variables:

```bash
export OPENAI_COMPAT_BASE_URL="https://your-endpoint.example/v1"
export OPENAI_COMPAT_API_KEY="your-key-if-needed"
export OPENAI_COMPAT_MODEL="your-model-name"
```

Then run:

```bash
PYTHONPATH=src python -m adaptive_injection \
  --target openai-compatible \
  --policy bandit \
  --budget 25 \
  --run-id real_target_bandit
```

## What you still need to implement

### 1. Real seed traces
Replace `data/seeds/sample_seeds.jsonl` with your actual seed set.

Expected schema per line:
```json
{"seed_id":"...","family":"...","prompt":"...","tags":["..."]}
```

You should add:
- public jailbreak seeds grouped by family,
- your own abstract prompt templates,
- enough diversity to test transfer and adaptation.

### 2. Strong judge logic
Current file: `src/adaptive_injection/judges/rubric.py`

You need to replace the heuristic judge with either:
- a separate judge model call that emits structured JSON, or
- a more reliable local rubric implementation.

The current output contract is `JudgeResult` in `src/adaptive_injection/models.py`.

### 3. Real target adapters
Current files:
- `src/adaptive_injection/targets/openai_compatible.py`
- `src/adaptive_injection/targets/mock_target.py`

You likely need to add one or both:
- `VllmTargetAdapter`
- `TransformersTargetAdapter`

Each adapter must implement:
```python
TargetAdapter.generate(prompt: str, system_prompt: str | None) -> TargetResponse
```

### 4. Stronger adaptive policy
Current files:
- `src/adaptive_injection/policies/random_policy.py`
- `src/adaptive_injection/policies/bandit_policy.py`

You may want to add:
- evolutionary search,
- beam search,
- multi-turn follow-up planning conditioned on prior responses.

### 5. Better multi-turn traces
The current runner mutates prompts across steps but does not store a full conversational transcript.

You should extend:
- `PromptCandidate`
- `TrialRecord`
- `ExperimentRunner`

so each state can include prior assistant outputs and explicit follow-up turns.

## Where to plug in missing pieces
Search the codebase for:
- `TODO(user)`

Those markers identify the places where this scaffold stops and your project-specific implementation begins.

## Suggested real experiment sequence
1. Run the smoke test locally with `--target mock`.
2. Replace the seed dataset with your real seed set.
3. Plug in your real target adapter.
4. Replace the heuristic judge.
5. Run static vs adaptive experiments.
6. Run defense ablations.
7. Export summaries from `artifacts/metrics/` for plots.

## Notes
- This implementation is designed to be safe to run locally without requiring access to an external model.
- The mock target is only for pipeline validation, not for scientific results.
- Keep raw prompt/output traces local if they contain sensitive or high-risk content.
