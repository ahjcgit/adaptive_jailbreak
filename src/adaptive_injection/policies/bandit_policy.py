from __future__ import annotations

import math
import random
from typing import Iterable

from adaptive_injection.models import JudgeResult, PromptCandidate
from adaptive_injection.policies.base import AttackPolicy


class BanditAttackPolicy(AttackPolicy):
    name = "bandit"

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.counts: dict[str, int] = {}
        self.values: dict[str, float] = {}
        self.total = 0

    def choose_next(self, frontier: Iterable[PromptCandidate]) -> PromptCandidate:
        items = list(frontier)
        best = None
        best_score = float("-inf")
        for item in items:
            arm = self._arm_name(item)
            count = self.counts.get(arm, 0)
            value = self.values.get(arm, 0.0)
            if count == 0:
                score = float("inf")
            else:
                score = value + math.sqrt((2.0 * math.log(max(self.total, 1))) / count)
            if score > best_score:
                best_score = score
                best = item
        assert best is not None
        return best

    def observe(self, candidate: PromptCandidate, result: JudgeResult, mutation_name: str | None) -> None:
        arm = mutation_name or self._arm_name(candidate)
        self.total += 1
        count = self.counts.get(arm, 0) + 1
        prev = self.values.get(arm, 0.0)
        reward = float(result.score)
        self.counts[arm] = count
        self.values[arm] = prev + (reward - prev) / count

    def _arm_name(self, candidate: PromptCandidate) -> str:
        if candidate.mutation_chain:
            return candidate.mutation_chain[-1]
        return f"seed:{candidate.seed_family}"
