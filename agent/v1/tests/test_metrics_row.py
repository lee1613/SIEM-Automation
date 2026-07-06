from run_all_v1 import build_metrics_row


def test_metrics_row_flags_ungrounded_and_verdict():
    row = build_metrics_row(
        qid="Q225", points=500, verdict="wrong", earned=0,
        clean_answer="taedonggang.jpeg",
        delegations=[
            {"status": "partial", "answer": "candidates: /images/index1.jpeg",
             "iterations": 9, "cap_hit": False},
            {"status": "partial", "answer": "no result", "iterations": 4, "cap_hit": False},
        ],
        stage_ms={"plan": 12000, "exec": 900000, "join": 30000, "extract": 2000},
        usage_by_role={"sh": {"estimated_usd": 0.002}, "senior": {"estimated_usd": 0.04}},
    )
    assert row["qid"] == "Q225"
    assert row["verdict"] == "wrong"
    assert row["delegations"] == 2
    assert row["statuses"] == ["partial", "partial"]
    assert row["cap_hits"] == 0
    # "taedonggang.jpeg" never appears verbatim in any worker answer -> ungrounded
    assert row["grounded"] is False
    assert row["latency_s"]["total"] == round((12000+900000+30000+2000)/1000, 1)


def test_metrics_row_grounded_true_when_answer_in_worker_text():
    row = build_metrics_row(
        qid="Q301", points=100, verdict="correct", earned=100,
        clean_answer="199.66.91.253",
        delegations=[{"status": "solved", "answer": "FINAL ANSWER: 199.66.91.253",
                      "iterations": 6, "cap_hit": False}],
        stage_ms={"plan": 5000, "exec": 60000, "join": 8000, "extract": 1000},
        usage_by_role={},
    )
    assert row["grounded"] is True
