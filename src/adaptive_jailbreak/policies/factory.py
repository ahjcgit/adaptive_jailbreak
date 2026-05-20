from __future__ import annotations

from adaptive_jailbreak.policies.bandit_policy import BanditPolicy
from adaptive_jailbreak.policies.random_policy import RandomPolicy


def build_policy(name: str, *, seed: int, mode: str):
    if name == "random":
        return RandomPolicy(seed=seed, mode=mode)
    if name == "bandit":
        return BanditPolicy(seed=seed, mode=mode)
    raise ValueError(f"Unknown policy: {name!r}")
