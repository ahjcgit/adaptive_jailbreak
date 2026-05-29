from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.adapters.dummy import DummyModelAdapter
from adaptive_jailbreak.adapters.local import LocalModelAdapter
from adaptive_jailbreak.schemas import AuthConfig, ModelConfig


def build_adapter(config_or_adapter: ModelConfig | str, model_id: str | None = None, provider: str | None = None, auth: AuthConfig | None = None) -> ModelAdapter:
    if isinstance(config_or_adapter, ModelConfig):
        config = config_or_adapter
        adapter = config.adapter
        model_id = config.model
        provider = config.provider
    else:
        config = None
        adapter = config_or_adapter
    if model_id is None or provider is None:
        raise ValueError("model_id and provider are required when adapter config is not provided")
    if adapter == "dummy":
        return DummyModelAdapter(model_id=model_id, provider=provider)
    if adapter == "local":
        return LocalModelAdapter.from_config(config, model_id=model_id, provider=provider, auth=auth)
    raise ValueError(f"Unknown adapter: {adapter}")


__all__ = ["DummyModelAdapter", "LocalModelAdapter", "ModelAdapter", "build_adapter"]
