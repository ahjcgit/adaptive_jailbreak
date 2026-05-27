from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from adaptive_jailbreak.analysis import ResultAnalyzer, format_trajectory_markdown, format_trajectory_pretty_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Format trajectory JSONL into human-readable output.")
    parser.add_argument("trajectory", help="Path to trajectory.jsonl")
    parser.add_argument("--output", help="Output path. Defaults to trajectory.md next to the JSONL file.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    trajectory_path = Path(args.trajectory)
    records = ResultAnalyzer.from_jsonl(trajectory_path).records
    if args.format == "markdown":
        rendered = format_trajectory_markdown(records)
        default_output = trajectory_path.with_suffix(".md")
    else:
        rendered = format_trajectory_pretty_json(records)
        default_output = trajectory_path.with_name(trajectory_path.stem + ".pretty.json")

    output_path = Path(args.output) if args.output else default_output
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {len(records)} formatted records to {output_path}")


if __name__ == "__main__":
    main()
