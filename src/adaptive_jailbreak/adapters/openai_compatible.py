from __future__ import annotations

from typing import Any

from adaptive_jailbreak.adapters.base import AdapterCallResult
from adaptive_jailbreak.adapters.http_utils import post_json
from adaptive_jailbreak.models import ModelResponse, ModelUsage


class OpenAICompatibleAdapter:
    """
    OpenAI-style Chat Completions adapter:
      POST {base_url}/chat/completions

    Expected env var (by default): OPENAI_COMPAT_API_KEY
    """

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str | None = None,
        timeout_s: float = 60.0,
    ):
        if not base_url:
            raise ValueError("OpenAICompatibleAdapter requires base_url.")
        if not model:
            raise ValueError("OpenAICompatibleAdapter requires model.")
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_s = timeout_s

    def generate(self, prompt: str, system_prompt: str | None = None) -> AdapterCallResult:
        url = f"{self._base_url}/chat/completions"
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.7,
        }

        resp = post_json(url, payload, timeout_s=self._timeout_s, headers=headers)
        js = resp.json or {}

        choice0: dict[str, Any] = {}
        if isinstance(js, dict):
            choices = js.get("choices")
            if isinstance(choices, list) and choices:
                if isinstance(choices[0], dict):
                    choice0 = choices[0]

        msg = choice0.get("message") if isinstance(choice0, dict) else None
        content = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(content, str):
            content = resp.text

        usage_js = js.get("usage") if isinstance(js, dict) else None
        usage = ModelUsage(
            prompt_tokens=(usage_js or {}).get("prompt_tokens") if isinstance(usage_js, dict) else None,
            completion_tokens=(usage_js or {}).get("completion_tokens") if isinstance(usage_js, dict) else None,
            total_tokens=(usage_js or {}).get("total_tokens") if isinstance(usage_js, dict) else None,
        )

        finish_reason = choice0.get("finish_reason") if isinstance(choice0, dict) else None
        return AdapterCallResult(
            response=ModelResponse(
                text=content,
                raw=js if isinstance(js, dict) else {"raw_text": resp.text},
                usage=usage,
                finish_reason=str(finish_reason) if finish_reason is not None else None,
            ),
            latency_s=resp.latency_s,
        )

