from __future__ import annotations

import json
from pathlib import Path

from adaptive_jailbreak.schemas import TrajectoryRecord


def export_for_manual_annotation(records: list[TrajectoryRecord], path: str | Path) -> None:
    payload = [
        {
            "run_id": record.run_id,
            "task_id": record.task_id,
            "iteration": record.iteration,
            "attacker_prompt": record.attacker_prompt,
            "target_response": record.target_response,
            "human_success_label": None,
            "human_refusal_label": None,
            "notes": "",
        }
        for record in records
    ]
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
