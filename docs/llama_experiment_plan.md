# Llama Experiment Plan

## Model Choice

Use `meta-llama/Llama-3.1-8B-Instruct` as the Llama-family comparison model.

Why this model:

- It is close in scale to `Qwen/Qwen2.5-7B-Instruct`.
- It is instruction-tuned and supports chat-style prompting.
- It is widely used as an 8B-class baseline, making results easier to interpret.
- The current local adapter already uses Hugging Face chat templates when available, so no custom prompt formatting should be necessary.

Source note: the Hugging Face model card lists `meta-llama/Llama-3.1-8B-Instruct`, and public docs note it is a gated Meta Llama model requiring Hugging Face access approval.

## New Configs

The Qwen configs were copied into Llama variants:

- `experiments/bomb_2_llama.yaml`
- `experiments/erotic_llama.yaml`
- `experiments/system_prompt_3_llama.yaml`

Each config uses Llama for:

- attacker
- target
- evaluator

This keeps the experiment internally matched, similar to the current Qwen setup.

## Expected Impact

The Llama runs should help separate framework behavior from model-family behavior.

Watch for:

- Whether Llama follows the `<candidate>...</candidate>` output contract more or less reliably than Qwen.
- Whether Llama attacker prompts are more creative or more repetitive.
- Whether Llama target behavior is more refusal-heavy, more compliant, or more prone to prompt-leak failures.
- Whether Llama evaluator feedback is more or less aligned with deterministic success criteria.

## Structural Requirements

No code changes are expected before trying the run.

Structural caveats:

- `meta-llama/Llama-3.1-8B-Instruct` is gated on Hugging Face. The `HF_TOKEN` used by the repo must have accepted access to the model.
- The current adapter uses `AutoTokenizer.apply_chat_template` when available. Llama 3.1 Instruct should be compatible with that path.
- The configs keep the same 4-bit quantization settings as Qwen. If loading fails, the likely fixes are:
  - confirm Hugging Face access first
  - try `torch_dtype: bfloat16` if the local GPU supports it
  - try `quantization.bits: 8` or no quantization if bitsandbytes has trouble
  - lower attacker `max_tokens` if memory becomes tight

## Suggested Batch

To compare directly against the current Qwen experiments, run:

```bash
CONFIGS=(
  "experiments/bomb_2_llama.yaml"
  "experiments/erotic_llama.yaml"
  "experiments/system_prompt_3_llama.yaml"
)
```

with the same seeds:

```bash
SEEDS=(
  500
  501
  502
)
```

The existing `scripts/run_many.sh` currently has its config list hardcoded, so either temporarily edit that list or make a copy of the script for the Llama batch.

## Validation Done

All three new configs pass CLI dry-run validation:

- `experiments/bomb_2_llama.yaml`
- `experiments/erotic_llama.yaml`
- `experiments/system_prompt_3_llama.yaml`

Dry-run validation checks schema and safety configuration, but it does not download or load the gated model weights.
