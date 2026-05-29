from __future__ import annotations

import os
from time import perf_counter
from typing import Any

from adaptive_jailbreak.adapters.base import ModelAdapter
from adaptive_jailbreak.schemas import AuthConfig, GenerationConfig, ModelConfig, ModelMessage, ModelResponse


class LocalModelAdapter(ModelAdapter):
    '''Transformers-backed local adapter.

    Model text is treated as inert data: the adapter only returns generated strings and metadata.
    '''

    _model_cache: dict[str, tuple[Any, Any, str]] = {}
    supports_seed = True

    def __init__(
        self,
        model_id: str,
        provider: str = "local",
        backend: str | None = None,
        revision: str | None = None,
        torch_dtype: str | None = None,
        device_map: str | None = None,
        quantization: dict[str, Any] | None = None,
        hf_token: str | None = None,
    ) -> None:
        super().__init__(model_id=model_id, provider=provider)
        self.backend = backend or "transformers"
        self.revision = revision
        self.torch_dtype = torch_dtype
        self.device_map = device_map
        self.quantization = quantization or {}
        self.hf_token = hf_token

    @classmethod
    def from_config(
        cls,
        config: ModelConfig | None,
        model_id: str,
        provider: str,
        auth: AuthConfig | None = None,
    ) -> "LocalModelAdapter":
        return cls(
            model_id=model_id,
            provider=provider,
            backend=config.backend if config else None,
            revision=config.revision if config else None,
            torch_dtype=config.torch_dtype if config else None,
            device_map=config.device_map if config else None,
            quantization=config.quantization if config else None,
            hf_token=auth.huggingface_token if auth else None,
        )

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
        cache_key = self._cache_key()
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError as exc:  # pragma: no cover - depends on optional environment
            raise ImportError(
                "LocalModelAdapter requires transformers and torch. Install with: pip install -e .[local]"
            ) from exc

        local_files_only = os.getenv("ADAPTIVE_JAILBREAK_LOCAL_FILES_ONLY", "").lower() in {"1", "true", "yes"}
        common_kwargs = self._hub_kwargs(local_files_only)
        tokenizer = AutoTokenizer.from_pretrained(self.model_id, **common_kwargs)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model_kwargs = self._model_kwargs(torch, BitsAndBytesConfig, common_kwargs)
        model = AutoModelForCausalLM.from_pretrained(self.model_id, **model_kwargs)
        device = self._input_device(torch, model)
        if not self.device_map:
            model.to(device)
        model.eval()
        self._model_cache[cache_key] = (tokenizer, model, device)
        return tokenizer, model, device

    def _hub_kwargs(self, local_files_only: bool) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"local_files_only": local_files_only}
        if self.revision:
            kwargs["revision"] = self.revision
        if self.hf_token:
            kwargs["token"] = self.hf_token
        return kwargs

    def _model_kwargs(self, torch: Any, bits_and_bytes_config: Any, common_kwargs: dict[str, Any]) -> dict[str, Any]:
        kwargs = dict(common_kwargs)
        if self.torch_dtype:
            kwargs["dtype"] = self._torch_dtype(torch, self.torch_dtype)
        if self.device_map:
            kwargs["device_map"] = self.device_map
        quantization = dict(self.quantization)
        bits = quantization.pop("bits", None)
        if bits in {4, "4", "4bit"}:
            kwargs["quantization_config"] = self._quantization_config(
                torch,
                bits_and_bytes_config,
                load_in_4bit=True,
                quantization=quantization,
            )
        elif bits in {8, "8", "8bit"}:
            kwargs["quantization_config"] = self._quantization_config(
                torch,
                bits_and_bytes_config,
                load_in_8bit=True,
                quantization=quantization,
            )
        elif bits not in {None, "none"}:
            raise ValueError(f"Unsupported quantization bits: {bits}")
        return kwargs

    def _quantization_config(
        self,
        torch: Any,
        bits_and_bytes_config: Any,
        quantization: dict[str, Any],
        **load_kwargs: Any,
    ) -> Any:
        bnb_kwargs = dict(load_kwargs)
        compute_dtype = quantization.pop("bnb_4bit_compute_dtype", quantization.pop("compute_dtype", None))
        if compute_dtype:
            bnb_kwargs["bnb_4bit_compute_dtype"] = self._torch_dtype(torch, str(compute_dtype))
        for key, value in quantization.items():
            bnb_kwargs[key] = value
        return bits_and_bytes_config(**bnb_kwargs)

    @staticmethod
    def _torch_dtype(torch: Any, value: str) -> Any:
        mapping = {
            "auto": "auto",
            "float16": torch.float16,
            "fp16": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float32": torch.float32,
            "fp32": torch.float32,
        }
        if value not in mapping:
            raise ValueError(f"Unsupported torch_dtype: {value}")
        return mapping[value]

    def _input_device(self, torch: Any, model: Any) -> str:
        if self.device_map == "cpu":
            return "cpu"
        embedding_device = self._input_embedding_device(model)
        if embedding_device:
            return embedding_device
        if self.device_map:
            hf_device_map = getattr(model, "hf_device_map", {}) or {}
            for mapped_device in hf_device_map.values():
                device = self._normalize_device(mapped_device)
                if device:
                    return device
            model_device = self._normalize_device(getattr(model, "device", None))
            return model_device or "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _input_embedding_device(self, model: Any) -> str | None:
        get_embeddings = getattr(model, "get_input_embeddings", None)
        if not callable(get_embeddings):
            return None
        embeddings = get_embeddings()
        weight = getattr(embeddings, "weight", None)
        return self._normalize_device(getattr(weight, "device", None))

    @staticmethod
    def _normalize_device(device: Any) -> str | None:
        if device is None:
            return None
        if isinstance(device, int):
            return f"cuda:{device}"
        device_name = str(device)
        if device_name.isdigit():
            return f"cuda:{device_name}"
        if device_name in {"cpu", "disk", "meta"}:
            return None
        return device_name

    def _cache_key(self) -> str:
        return repr((self.model_id, self.revision, self.torch_dtype, self.device_map, sorted(self.quantization.items())))

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
