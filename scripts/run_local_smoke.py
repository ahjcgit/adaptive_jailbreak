from __future__ import annotations

import argparse
import os
import sys
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from adaptive_jailbreak.analysis import ResultAnalyzer, markdown_report
from adaptive_jailbreak.config import ConfigLoader
from adaptive_jailbreak.runner import ExperimentRunner
from adaptive_jailbreak.utils.time import now_utc


DEFAULT_ATTACKER_MODEL = "sshleifer/tiny-gpt2"
DEFAULT_TARGET_MODEL = "hf-internal-testing/tiny-random-gpt2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny local-model smoke test for the attacker-target experiment loop."
    )
    parser.add_argument("--config", default=str(ROOT / "configs" / "local_tiny_transformers.yaml"))
    parser.add_argument("--attacker-model", default=DEFAULT_ATTACKER_MODEL)
    parser.add_argument("--target-model", default=DEFAULT_TARGET_MODEL)
    parser.add_argument("--max-iterations", type=int, default=2)
    parser.add_argument("--max-new-tokens", type=int, default=48)
    parser.add_argument("--task-id", default=None, help="Optional single task ID override. Defaults to the config task list.")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--experiment-id", default=None)
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Require models to be available from local Hugging Face cache or local paths.",
    )
    return parser.parse_args()


def load_template(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config template must be a mapping: {path}")
    return data


def build_run_config(args: argparse.Namespace) -> Path:
    timestamp = now_utc().replace(":", "").replace("-", "").replace("Z", "")
    experiment_id = args.experiment_id or f"local_tiny_smoke_{timestamp}"
    output_dir = args.output_dir or f"outputs/{experiment_id}"

    config = deepcopy(load_template(args.config))
    config["experiment"]["experiment_id"] = experiment_id
    config["experiment"]["output_dir"] = output_dir
    config["experiment"]["local_only"] = True
    config["attacker"]["provider"] = "local"
    config["attacker"]["adapter"] = "local"
    config["attacker"]["model"] = args.attacker_model
    config["attacker"]["generation"]["max_tokens"] = args.max_new_tokens
    config["target"]["provider"] = "local"
    config["target"]["adapter"] = "local"
    config["target"]["model"] = args.target_model
    config["target"]["generation"]["max_tokens"] = args.max_new_tokens
    config["runner"]["max_iterations"] = args.max_iterations
    if args.task_id:
        config["tasks"]["task_ids"] = [args.task_id]

    run_config_dir = ROOT / output_dir
    resolved_output_dir = run_config_dir.resolve()
    if ROOT.resolve() not in resolved_output_dir.parents and resolved_output_dir != ROOT.resolve():
        raise ValueError(f"Output directory must stay under the project root: {output_dir}")
    run_config_dir.mkdir(parents=True, exist_ok=True)
    run_config_path = run_config_dir / "run_config.yaml"
    run_config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return run_config_path


def main() -> None:
    args = parse_args()
    if args.local_files_only:
        os.environ["ADAPTIVE_JAILBREAK_LOCAL_FILES_ONLY"] = "1"
    run_config_path = build_run_config(args)
    print(f"Using generated config: {run_config_path}")
    print("Loading local models. First run may download model weights into the Hugging Face cache.")

    try:
        runner = ExperimentRunner(ConfigLoader.load(run_config_path), project_root=ROOT)
        records = runner.run()
    except ImportError as exc:
        print(str(exc), file=sys.stderr)
        print("Install local-model dependencies with: pip install -e .[local]", file=sys.stderr)
        raise SystemExit(2) from exc

    analyzer = ResultAnalyzer(records)
    summary = analyzer.summarize()
    report_path = Path(runner.store.output_dir) / "report.md"
    report_path.write_text(markdown_report(analyzer), encoding="utf-8")

    print(f"Wrote {len(records)} trajectory records to {runner.store.trajectory_path}")
    print(f"Wrote report to {report_path}")
    print(f"Success rate: {summary['success_rate']:.3f}")
    print(f"Refusal rate: {summary['refusal_rate']:.3f}")


if __name__ == "__main__":
    main()
