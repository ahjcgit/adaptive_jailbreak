from __future__ import annotations

import random
import time
from dataclasses import asdict
from typing import Any

from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.models import (
    AdapterConfig,
    ExperimentState,
    PromptCandidate,
    Timings,
    TrialRecord,
)
from adaptive_jailbreak.utils.io import ensure_dir, write_csv, write_json, write_jsonl


class ExperimentRunner:
    def __init__(
        self,
        *,
        run_id: str,
        budget: int,
        seed: int,
        mode: str,
        policy_name: str,
        generator_cfg: AdapterConfig,
        target_cfg: AdapterConfig,
        generator: ModelAdapter,
        target: ModelAdapter,
        judge,
        policy,
        artifacts_dir: str = "artifacts",
    ):
        self._run_id = run_id
        self._budget = int(budget)
        self._seed = int(seed)
        self._mode = mode
        self._policy_name = policy_name
        self._generator_cfg = generator_cfg
        self._target_cfg = target_cfg
        self._generator = generator
        self._target = target
        self._judge = judge
        self._policy = policy
        self._rng = random.Random(self._seed)

        mode_dir = "modeA" if mode == "restricted" else "modeB"
        self._artifacts_root = f"{artifacts_dir.rstrip('/\\\\')}/{mode_dir}"
        self._logs_dir = f"{self._artifacts_root}/logs"
        self._metrics_dir = f"{self._artifacts_root}/metrics"

    def run(self) -> dict[str, Any]:
        ensure_dir(self._logs_dir)
        ensure_dir(self._metrics_dir)

        state = ExperimentState(
            run_id=self._run_id,
            mode=self._mode,  # type: ignore[arg-type]
            budget=self._budget,
            policy_name=self._policy_name,
        )

        records: list[TrialRecord] = []

        for trial_idx in range(self._budget):
            # 1) Choose next prompt family/template/mutator using policy
            candidate: PromptCandidate = self._policy.next_candidate(state)

            # 2) Ask generator model to produce the concrete prompt (can also be identity)
            gen_prompt = self._policy.render_generator_prompt(state, candidate)
            gen_call = self._generator.generate(gen_prompt, system_prompt=self._policy.generator_system_prompt(state))
            generated_prompt = self._policy.extract_prompt_from_generator(gen_call.response.text, fallback=candidate.prompt)

            # 3) Send to target model
            target_call = self._target.generate(
                generated_prompt,
                system_prompt=self._policy.target_system_prompt(state),
            )

            # 4) Judge + metrics
            judge_result = self._judge.evaluate(
                prompt=generated_prompt,
                response_text=target_call.response.text,
                mode=self._mode,
            )

            record = TrialRecord(
                run_id=self._run_id,
                trial_idx=trial_idx,
                mode=self._mode,  # type: ignore[arg-type]
                generator=self._generator_cfg,
                target=self._target_cfg,
                policy=self._policy_name,
                candidate=PromptCandidate(
                    prompt=generated_prompt,
                    family=candidate.family,
                    metadata={**candidate.metadata},
                ),
                generator_timing=Timings(latency_s=gen_call.latency_s),
                target_timing=Timings(latency_s=target_call.latency_s),
                response=target_call.response,
                judge=judge_result,
                created_at_unix_s=time.time(),
            )

            state.history.append(record)
            records.append(record)
            self._policy.observe(state, record)

        jsonl_path = f"{self._logs_dir}/{self._run_id}.jsonl"
        csv_path = f"{self._logs_dir}/{self._run_id}.csv"
        summary_path = f"{self._metrics_dir}/{self._run_id}_summary.json"

        # JSONL: full fidelity
        write_jsonl(jsonl_path, [asdict(r) for r in records])

        # CSV: flattened human-friendly view
        csv_rows: list[dict[str, Any]] = []
        for r in records:
            csv_rows.append(
                {
                    "run_id": r.run_id,
                    "trial_idx": r.trial_idx,
                    "mode": r.mode,
                    "policy": r.policy,
                    "family": r.candidate.family,
                    "jailbreak_success": r.judge.jailbreak_success,
                    "refusal_score": round(float(r.judge.refusal_score), 4),
                    "structure_score": round(float(r.judge.structure_score), 4),
                    "generator_latency_s": round(float(r.generator_timing.latency_s), 4),
                    "target_latency_s": round(float(r.target_timing.latency_s), 4),
                    "prompt": r.candidate.prompt,
                    "response": r.response.text,
                }
            )
        write_csv(csv_path, csv_rows)

        # Summary: aggregates
        successes = sum(1 for r in records if r.judge.jailbreak_success)
        avg_refusal = sum(float(r.judge.refusal_score) for r in records) / max(1, len(records))
        avg_structure = sum(float(r.judge.structure_score) for r in records) / max(1, len(records))
        avg_t_lat = sum(float(r.target_timing.latency_s) for r in records) / max(1, len(records))
        avg_g_lat = sum(float(r.generator_timing.latency_s) for r in records) / max(1, len(records))
        summary = {
            "run_id": self._run_id,
            "mode": self._mode,
            "budget": self._budget,
            "policy": self._policy_name,
            "successes": successes,
            "success_rate": successes / max(1, len(records)),
            "avg_refusal_score": avg_refusal,
            "avg_structure_score": avg_structure,
            "avg_generator_latency_s": avg_g_lat,
            "avg_target_latency_s": avg_t_lat,
            "artifacts": {
                "jsonl": jsonl_path,
                "csv": csv_path,
                "summary": summary_path,
            },
        }
        summary["summary_line"] = (
            f"run_id={self._run_id} mode={self._mode} budget={self._budget} "
            f"success_rate={summary['success_rate']:.2%} avg_refusal={avg_refusal:.3f} "
            f"avg_target_latency_s={avg_t_lat:.3f}"
        )
        write_json(summary_path, summary)
        return summary
