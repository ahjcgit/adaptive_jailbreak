from __future__ import annotations

import random

from adaptive_injection.policies.bandit_policy import BanditAttackPolicy
from adaptive_injection.policies.base import AttackPolicy
from adaptive_injection.policies.random_policy import RandomAttackPolicy


def build_policy(name: str, rng: random.Random) -> AttackPolicy:
    normalized = name.strip().lower()
    if normalized == "random":
        return RandomAttackPolicy(rng)
    if normalized == "bandit":
        return BanditAttackPolicy(rng)
    raise ValueError(f"Unsupported attack policy: {name}")
