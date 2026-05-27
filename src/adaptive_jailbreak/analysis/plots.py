from __future__ import annotations

from pathlib import Path

from adaptive_jailbreak.analysis.analyzer import ResultAnalyzer


def write_success_over_time_csv(analyzer: ResultAnalyzer, path: str | Path) -> None:
    lines = ["iteration,success_rate"]
    for iteration, value in sorted(analyzer.success_over_time().items()):
        lines.append(f"{iteration},{value}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
