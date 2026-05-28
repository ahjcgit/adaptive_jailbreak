from adaptive_jailbreak.strategies.base import AttackStrategy
from adaptive_jailbreak.strategies.reflection import ReflectionStrategy


def build_strategy(name: str | None) -> AttackStrategy:
    mapping = {
        "reflection": ReflectionStrategy,
        None: ReflectionStrategy,
    }
    if name not in mapping:
        raise ValueError(f"Unknown strategy: {name}")
    return mapping[name]()


__all__ = [
    "AttackStrategy",
    "ReflectionStrategy",
    "build_strategy",
]
