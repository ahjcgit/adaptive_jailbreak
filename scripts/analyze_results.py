from __future__ import annotations

import argparse
import json

from adaptive_jailbreak.analysis import ResultAnalyzer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trajectory")
    args = parser.parse_args()
    print(json.dumps(ResultAnalyzer.from_jsonl(args.trajectory).summarize(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
