from __future__ import annotations

from abc import ABC, abstractmethod

from adaptive_injection.models import TargetResponse


class TargetAdapter(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> TargetResponse:
        raise NotImplementedError
