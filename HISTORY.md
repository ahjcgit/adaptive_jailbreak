# History

## 2026-05-29 03:06 -07:00

Cleaned up the experiment pipeline after the single-file experiment migration.

- Simplified configuration/schema handling around inline experiment YAML.
- Removed legacy external task/allowlist loading paths and unused no-op config fields.
- Kept `hybrid` as a deprecated evaluator alias for rule-based scoring while removing the separate wrapper implementation.
- Added structured model-evaluator feedback via `EvaluatorScores.feedback`, with strategy fallback support for older rationale-embedded feedback.
- Simplified attacker strategy/runner next-prompt plumbing to derive the previous step from the trajectory.
- Removed duplicate CLI surface (`format`) and the brittle reevaluation command.
- Updated experiment YAMLs, README guidance, tests, and ignore rules for generated metadata/temp files.
- Removed tracked generated package metadata under `src/adaptive_jailbreak.egg-info/`.

Verification:

- `pytest` passed with 48 tests.
- `PYTHONPATH=src python -m adaptive_jailbreak.cli run --config experiments/synthetic_smoke.yaml --dry-run` completed successfully.
- Confirmed `outputs/` had no git status changes.
