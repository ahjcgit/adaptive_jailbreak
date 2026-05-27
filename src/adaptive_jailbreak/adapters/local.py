from __future__ import annotations

import os
from time import perf_counter
from typing import Any

from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.schemas import GenerationConfig, ModelMessage, ModelResponse


class LocalModelAdapter(ModelAdapter):
    '''Transformers-backed local adapter.

    Model text is treated as inert data: the adapter only returns generated strings and metadata.
    '''

    _model_cache: dict[str, tuple[Any, Any, str]] = {}
    supports_seed = True

    def __init__(self, model_id: str, provider: str = "local", backend: str | None = None) -> None:
        super().__init__(model_id=model_id, provider=provider)
        self.backend = backend or "transformers"

    def generate(
        self,
        messages: list[ModelMessage],
        generation_config: GenerationConfig,
        metadata: dict[str, Any] | None = None,
    ) -> ModelResponse:
        if self.backend != "transformers":
            raise NotImplementedError(f"Unsupported local backend: {self.backend}")

        start = perf_counter()
        tokenizer, model, device = self._load_transformers_model()
        prompt = self._format_messages(messages)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        inputs = {key: value.to(device) for key, value in inputs.items()}

        self._seed(generation_config.seed)
        do_sample = generation_config.temperature > 0
        generate_kwargs: dict[str, Any] = {
            "max_new_tokens": generation_config.max_tokens,
            "do_sample": do_sample,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if do_sample:
            generate_kwargs["temperature"] = generation_config.temperature
            generate_kwargs["top_p"] = generation_config.top_p

        try:
            import torch
        except ImportError as exc:  # pragma: no cover - depends on optional environment
            raise ImportError("LocalModelAdapter requires torch. Install with: pip install -e .[local]") from exc

        with torch.no_grad():
            output_ids = model.generate(**inputs, **generate_kwargs)

        input_length = int(inputs["input_ids"].shape[-1])
        generated_ids = output_ids[0][input_length:]
        text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        if not text:
            text = tokenizer.decode(output_ids[0], skip_special_tokens=True).replace(prompt, "", 1).strip()

        elapsed_ms = int((perf_counter() - start) * 1000)
        response_metadata = dict(metadata or {})
        response_metadata.update(
            {
                "backend": self.backend,
                "device": device,
                "latency_ms": elapsed_ms,
                "token_usage": {
                    "input_tokens": input_length,
                    "output_tokens": int(generated_ids.shape[-1]),
                },
            }
        )
        return ModelResponse(text=text, model_id=self.model_id, provider=self.provider, metadata=response_metadata)

    def healthcheck(self) -> bool:
        try:
            self._load_transformers_model()
        except ImportError:
            return False
        return True

    def _load_transformers_model(self) -> tuple[Any, Any, str]:
        if self.model_id in self._model_cache:
            return self._model_cache[self.model_id]
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - depends on optional environment
            raise ImportError(
                "LocalModelAdapter requires transformers and torch. Install with: pip install -e .[local]"
            ) from exc

        local_files_only = os.getenv("ADAPTIVE_JAILBREAK_LOCAL_FILES_ONLY", "").lower() in {"1", "true", "yes"}
        tokenizer = AutoTokenizer.from_pretrained(self.model_id, local_files_only=local_files_only)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(self.model_id, local_files_only=local_files_only)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        model.eval()
        self._model_cache[self.model_id] = (tokenizer, model, device)
        return tokenizer, model, device

    @staticmethod
    def _format_messages(messages: list[ModelMessage]) -> str:
        return "\n".join(f"{message.role}: {message.content}" for message in messages) + "\nassistant:"

    @staticmethod
    def _seed(seed: int | None) -> None:
        if seed is None:
            return
        try:
            import torch
        except ImportError as exc:  # pragma: no cover - depends on optional environment
            raise ImportError("LocalModelAdapter requires torch. Install with: pip install -e .[local]") from exc
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
