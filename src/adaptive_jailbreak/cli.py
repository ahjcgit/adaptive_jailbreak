from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from adaptive_jailbreak.analysis import (
    ResultAnalyzer,
    format_trajectory_markdown,
    format_trajectory_pretty_json,
    markdown_report,
)
from adaptive_jailbreak.config import ConfigLoader
from adaptive_jailbreak.evaluators import build_evaluator
from adaptive_jailbreak.runner import ExperimentRunner
from adaptive_jailbreak.safety import SafetyControls
from adaptive_jailbreak.schemas import TrajectoryRecord


def _load_records(path: str | Path) -> list[TrajectoryRecord]:
    return ResultAnalyzer.from_jsonl(path).records


def cmd_run(args: argparse.Namespace) -> None:
    config = ConfigLoader.load(args.config)
    if args.dry_run:
        SafetyControls.from_config(config).validate_experiment_config()
        print("Config valid; dry run complete.")
        return
    runner = ExperimentRunner(config)
    records = runner.run()
    print(f"Wrote {len(records)} records to {runner.store.trajectory_path}")


def cmd_resume(args: argparse.Namespace) -> None:
    runner = ExperimentRunner(ConfigLoader.load(args.config))
    records = runner.run(resume_run_id=args.run_id, force_config=args.force_config)
    print(f"Resumed {args.run_id}; wrote {len(records)} new records.")


def cmd_evaluate(args: argparse.Namespace) -> None:
    config = ConfigLoader.load(args.config)
    evaluator = build_evaluator(config.evaluator)
    records = _load_records(args.trajectory)
    updated = []
    for record in records:
        task_stub = type("TaskStub", (), {"task_id": record.task_id, "prompt": record.attacker_prompt})()
        scores = evaluator.score(task_stub, record.attacker_prompt, record.target_response, [])
        payload = record.to_dict()
        payload["evaluator_scores"] = scores.to_dict()
        payload["success_label"] = scores.success_label
        payload["refusal_label"] = scores.refusal_label
        updated.append(payload)
    Path(args.output).write_text("\n".join(json.dumps(item, sort_keys=True) for item in updated) + "\n", encoding="utf-8")
    print(f"Wrote reevaluated records to {args.output}")


def cmd_summarize(args: argparse.Namespace) -> None:
    print(json.dumps(ResultAnalyzer.from_jsonl(args.trajectory).summarize(), indent=2, sort_keys=True))


def cmd_compare(args: argparse.Namespace) -> None:
    analyzer = ResultAnalyzer.from_jsonl(args.trajectory)
    print(json.dumps(analyzer.compare(args.field), indent=2, sort_keys=True))


def cmd_export(args: argparse.Namespace) -> None:
    records = _load_records(args.trajectory)
    output = Path(args.output)
    if args.format == "markdown":
        output.write_text(markdown_report(ResultAnalyzer(records)), encoding="utf-8")
    elif args.format == "json":
        output.write_text(json.dumps([record.to_dict() for record in records], indent=2), encoding="utf-8")
    elif args.format == "csv":
        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["run_id", "task_id", "iteration", "success_label", "refusal_label"])
            writer.writeheader()
            for record in records:
                writer.writerow({
                    "run_id": record.run_id,
                    "task_id": record.task_id,
                    "iteration": record.iteration,
                    "success_label": record.success_label,
                    "refusal_label": record.refusal_label,
                })
    else:
        raise ValueError(f"Unsupported export format: {args.format}")
    print(f"Exported {len(records)} records to {output}")


def cmd_format(args: argparse.Namespace) -> None:
    records = _load_records(args.trajectory)
    output = Path(args.output)
    if args.format == "markdown":
        output.write_text(format_trajectory_markdown(records), encoding="utf-8")
    elif args.format == "json":
        output.write_text(format_trajectory_pretty_json(records), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported format: {args.format}")
    print(f"Wrote {len(records)} formatted records to {output}")


def cmd_replay(args: argparse.Namespace) -> None:
    records = _load_records(args.trajectory)
    if args.run_id:
        records = [record for record in records if record.run_id == args.run_id]
    for record in records:
        print(f"[{record.run_id} iteration={record.iteration} task={record.task_id}]")
        print(f"prompt: {record.attacker_prompt}")
        print(f"response: {record.target_response}")
        print(f"labels: success={record.success_label} refusal={record.refusal_label}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adaptive-jailbreak")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--config", required=True)
    run.add_argument("--dry-run", action="store_true")
    run.set_defaults(func=cmd_run)
    resume = sub.add_parser("resume")
    resume.add_argument("--config", required=True)
    resume.add_argument("--run-id", required=True)
    resume.add_argument("--force-config", action="store_true")
    resume.set_defaults(func=cmd_resume)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--config", required=True)
    evaluate.add_argument("trajectory")
    evaluate.add_argument("--output", required=True)
    evaluate.set_defaults(func=cmd_evaluate)
    summarize = sub.add_parser("summarize")
    summarize.add_argument("trajectory")
    summarize.set_defaults(func=cmd_summarize)
    compare = sub.add_parser("compare")
    compare.add_argument("trajectory")
    compare.add_argument("--field", default="target_model")
    compare.set_defaults(func=cmd_compare)
    export = sub.add_parser("export")
    export.add_argument("trajectory")
    export.add_argument("--format", choices=["markdown", "json", "csv"], default="markdown")
    export.add_argument("--output", required=True)
    export.set_defaults(func=cmd_export)
    fmt = sub.add_parser("format")
    fmt.add_argument("trajectory")
    fmt.add_argument("--format", choices=["markdown", "json"], default="markdown")
    fmt.add_argument("--output", required=True)
    fmt.set_defaults(func=cmd_format)
    replay = sub.add_parser("replay")
    replay.add_argument("trajectory")
    replay.add_argument("--run-id")
    replay.set_defaults(func=cmd_replay)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
