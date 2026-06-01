#!/usr/bin/env bash
set -euo pipefail

# Edit these two lists before leaving.
CONFIGS=(
  "experiments/erotic_llama.yaml"
  "experiments/bomb_2_llama.yaml"
  "experiments/system_prompt_3_llama.yaml"
)

SEEDS=(
  500
  501
  502
)

# Optional:
#   DRY_RUN=1 bash scripts/run_many.sh
#   BATCH_NAME=my_batch bash scripts/run_many.sh
DRY_RUN="${DRY_RUN:-0}"
BATCH_NAME="${BATCH_NAME:-batch_$(date +%Y%m%d_%H%M%S)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_ROOT="$ROOT/outputs/$BATCH_NAME"

mkdir -p "$OUT_ROOT/_configs" "$OUT_ROOT/_logs"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

for config in "${CONFIGS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    base="$(basename "$config" .yaml)"
    run_name="${base}_seed_${seed}"
    generated_config="$OUT_ROOT/_configs/${run_name}.yaml"
    output_dir="outputs/${BATCH_NAME}/${run_name}"
    log_file="$OUT_ROOT/_logs/${run_name}.log"

    "$PYTHON_BIN" - "$ROOT/$config" "$generated_config" "$seed" "$output_dir" <<'PY'
import sys
from pathlib import Path

import yaml

source = Path(sys.argv[1])
target = Path(sys.argv[2])
seed = int(sys.argv[3])
output_dir = sys.argv[4]

data = yaml.safe_load(source.read_text(encoding="utf-8"))
data["seed"] = seed
data["experiment"]["output_dir"] = output_dir
auth = data.setdefault("auth", {})
token_path = auth.get("huggingface_token_path")
if token_path:
    resolved_token_path = (source.parent / token_path).resolve()
    auth["huggingface_token_path"] = str(resolved_token_path)

target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY

    cmd=("$PYTHON_BIN" -m adaptive_jailbreak.cli run --config "$generated_config")
    if [[ "$DRY_RUN" == "1" ]]; then
      cmd+=(--dry-run)
    fi

    echo "============================================================"
    echo "Running $config with seed $seed"
    echo "Output: $output_dir"
    echo "Log:    $log_file"
    echo "============================================================"

    "${cmd[@]}" 2>&1 | tee "$log_file"
  done
done

echo "All runs finished. Batch output: outputs/$BATCH_NAME"
