from __future__ import annotations

import argparse
import json

from adaptive_injection.models import DefenseConfig, ExperimentConfig, new_id
from adaptive_injection.runners.experiment import ExperimentRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adaptive jailbreak red-teaming harness")
    parser.add_argument("--seeds", default="data/seeds/sample_seeds.jsonl")
    parser.add_argument("--benign", default="data/benign/sample_benign.jsonl")
    parser.add_argument("--artifact-dir", default="artifacts")
    parser.add_argument("--budget", type=int, default=12)
    parser.add_argument("--max-turns", type=int, default=3)
    parser.add_argument("--policy", choices=["random", "bandit"], default="bandit")
    parser.add_argument("--target", choices=["mock", "openai-compatible"], default="mock")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--system-hardening", action="store_true")
    parser.add_argument("--input-moderation", action="store_true")
    parser.add_argument("--output-moderation", action="store_true")
    parser.add_argument("--self-critique", action="store_true")
    parser.add_argument("--response-normalization", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = ExperimentConfig(
        run_id=args.run_id or new_id("run"),
        seeds_path=args.seeds,
        benign_path=args.benign,
        artifact_dir=args.artifact_dir,
        budget=args.budget,
        max_turns=args.max_turns,
        attack_policy=args.policy,
        target_name=args.target,
        defense=DefenseConfig(
            system_hardening=args.system_hardening,
            input_moderation=args.input_moderation,
            output_moderation=args.output_moderation,
            self_critique=args.self_critique,
            response_normalization=args.response_normalization,
        ),
        seed=args.seed,
    )
    summary = ExperimentRunner(config).run()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
