from orchestrator import decide_joiner_answer


def test_grounded_answer_is_kept():
    tr = {1: {"status": "solved", "answer": "FINAL ANSWER: 199.66.91.253"}}
    out = decide_joiner_answer("199.66.91.253", tr, "C2 IP?", plan_round=1, max_rounds=3)
    assert out["action"] == "final"
    assert out["answer"] == "199.66.91.253"


def test_ungrounded_with_rounds_left_replans():
    tr = {1: {"status": "partial", "answer": "candidates: /images/index1.jpeg"}}
    out = decide_joiner_answer("taedonggang.jpeg", tr, "defacement image",
                               plan_round=1, max_rounds=3)
    assert out["action"] == "replan"
    assert "not found" in out["reason"].lower()


def test_ungrounded_no_rounds_left_falls_back_to_best_candidate():
    tr = {1: {"status": "solved", "answer": "FINAL ANSWER: /images/index1.jpeg"}}
    out = decide_joiner_answer("taedonggang.jpeg", tr, "defacement image",
                               plan_round=3, max_rounds=3)
    assert out["action"] == "final"
    assert "/images/index1.jpeg" in out["answer"]


def test_ungrounded_no_candidate_keeps_original():
    out = decide_joiner_answer("glacier", {1: {"status": "failed", "answer": ""}},
                               "iam resource", plan_round=3, max_rounds=3)
    assert out["action"] == "final"
    assert out["answer"] == "glacier"   # nothing better to offer
