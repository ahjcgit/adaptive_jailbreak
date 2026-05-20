from __future__ import annotations

from adaptive_injection.targets.base import TargetAdapter
from adaptive_injection.targets.mock_target import MockSafetyTarget
from adaptive_injection.targets.openai_compatible import OpenAICompatibleTarget


def build_target(name: str, seed: int = 0) -> TargetAdapter:
    normalized = name.strip().lower()
    if normalized == "mock":
        return MockSafetyTarget(seed=seed)
    if normalized in {"openai", "openai-compatible"}:
        return OpenAICompatibleTarget()
    raise ValueError(f"Unsupported target: {name}")
