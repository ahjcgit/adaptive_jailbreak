from __future__ import annotations

import argparse
import os
from dataclasses import asdict

from adaptive_jailbreak.adapters.factory import build_model_adapter
from adaptive_jailbreak.judges.factory import build_judge
from adaptive_jailbreak.policies.factory import build_policy
from adaptive_jailbreak.runners.experiment import ExperimentRunner
from adaptive_jailbreak.models import AdapterConfig


def _env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    return v if v not in (None, "") else default


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="adaptive-jailbreak")

    p.add_argument("--run-id", default="run", help="Run identifier used for artifact filenames.")
    p.add_argument("--budget", type=int, default=20, help="Number of trials to run.")
    p.add_argument("--seed", type=int, default=0, help="Random seed.")

    p.add_argument("--mode", choices=["restricted", "unrestricted"], default="restricted")
    p.add_argument(
        "--enable-unrestricted",
        action="store_true",
        help="Required gate to run unrestricted mode.",
    )

    p.add_argument("--gen", choices=["mock", "ollama", "openai-compatible"], default="mock")
    p.add_argument("--gen-model", default=_env("GEN_MODEL"))
    p.add_argument("--gen-base-url", default=_env("GEN_BASE_URL"))

    p.add_argument("--target", choices=["mock", "ollama", "openai-compatible"], default="mock")
    p.add_argument("--target-model", default=_env("OPENAI_COMPAT_MODEL") or _env("TARGET_MODEL"))
    p.add_argument("--target-base-url", default=_env("OPENAI_COMPAT_BASE_URL") or _env("TARGET_BASE_URL"))

    p.add_argument("--policy", choices=["random", "bandit"], default="bandit")

    p.add_argument("--timeout-s", type=float, default=60.0)

    p.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Artifact root directory; mode subdirectories are created under this.",
    )

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)

    if args.mode == "unrestricted" and not args.enable_unrestricted:
        raise SystemExit("Unrestricted mode requires --enable-unrestricted.")

    gen_cfg = AdapterConfig(
        backend=args.gen,
        model=args.gen_model,
        base_url=args.gen_base_url,
        timeout_s=args.timeout_s,
    )
    target_cfg = AdapterConfig(
        backend=args.target,
        model=args.target_model,
        base_url=args.target_base_url,
        api_key_env="OPENAI_COMPAT_API_KEY",
        timeout_s=args.timeout_s,
    )

    generator = build_model_adapter(gen_cfg, role="generator")
    target = build_model_adapter(target_cfg, role="target")
    judge = build_judge(mode=args.mode)
    policy = build_policy(args.policy, seed=args.seed, mode=args.mode)

    runner = ExperimentRunner(
        run_id=args.run_id,
        budget=args.budget,
        seed=args.seed,
        mode=args.mode,
        policy_name=args.policy,
        generator_cfg=gen_cfg,
        target_cfg=target_cfg,
        generator=generator,
        target=target,
        judge=judge,
        policy=policy,
        artifacts_dir=args.artifacts_dir,
    )

    summary = runner.run()
    print(summary["summary_line"])
    if os.environ.get("ADAPTIVE_JAILBREAK_DEBUG") == "1":
        print(asdict(gen_cfg))
        print(asdict(target_cfg))
    return 0
