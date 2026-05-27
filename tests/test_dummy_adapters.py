from adaptive_jailbreak.adapters.dummy import DummyModelAdapter
from adaptive_jailbreak.schemas import GenerationConfig, ModelMessage


def test_dummy_adapter_is_deterministic():
    adapter = DummyModelAdapter("dummy", "dummy")
    messages = [ModelMessage(role="user", content="hello")]
    first = adapter.generate(messages, GenerationConfig(seed=1), {"role": "attacker", "iteration": 0, "task_id": "t"})
    second = adapter.generate(messages, GenerationConfig(seed=1), {"role": "attacker", "iteration": 0, "task_id": "t"})
    assert first.text == second.text
    assert first.provider == "dummy"
