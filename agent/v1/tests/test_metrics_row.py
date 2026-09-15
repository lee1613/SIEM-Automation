from run_all_v1 import build_metrics_row, seed_resume_results, upsert_metrics_row


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


def test_grounded_uses_component_wise_check_for_list_answers():
    delegations = [
        {"answer": "Users seen: bstoll, btun, also splunk_access and web_admin.",
         "status": "solved", "cap_hit": False},
    ]
    row = build_metrics_row(
        qid="Q200", points=100, verdict="correct", earned=100,
        clean_answer="bstoll,btun,splunk_access,web_admin",
        delegations=delegations, stage_ms={}, usage_by_role={},
        question_text="",
    )
    assert row["grounded"] is True


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


# ── upsert_metrics_row: crash-then-resume dedupe (Issue 1) ────────────────────

def test_upsert_replaces_stale_row_for_same_qid():
    rows = [
        {"qid": "Q200", "verdict": "wrong", "grounded": False},
        {"qid": "Q301", "verdict": "correct", "grounded": True},
    ]
    upsert_metrics_row(rows, {"qid": "Q200", "verdict": "correct", "grounded": True})
    q200 = [m for m in rows if m["qid"] == "Q200"]
    assert len(q200) == 1                      # exactly one row — no duplicate
    assert q200[0]["verdict"] == "correct"     # and it is the NEW row
    assert len(rows) == 2                      # unrelated row untouched


def test_upsert_appends_new_qid():
    rows = [{"qid": "Q200", "verdict": "correct"}]
    upsert_metrics_row(rows, {"qid": "Q301", "verdict": "wrong"})
    assert [m["qid"] for m in rows] == ["Q200", "Q301"]


# ── seed_resume_results: old vs new summary schema (Issue 2) ──────────────────

def test_seed_resume_new_schema_reloads_from_questions_dir(tmp_path):
    import json
    qdir = tmp_path / "questions"
    qdir.mkdir()
    rec = {"id": "Q200", "sb_correct": True, "earned": 100}
    (qdir / "Q200.json").write_text(json.dumps(rec), encoding="utf-8")
    prior = {"index": [{"id": "Q200", "verdict": "correct", "earned": 100}]}
    results = seed_resume_results(prior, str(qdir))
    assert results == [rec]


def test_seed_resume_old_schema_falls_back_to_embedded_results(tmp_path):
    # run_1.0 / run_1.1 summaries: inline "results" array, no "index" key.
    prior = {"results": [{"id": "Q1", "sb_correct": False, "earned": 0}]}
    results = seed_resume_results(prior, str(tmp_path / "questions"))
    assert results == [{"id": "Q1", "sb_correct": False, "earned": 0}]


def test_seed_resume_new_schema_skips_missing_question_files(tmp_path):
    qdir = tmp_path / "questions"
    qdir.mkdir()
    prior = {"index": [{"id": "Q999", "verdict": "wrong", "earned": 0}]}
    assert seed_resume_results(prior, str(qdir)) == []


def test_worker_latency_is_broken_out_per_worker_and_summed():
    """worker_total exceeding the sh stage is the readout that the fan-out
    actually overlapped — so both the per-worker map and its sum must survive."""
    row = build_metrics_row(
        qid="Q216", points=1000, verdict="wrong", earned=0, clean_answer="7070",
        delegations=[
            {"worker": "senior#1", "status": "failed", "answer": "", "duration_s": 300.0},
            {"worker": "senior#2", "status": "solved", "answer": "7070", "duration_s": 250.5},
            {"worker": "senior#3", "status": "failed", "answer": "", "duration_s": 120.0},
        ],
        stage_ms={"sh": 400_000, "extract": 1000},
        usage_by_role={"senior": {"estimated_usd": 1.9}},
    )
    assert row["latency_s"]["workers"] == {
        "senior#1": 300.0, "senior#2": 250.5, "senior#3": 120.0}
    assert row["latency_s"]["worker_total"] == 670.5
    # 670.5s of worker time inside a 400s SH stage -> the fan-out overlapped.
    assert row["latency_s"]["worker_total"] > row["latency_s"]["sh"]
