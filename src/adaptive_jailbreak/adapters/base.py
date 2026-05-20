from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from adaptive_jailbreak.models import ModelResponse


@dataclass(frozen=True)
class AdapterCallResult:
    response: ModelResponse
    latency_s: float


class ModelAdapter(Protocol):
    """
    Minimal contract for either generator or target backends.

    The runner treats both as the same interface: "send prompt -> get response + latency".
    """

    def generate(self, prompt: str, system_prompt: str | None = None) -> AdapterCallResult: ...

