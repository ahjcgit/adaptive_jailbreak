from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from adaptive_jailbreak.schemas import GenerationConfig, ModelMessage, ModelResponse


class ModelAdapter(ABC):
    supports_system_prompt = True
    supports_seed = False

    def __init__(self, model_id: str, provider: str) -> None:
        self.model_id = model_id
        self.provider = provider

    @abstractmethod
    def generate(
        self,
        messages: list[ModelMessage],
        generation_config: GenerationConfig,
        metadata: dict[str, Any] | None = None,
    ) -> ModelResponse:
        raise NotImplementedError

    def healthcheck(self) -> bool:
        return True
