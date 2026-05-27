from __future__ import annotations

from adaptive_jailbreak.schemas import TrajectoryRecord
from adaptive_jailbreak.strategies.base import AttackStrategy


class NoReflectionAblationStrategy(AttackStrategy):
    name = "ablation"

    def _reflection(self, previous_step: TrajectoryRecord | None) -> str:
        return ""
