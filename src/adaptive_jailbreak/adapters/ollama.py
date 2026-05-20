from __future__ import annotations

from typing import Any

from adaptive_jailbreak.adapters.base import AdapterCallResult
from adaptive_jailbreak.adapters.http_utils import post_json
from adaptive_jailbreak.models import ModelResponse, ModelUsage


class OllamaAdapter:
    """
    Minimal Ollama chat adapter.

    Uses the local HTTP API (default `http://localhost:11434`).
    """

    def __init__(self, model: str, base_url: str | None = None, timeout_s: float = 60.0):
        if not model:
            raise ValueError("OllamaAdapter requires a model name.")
        self._model = model
        self._base_url = (base_url or "http://localhost:11434").rstrip("/")
        self._timeout_s = timeout_s

    def generate(self, prompt: str, system_prompt: str | None = None) -> AdapterCallResult:
        url = f"{self._base_url}/api/chat"
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
        }
        resp = post_json(url, payload, timeout_s=self._timeout_s)
        js = resp.json or {}
        msg = ((js.get("message") or {}) if isinstance(js, dict) else {}) or {}
        text = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(text, str):
            text = resp.text

        usage = ModelUsage(
            prompt_tokens=js.get("prompt_eval_count") if isinstance(js, dict) else None,
            completion_tokens=js.get("eval_count") if isinstance(js, dict) else None,
            total_tokens=None,
        )
        return AdapterCallResult(
            response=ModelResponse(
                text=text,
                raw=js if isinstance(js, dict) else {"raw_text": resp.text},
                usage=usage,
                finish_reason="stop",
            ),
            latency_s=resp.latency_s,
        )

