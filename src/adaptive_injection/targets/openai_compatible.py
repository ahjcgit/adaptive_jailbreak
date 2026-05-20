from __future__ import annotations

import json
import os
import time
import urllib.request

from adaptive_injection.models import TargetResponse
from adaptive_injection.targets.base import TargetAdapter


class OpenAICompatibleTarget(TargetAdapter):
    """Simple OpenAI-compatible chat adapter.

    TODO(user): set the environment variables documented in README and verify the
    response parsing matches your provider or local server.
    """

    name = "openai-compatible"

    def __init__(self) -> None:
        self.base_url = os.environ.get("OPENAI_COMPAT_BASE_URL")
        self.api_key = os.environ.get("OPENAI_COMPAT_API_KEY")
        self.model = os.environ.get("OPENAI_COMPAT_MODEL")
        if not self.base_url or not self.model:
            raise ValueError("Missing OPENAI_COMPAT_BASE_URL or OPENAI_COMPAT_MODEL")

    def generate(self, prompt: str, system_prompt: str | None = None) -> TargetResponse:
        start = time.perf_counter()
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                *([{"role": "system", "content": system_prompt}] if system_prompt else []),
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        req = urllib.request.Request(url, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        body = json.dumps(payload).encode("utf-8")
        with urllib.request.urlopen(req, body, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {}).get("total_tokens")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return TargetResponse(text=text, latency_ms=latency_ms, token_usage=usage, raw=data)
