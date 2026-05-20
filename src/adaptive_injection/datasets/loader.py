from __future__ import annotations

import json
from pathlib import Path

from adaptive_injection.models import PromptSeed


class DatasetLoader:
    def load_seeds(self, path: str) -> list[PromptSeed]:
        return [PromptSeed(**row) for row in self._read_jsonl(path)]

    def load_benign(self, path: str) -> list[dict]:
        return self._read_jsonl(path)

    def _read_jsonl(self, path: str) -> list[dict]:
        rows: list[dict] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
        return rows
