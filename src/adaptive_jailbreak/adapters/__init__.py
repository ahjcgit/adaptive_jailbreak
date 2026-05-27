from adaptive_jailbreak.adapters.api import APIModelAdapter
from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.adapters.dummy import DummyModelAdapter
from adaptive_jailbreak.adapters.local import LocalModelAdapter


def build_adapter(adapter: str, model_id: str, provider: str) -> ModelAdapter:
    if adapter == "dummy":
        return DummyModelAdapter(model_id=model_id, provider=provider)
    if adapter == "local":
        return LocalModelAdapter(model_id=model_id, provider=provider)
    if adapter == "api":
        return APIModelAdapter(model_id=model_id, provider=provider)
    raise ValueError(f"Unknown adapter: {adapter}")


__all__ = ["APIModelAdapter", "DummyModelAdapter", "LocalModelAdapter", "ModelAdapter", "build_adapter"]
