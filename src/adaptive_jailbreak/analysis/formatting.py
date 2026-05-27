from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from adaptive_jailbreak.schemas import TrajectoryRecord


def format_trajectory_markdown(records: list[TrajectoryRecord]) -> str:
    if not records:
        return "# Trajectory\n\nNo records found.\n"

    lines = [
        "# Trajectory",
        "",
        f"- Records: {len(records)}",
        f"- Experiment: `{records[0].experiment_id}`",
        f"- Attacker model: `{records[0].attacker_model}`",
        f"- Target model: `{records[0].target_model}`",
        "",
    ]

    grouped: dict[str, list[TrajectoryRecord]] = defaultdict(list)
    for record in records:
        grouped[record.run_id].append(record)

    for run_id, run_records in grouped.items():
        run_records = sorted(run_records, key=lambda record: record.iteration)
        task_id = run_records[0].task_id
        lines.extend(
            [
                f"## Run `{run_id}`",
                "",
                f"- Task: `{task_id}`",
                f"- Iterations: {len(run_records)}",
                "",
            ]
        )
        for record in run_records:
            scores = record.evaluator_scores
            metadata = record.metadata
            lines.extend(
                [
                    f"### Iteration {record.iteration}",
                    "",
                    "- Labels:",
                    f"  - Success: `{record.success_label}`",
                    f"  - Refusal: `{record.refusal_label}`",
                    f"  - Failure mode: `{metadata.get('failure_mode')}`",
                    "",
                    "- Scores:",
                    f"  - Compliance: `{_fmt(scores.get('compliance_score'))}`",
                    f"  - Refusal: `{_fmt(scores.get('refusal_score'))}`",
                    f"  - Semantic similarity: `{_fmt(scores.get('semantic_similarity'))}`",
                    f"  - Attack success probability: `{_fmt(scores.get('attack_success_probability'))}`",
                    "",
                    "- Metadata:",
                    f"  - Prompt length: `{metadata.get('prompt_length')}`",
                    f"  - Response length: `{metadata.get('response_length')}`",
                    f"  - Novelty from previous: `{_fmt(metadata.get('novelty_from_previous'))}`",
                    f"  - Target latency ms: `{metadata.get('adapter_latency_ms')}`",
                    "",
                    "**Attacker Reflection**",
                    "",
                    _fenced(record.attacker_reflection),
                    "",
                    "**Attacker Prompt**",
                    "",
                    _fenced(record.attacker_prompt),
                    "",
                    "**Target Response**",
                    "",
                    _fenced(record.target_response),
                    "",
                    "**Evaluator Rationale**",
                    "",
                    _fenced(str(scores.get("rationale", ""))),
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def format_trajectory_pretty_json(records: list[TrajectoryRecord]) -> str:
    payload: dict[str, Any] = {
        "records": [record.to_dict() for record in records],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if value is None:
        return "None"
    return str(value)


def _fenced(text: str) -> str:
    return "```text\n" + text.strip() + "\n```"
