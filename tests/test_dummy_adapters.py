from adaptive_jailbreak.adapters.dummy import DummyModelAdapter
from adaptive_jailbreak.adapters.local import LocalModelAdapter
from adaptive_jailbreak.schemas import AuthConfig, GenerationConfig, ModelConfig, ModelMessage


def test_dummy_adapter_is_deterministic():
    adapter = DummyModelAdapter("dummy", "dummy")
    messages = [ModelMessage(role="user", content="hello")]
    first = adapter.generate(messages, GenerationConfig(seed=1), {"role": "attacker", "iteration": 0, "task_id": "t"})
    second = adapter.generate(messages, GenerationConfig(seed=1), {"role": "attacker", "iteration": 0, "task_id": "t"})
    assert first.text == second.text
    assert first.provider == "dummy"


def test_local_adapter_accepts_quantized_huggingface_config():
    config = ModelConfig.from_dict(
        {
            "provider": "local",
            "model": "org/model",
            "adapter": "local",
            "device_map": "auto",
            "torch_dtype": "float16",
            "quantization": {"bits": 4, "compute_dtype": "float16"},
        }
    )
    adapter = LocalModelAdapter.from_config(config, "org/model", "local", AuthConfig(huggingface_token="hf_test"))
    assert adapter.device_map == "auto"
    assert adapter.torch_dtype == "float16"
    assert adapter.quantization["bits"] == 4
    assert adapter.hf_token == "hf_test"


def test_local_adapter_builds_bitsandbytes_quantization_config():
    class FakeTorch:
        float16 = "float16"
        bfloat16 = "bfloat16"
        float32 = "float32"

    class FakeBitsAndBytesConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    adapter = LocalModelAdapter(
        "org/model",
        quantization={"bits": 4, "compute_dtype": "float16"},
        device_map="auto",
        torch_dtype="float16",
    )
    kwargs = adapter._model_kwargs(FakeTorch, FakeBitsAndBytesConfig, {"local_files_only": False})
    assert "load_in_4bit" not in kwargs
    assert kwargs["quantization_config"].kwargs == {
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": "float16",
    }


def test_local_adapter_uses_embedding_device_when_device_map_is_empty():
    class FakeWeight:
        device = "cuda:0"

    class FakeEmbeddings:
        weight = FakeWeight()

    class FakeModel:
        hf_device_map = {}
        device = "cuda:0"

        def get_input_embeddings(self):
            return FakeEmbeddings()

    adapter = LocalModelAdapter("org/model", device_map="auto")
    assert adapter._input_device(None, FakeModel()) == "cuda:0"
