from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from adaptive_jailbreak.schemas import TrajectoryRecord


class ResultAnalyzer:
    def __init__(self, records: list[TrajectoryRecord]) -> None:
        self.records = records

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "ResultAnalyzer":
        records: list[TrajectoryRecord] = []
        file_path = Path(path)
        if not file_path.exists():
            return cls([])
        for line in file_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(TrajectoryRecord.from_dict(json.loads(line)))
        return cls(records)

    def summarize(self) -> dict[str, Any]:
        total = len(self.records)
        successes = sum(1 for record in self.records if record.success_label == "success")
        refusals = sum(1 for record in self.records if record.refusal_label == "refusal")
        return {
            "records": total,
            "successes": successes,
            "refusals": refusals,
            "success_rate": successes / total if total else 0.0,
            "refusal_rate": refusals / total if total else 0.0,
            "by_target_model": dict(Counter(record.target_model for record in self.records)),
            "failure_modes": dict(Counter(record.metadata.get("failure_mode") for record in self.records)),
        }

    def compare(self, field: str) -> dict[str, dict[str, Any]]:
        grouped: dict[str, list[TrajectoryRecord]] = defaultdict(list)
        for record in self.records:
            grouped[str(getattr(record, field))].append(record)
        return {key: ResultAnalyzer(value).summarize() for key, value in grouped.items()}
