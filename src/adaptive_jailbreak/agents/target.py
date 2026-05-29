from __future__ import annotations

import re

from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.schemas import GenerationConfig, ModelMessage, ModelResponse


class TargetAgent:
    def __init__(self, adapter: ModelAdapter, generation_config: GenerationConfig) -> None:
        self.adapter = adapter
        self.generation_config = generation_config

    def respond(self, prompt: str, iteration: int = 0, system_prompt: str | None = None) -> ModelResponse:
        messages = []
        if system_prompt:
            messages.append(ModelMessage(role="system", content=system_prompt))
        messages.append(ModelMessage(role="user", content=prompt))
        response = self.adapter.generate(messages, self.generation_config, {"role": "target", "iteration": iteration})
        sanitized_text = self._sanitize_response(response.text)
        metadata = dict(response.metadata)
        metadata.update(
            {
                "raw_target_response": response.text,
                "target_response_sanitized": sanitized_text != response.text.strip(),
            }
        )
        return ModelResponse(
            text=sanitized_text,
            model_id=response.model_id,
            provider=response.provider,
            metadata=metadata,
        )

    def _sanitize_response(self, text: str) -> str:
        response = text.strip()
        if re.match(r"(?is)^ACCESS DENIED\b", response):
            return "ACCESS DENIED"

        cut_at = len(response)
        for pattern in [
            r"(?i)\s+(?:system|user|assistant)\s*:",
            r"(?i)\s+ACCESS DENIED\b",
        ]:
            match = re.search(pattern, response)
            if match:
                cut_at = min(cut_at, match.start())

        return response[:cut_at].strip()
