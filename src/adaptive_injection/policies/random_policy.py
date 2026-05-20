from __future__ import annotations

import random
from typing import Iterable

from adaptive_injection.models import JudgeResult, PromptCandidate
from adaptive_injection.policies.base import AttackPolicy


class RandomAttackPolicy(AttackPolicy):
    name = "random"

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def choose_next(self, frontier: Iterable[PromptCandidate]) -> PromptCandidate:
        items = list(frontier)
        return self.rng.choice(items)

    def observe(self, candidate: PromptCandidate, result: JudgeResult, mutation_name: str | None) -> None:
        return None
