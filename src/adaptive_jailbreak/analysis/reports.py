from __future__ import annotations

from adaptive_jailbreak.analysis.analyzer import ResultAnalyzer


def markdown_report(analyzer: ResultAnalyzer) -> str:
    summary = analyzer.summarize()
    lines = [
        "# Experiment Report",
        "",
        f"- Records: {summary['records']}",
        f"- Success rate: {summary['success_rate']:.3f}",
        f"- Refusal rate: {summary['refusal_rate']:.3f}",
        "",
        "## Success Over Time",
    ]
    for iteration, value in sorted(analyzer.success_over_time().items()):
        lines.append(f"- Iteration {iteration}: {value:.3f}")
    return "\n".join(lines) + "\n"
