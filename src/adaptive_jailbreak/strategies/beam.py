from __future__ import annotations

from adaptive_jailbreak.schemas import AttackCandidate
from adaptive_jailbreak.strategies.base import AttackStrategy


class BeamSearchStrategy(AttackStrategy):
    name = "beam"

    def __init__(self, beam_width: int = 3) -> None:
        self.beam_width = beam_width

    def select_candidates(self, candidates: list[AttackCandidate], scores: list[dict]) -> list[AttackCandidate]:
        paired = list(zip(candidates, scores, strict=False))
        paired.sort(key=lambda item: item[1].get("compliance_score", 0.0), reverse=True)
        return [candidate for candidate, _ in paired[: self.beam_width]]
