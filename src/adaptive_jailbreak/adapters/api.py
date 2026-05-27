from __future__ import annotations

from typing import Any, Callable

from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.schemas import GenerationConfig, ModelMessage, ModelResponse


class APIModelAdapter(ModelAdapter):
    '''API adapter shell with injectable client for controlled tests and provider integrations.'''

    def __init__(
        self,
        model_id: str,
        provider: str,
        client: Callable[[list[ModelMessage], GenerationConfig, dict[str, Any]], str] | None = None,
    ) -> None:
        super().__init__(model_id=model_id, provider=provider)
        self.client = client

    def generate(
        self,
        messages: list[ModelMessage],
        generation_config: GenerationConfig,
        metadata: dict[str, Any] | None = None,
    ) -> ModelResponse:
        if self.client is None:
            raise NotImplementedError("APIModelAdapter requires an explicit provider client.")
        metadata = metadata or {}
        text = self.client(messages, generation_config, metadata)
        return ModelResponse(text=text, model_id=self.model_id, provider=self.provider, metadata=metadata)
