from __future__ import annotations

import argparse

from adaptive_jailbreak.analysis import ResultAnalyzer
from adaptive_jailbreak.evaluators.manual_export import export_for_manual_annotation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trajectory")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    export_for_manual_annotation(ResultAnalyzer.from_jsonl(args.trajectory).records, args.output)


if __name__ == "__main__":
    main()
