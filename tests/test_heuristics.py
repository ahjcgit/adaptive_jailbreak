from adaptive_jailbreak.judges.heuristics import refusal_score, structure_score


def test_refusal_score_basic():
    assert refusal_score("REFUSE") >= 0.75
    assert refusal_score("Sure, here you go.") == 0.0


def test_structure_score_json():
    assert structure_score("{\"ok\": true}") == 1.0
    assert structure_score("plain text") <= 0.3

