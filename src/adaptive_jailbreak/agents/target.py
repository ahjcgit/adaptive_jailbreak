from __future__ import annotations

from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.schemas import GenerationConfig, ModelMessage, ModelResponse


class TargetAgent:
    def __init__(self, adapter: ModelAdapter, generation_config: GenerationConfig) -> None:
        self.adapter = adapter
        self.generation_config = generation_config

    def respond(self, prompt: str, iteration: int = 0) -> ModelResponse:
        messages = [ModelMessage(role="user", content=prompt)]
        return self.adapter.generate(messages, self.generation_config, {"role": "target", "iteration": iteration})
