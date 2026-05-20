from __future__ import annotations

import os

from adaptive_jailbreak.adapters.mock import MockAdapter
from adaptive_jailbreak.adapters.ollama import OllamaAdapter
from adaptive_jailbreak.adapters.openai_compatible import OpenAICompatibleAdapter
from adaptive_jailbreak.models import AdapterConfig


def build_model_adapter(cfg: AdapterConfig, role: str):
    backend = (cfg.backend or "").lower()
    if backend == "mock":
        return MockAdapter(role=role, seed=0)
    if backend == "ollama":
        return OllamaAdapter(model=cfg.model or "", base_url=cfg.base_url, timeout_s=cfg.timeout_s)
    if backend == "openai-compatible":
        api_key = os.environ.get(cfg.api_key_env or "OPENAI_COMPAT_API_KEY")
        base_url = cfg.base_url or os.environ.get("OPENAI_COMPAT_BASE_URL") or ""
        model = cfg.model or os.environ.get("OPENAI_COMPAT_MODEL") or ""
        return OpenAICompatibleAdapter(model=model, base_url=base_url, api_key=api_key, timeout_s=cfg.timeout_s)
    raise ValueError(f"Unknown backend: {cfg.backend!r}")

