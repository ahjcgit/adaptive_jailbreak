from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from adaptive_injection.models import JudgeResult, PromptCandidate


class AttackPolicy(ABC):
    name: str

    @abstractmethod
    def choose_next(self, frontier: Iterable[PromptCandidate]) -> PromptCandidate:
        raise NotImplementedError

    @abstractmethod
    def observe(self, candidate: PromptCandidate, result: JudgeResult, mutation_name: str | None) -> None:
        raise NotImplementedError
