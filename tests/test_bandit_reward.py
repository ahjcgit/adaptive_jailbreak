from adaptive_jailbreak.models import (
    AdapterConfig,
    JudgeResult,
    ModelResponse,
    PromptCandidate,
    Timings,
    TrialRecord,
)
from adaptive_jailbreak.policies.bandit_policy import BanditPolicy


def _record(*, family: str, success: bool, refusal: float, structure: float, latency_s: float) -> TrialRecord:
    cfg = AdapterConfig(backend="mock")
    return TrialRecord(
        run_id="r",
        trial_idx=0,
        mode="restricted",
        generator=cfg,
        target=cfg,
        policy="bandit",
        candidate=PromptCandidate(prompt="p", family=family, metadata={}),
        generator_timing=Timings(latency_s=0.01),
        target_timing=Timings(latency_s=latency_s),
        response=ModelResponse(text="x"),
        judge=JudgeResult(
            mode="restricted",
            jailbreak_success=success,
            refusal_score=refusal,
            structure_score=structure,
        ),
        created_at_unix_s=0.0,
    )


def test_bandit_updates_stats_without_error():
    pol = BanditPolicy(seed=0, mode="restricted")
    state = type("S", (), {"history": [], "run_id": "r", "mode": "restricted", "budget": 1, "policy_name": "bandit"})()

    r1 = _record(family="modeA_json_refusal_probe", success=True, refusal=0.0, structure=1.0, latency_s=0.1)
    pol.observe(state, r1)
    r2 = _record(family="modeA_structure_only", success=False, refusal=1.0, structure=0.3, latency_s=1.0)
    pol.observe(state, r2)

