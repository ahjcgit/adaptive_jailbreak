from __future__ import annotations

from typing import Protocol

from adaptive_jailbreak.models import ExperimentState, PromptCandidate, TrialRecord


class AdaptivePolicy(Protocol):
    def next_candidate(self, state: ExperimentState) -> PromptCandidate: ...

    def observe(self, state: ExperimentState, record: TrialRecord) -> None: ...

    def generator_system_prompt(self, state: ExperimentState) -> str | None: ...

    def target_system_prompt(self, state: ExperimentState) -> str | None: ...

    def render_generator_prompt(self, state: ExperimentState, candidate: PromptCandidate) -> str: ...

    def extract_prompt_from_generator(self, generator_text: str, fallback: str) -> str: ...

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from adaptive_jailbreak.models import JudgeResult, PromptCandidate


class AttackPolicy(ABC):
    name: str

    @abstractmethod
    def choose_next(self, frontier: Iterable[PromptCandidate]) -> PromptCandidate:
        raise NotImplementedError

    @abstractmethod
    def observe(self, candidate: PromptCandidate, result: JudgeResult, mutation_name: str | None) -> None:
        raise NotImplementedError
