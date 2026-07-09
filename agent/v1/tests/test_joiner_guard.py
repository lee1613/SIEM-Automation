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


def test_grounding_replan_increments_plan_round_only_once():
    """joiner_node's grounding-forced-replan branch must NOT increment
    plan_round itself — route_joiner sends it to planner_node, which does its
    own +1. Double-incrementing here burns 2 of 3 replan rounds per failure."""
    decision = decide_joiner_answer(
        "fabricated_value", {}, "question text",
        plan_round=1, max_rounds=3,
    )
    assert decision["action"] == "replan"
    # This test documents the contract joiner_node must follow: when
    # decision["action"] == "replan", the returned state dict's "plan_round"
    # must equal the CURRENT plan_round (unchanged), not plan_round + 1 —
    # planner_node is the sole incrementer for this path.


def test_decide_joiner_answer_grounds_against_prior_round_evidence():
    """A value proven in an earlier round and restated in a later round's
    FINAL ANSWER must still ground, using accumulated (not just current-round)
    evidence — this is what orchestrator.py's joiner_node must pass in."""
    # Simulates joiner_node merging ctx.q_delegations (prior rounds) into the
    # task_results dict passed to decide_joiner_answer.
    current_round_results = {1: {"answer": "checked an unrelated field", "status": "solved"}}
    prior_round_delegation = {"answer": "the MD5 is d41d8cd98f00b204e9800998ecf8427e"}
    combined = dict(current_round_results)
    combined["prior_0"] = prior_round_delegation

    decision = decide_joiner_answer(
        "d41d8cd98f00b204e9800998ecf8427e", combined, "question text",
        plan_round=2, max_rounds=3,
    )
    assert decision["action"] == "final"
