from __future__ import annotations

import random
from pathlib import Path

from adaptive_injection.analysis.reporting import Reporter
from adaptive_injection.datasets.loader import DatasetLoader
from adaptive_injection.defenses.basic import DefensePipeline
from adaptive_injection.generation.mutators import PromptMutator
from adaptive_injection.judges.rubric import HeuristicJudge
from adaptive_injection.models import ExperimentConfig, TrialRecord, new_id
from adaptive_injection.policies.factory import build_policy
from adaptive_injection.targets.factory import build_target


class ExperimentRunner:
    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config
        self.rng = random.Random(config.seed)
        self.loader = DatasetLoader()
        self.mutator = PromptMutator(self.rng)
        self.policy = build_policy(config.attack_policy, self.rng)
        self.target = build_target(config.target_name, seed=config.seed)
        self.defenses = DefensePipeline(config.defense)
        self.judge = HeuristicJudge()
        self.reporter = Reporter()

    def run(self) -> dict:
        seeds = self.loader.load_seeds(self.config.seeds_path)
        benign = self.loader.load_benign(self.config.benign_path)
        frontier = [self.mutator.from_seed(seed) for seed in seeds]
        records: list[TrialRecord] = []
        refusal_pattern: str | None = None

        for step_idx in range(self.config.budget):
            current = self.policy.choose_next(frontier)
            blocked_in, blocked_input_msg = self.defenses.moderate_input(current.prompt_text)
            if blocked_in:
                response_text = blocked_input_msg or "Input blocked by moderation rule."
                latency_ms = 0
                token_usage = 0
                blocked_out = False
            else:
                response = self.target.generate(current.prompt_text, system_prompt=self.defenses.system_prompt())
                blocked_out, response = self.defenses.moderate_output(response)
                response = self.defenses.self_critique(response)
                response = self.defenses.normalize(response)
                response_text = response.text
                latency_ms = response.latency_ms
                token_usage = response.token_usage

            judged = self.judge.score(current.prompt_text, response_text)
            refusal_pattern = judged.features.get("refusal_pattern")
            self.policy.observe(current, judged, current.mutation_chain[-1] if current.mutation_chain else None)
            record = TrialRecord(
                trial_id=new_id("trial"),
                run_id=self.config.run_id,
                parent_trial_id=current.parent_candidate_id,
                step_idx=step_idx,
                turn_idx=current.turn_idx,
                target=self.target.name,
                defense_config=self.config.defense.to_dict(),
                attack_policy=self.policy.name,
                seed_family=current.seed_family,
                seed_id=current.seed_id,
                mutation_applied=current.mutation_chain,
                prompt_text=current.prompt_text,
                target_response=response_text,
                judge_score=judged.score,
                judge_label=judged.label,
                judge_confidence=judged.confidence,
                latency_ms=latency_ms,
                token_usage=token_usage,
                cost_estimate=estimate_cost(token_usage),
                blocked_by_input_guard=blocked_in,
                blocked_by_output_guard=blocked_out,
            )
            records.append(record)
            if step_idx + 1 >= self.config.budget:
                break
            mutation = self.mutator.mutate(current, refusal_pattern=refusal_pattern)
            frontier.append(mutation.candidate)

        benign_summary = self._run_benign_eval(benign)
        summary = self._write_outputs(records)
        summary["benign_eval"] = benign_summary
        summary_path = Path(self.config.artifact_dir) / "metrics" / f"{self.config.run_id}_summary.json"
        summary_path.write_text(__import__("json").dumps(summary, indent=2), encoding="utf-8")
        return summary

    def _run_benign_eval(self, benign_rows: list[dict]) -> dict:
        if not benign_rows:
            return {"count": 0, "over_refusal_rate": 0.0}
        refusals = 0
        for row in benign_rows:
            prompt = row["prompt"]
            blocked_in, _ = self.defenses.moderate_input(prompt)
            if blocked_in:
                refusals += 1
                continue
            response = self.target.generate(prompt, system_prompt=self.defenses.system_prompt())
            response = self.defenses.self_critique(response)
            if "cannot" in response.text.lower():
                refusals += 1
        return {
            "count": len(benign_rows),
            "over_refusal_rate": refusals / len(benign_rows),
        }

    def _write_outputs(self, records: list[TrialRecord]) -> dict:
        artifact = Path(self.config.artifact_dir)
        logs_dir = artifact / "logs"
        metrics_dir = artifact / "metrics"
        logs_dir.mkdir(parents=True, exist_ok=True)
        metrics_dir.mkdir(parents=True, exist_ok=True)
        jsonl_path = logs_dir / f"{self.config.run_id}.jsonl"
        csv_path = logs_dir / f"{self.config.run_id}.csv"
        summary_path = metrics_dir / f"{self.config.run_id}_summary.json"
        self.reporter.write_jsonl(str(jsonl_path), records)
        self.reporter.write_csv(str(csv_path), records)
        return self.reporter.write_summary(str(summary_path), records)


def estimate_cost(token_usage: int | None) -> float:
    if token_usage is None:
        return 0.0
    return round(token_usage * 0.000002, 6)
