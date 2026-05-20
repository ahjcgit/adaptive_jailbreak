from __future__ import annotations

from adaptive_jailbreak.judges.rubric import RestrictedJudge, UnrestrictedJudge


def build_judge(mode: str):
    if mode == "restricted":
        return RestrictedJudge()
    if mode == "unrestricted":
        return UnrestrictedJudge()
    raise ValueError(f"Unknown mode: {mode!r}")

