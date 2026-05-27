from __future__ import annotations

from adaptive_jailbreak.schemas import AttackCandidate
from adaptive_jailbreak.strategies.base import AttackStrategy


class MutationStrategy(AttackStrategy):
    name = "mutation"

    def select_candidates(self, candidates: list[AttackCandidate], scores: list[dict]) -> list[AttackCandidate]:
        return sorted(
            candidates,
            key=lambda candidate: candidate.metadata.get("novelty_from_previous", 0),
            reverse=True,
        )
