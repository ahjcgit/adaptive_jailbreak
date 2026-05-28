from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from adaptive_jailbreak.analysis.formatting import format_trajectory_markdown
from adaptive_jailbreak.schemas import TrajectoryRecord
from adaptive_jailbreak.utils.time import now_utc


class JsonlTrajectoryStore:
    def __init__(
        self,
        output_dir: str | Path,
        experiment_id: str,
        config_hash: str,
        config_path: str | None = None,
        flush_each_record: bool = True,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.experiment_id = experiment_id
        self.config_hash = config_hash
        self.config_path = config_path
        self.flush_each_record = flush_each_record
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.trajectory_path = self.output_dir / "trajectory.jsonl"
        self.trajectory_markdown_path = self.output_dir / "trajectory.md"
        self.manifest_path = self.output_dir / "manifest.json"
        self._ensure_manifest()

    def _ensure_manifest(self) -> None:
        if self.manifest_path.exists():
            return
        manifest = {
            "experiment_id": self.experiment_id,
            "config_hash": self.config_hash,
            "config_path": self.config_path,
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "run_ids": [],
            "runs": {},
            "summary": {"records": 0},
            "errors": [],
        }
        self._write_manifest(manifest)

    def _read_manifest(self) -> dict[str, Any]:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: dict[str, Any]) -> None:
        manifest["updated_at"] = now_utc()
        self.manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    def create_or_resume_run(self, task_id: str, resume_run_id: str | None = None, force_config: bool = False) -> str:
        manifest = self._read_manifest()
        if manifest["config_hash"] != self.config_hash and not force_config:
            raise ValueError("Config hash mismatch; pass force_config=True to override.")
        if resume_run_id:
            if resume_run_id not in manifest["runs"]:
                raise ValueError(f"Unknown run_id: {resume_run_id}")
            manifest["runs"][resume_run_id]["status"] = "running"
            self._write_manifest(manifest)
            return resume_run_id
        for run_id, run in manifest["runs"].items():
            if run["task_id"] == task_id and run["status"] in {"pending", "running", "interrupted", "failed"}:
                run["status"] = "running"
                self._write_manifest(manifest)
                return run_id
        run_id = f"run_{task_id}_{len(manifest['run_ids']) + 1:04d}"
        manifest["run_ids"].append(run_id)
        manifest["runs"][run_id] = {
            "task_id": task_id,
            "status": "running",
            "resume_pointer": -1,
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "completed_reason": None,
        }
        self._write_manifest(manifest)
        return run_id

    def append(self, record: TrajectoryRecord) -> None:
        with self.trajectory_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
            if self.flush_each_record:
                handle.flush()
                os.fsync(handle.fileno())
        manifest = self._read_manifest()
        run = manifest["runs"].setdefault(record.run_id, {"task_id": record.task_id, "status": "running"})
        run["resume_pointer"] = max(int(run.get("resume_pointer", -1)), record.iteration)
        run["updated_at"] = now_utc()
        manifest["summary"]["records"] = int(manifest["summary"].get("records", 0)) + 1
        self._write_manifest(manifest)
        self.write_markdown_output()

    def load_trajectory(self, run_id: str | None = None) -> list[TrajectoryRecord]:
        if not self.trajectory_path.exists():
            return []
        records: list[TrajectoryRecord] = []
        for line in self.trajectory_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = TrajectoryRecord.from_dict(json.loads(line))
            if run_id is None or record.run_id == run_id:
                records.append(record)
        return sorted(records, key=lambda record: (record.run_id, record.iteration))

    def write_markdown_output(self) -> None:
        records = self.load_trajectory()
        self.trajectory_markdown_path.write_text(format_trajectory_markdown(records), encoding="utf-8")

    def mark_run_complete(self, run_id: str, reason: str) -> None:
        manifest = self._read_manifest()
        manifest["runs"][run_id]["status"] = "completed"
        manifest["runs"][run_id]["completed_reason"] = reason
        manifest["runs"][run_id]["updated_at"] = now_utc()
        self._write_manifest(manifest)

    def mark_run_failed(self, run_id: str, error: str) -> None:
        manifest = self._read_manifest()
        manifest["runs"][run_id]["status"] = "failed"
        manifest["errors"].append({"run_id": run_id, "error": error, "timestamp": now_utc()})
        self._write_manifest(manifest)
