from adaptive_jailbreak.strategies.ablation import NoReflectionAblationStrategy
from adaptive_jailbreak.strategies.base import AttackStrategy
from adaptive_jailbreak.strategies.beam import BeamSearchStrategy
from adaptive_jailbreak.strategies.iterative import IterativeRefinementStrategy
from adaptive_jailbreak.strategies.memory import MemoryStrategy
from adaptive_jailbreak.strategies.mutation import MutationStrategy
from adaptive_jailbreak.strategies.reflection import ReflectionStrategy


def build_strategy(name: str | None) -> AttackStrategy:
    mapping = {
        "iterative": IterativeRefinementStrategy,
        "reflection": ReflectionStrategy,
        "mutation": MutationStrategy,
        "beam": BeamSearchStrategy,
        "memory": MemoryStrategy,
        "ablation": NoReflectionAblationStrategy,
        None: ReflectionStrategy,
    }
    if name not in mapping:
        raise ValueError(f"Unknown strategy: {name}")
    return mapping[name]()


__all__ = [
    "AttackStrategy",
    "BeamSearchStrategy",
    "IterativeRefinementStrategy",
    "MemoryStrategy",
    "MutationStrategy",
    "NoReflectionAblationStrategy",
    "ReflectionStrategy",
    "build_strategy",
]
