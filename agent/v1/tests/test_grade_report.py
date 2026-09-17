from grade_report import summarize

GRADES = [
    {"senior_id": "s1", "round": 1, "r1": "PASS", "r2_sh": "PASS",
     "r2_effective": "PASS", "r3": "WEAK", "route": "COMMAND",
     "decision": "continue", "basis": "", "novel_spl_count": 3},
    {"senior_id": "s1", "round": 2, "r1": "PASS", "r2_sh": "PASS",
     "r2_effective": "FAIL", "r3": "WEAK", "route": "COMMAND",
     "decision": "continue", "basis": "", "novel_spl_count": 0},
    {"senior_id": "s1", "round": 3, "r1": "WEAK", "r2_sh": "WEAK",
     "r2_effective": "WEAK", "r3": "PASS", "route": "ANSWER",
     "decision": "", "basis": "", "novel_spl_count": 2},
    {"senior_id": "s2", "round": 1, "r1": "PASS", "r2_sh": "FAIL",
     "r2_effective": "FAIL", "r3": "FAIL", "route": "CRITIC",
     "decision": "", "basis": "shape_mismatch", "novel_spl_count": 1},
]


def test_grade_distribution_counts_every_dimension():
    s = summarize(GRADES)
    assert s["distribution"]["r1"] == {"PASS": 3, "WEAK": 1, "FAIL": 0}
    assert s["distribution"]["r2_effective"] == {"PASS": 1, "WEAK": 1, "FAIL": 2}


def test_an_all_pass_column_is_flagged_as_an_inert_rubric():
    inert = [{**g, "r1": "PASS"} for g in GRADES]
    assert "r1" in summarize(inert)["inert_dimensions"]
    assert "r1" not in summarize(GRADES)["inert_dimensions"]


def test_continue_rate_is_reported_per_r2_grade():
    s = summarize(GRADES)
    assert s["continue_rate_by_r2"]["PASS"] == 1.0     # 1 of 1
    assert s["continue_rate_by_r2"]["FAIL"] == 0.5     # 1 of 2 (s1 r2, not s2)


def test_contradictions_are_counted():
    s = summarize(GRADES)
    assert s["contradictions"]["continue_after_fail"] == 1
    assert s["contradictions"]["answer_from_weak_scope"] == 1


def test_critics_are_counted_by_basis():
    assert summarize(GRADES)["critics_by_basis"]["shape_mismatch"] == 1


def test_novel_spl_distribution_answers_the_thrash_question():
    s = summarize(GRADES)
    assert s["novel_spl"]["zeros"] == 1
    assert s["novel_spl"]["rounds"] == 4


def test_an_empty_run_summarises_without_crashing():
    s = summarize([])
    assert s["novel_spl"]["rounds"] == 0
    assert s["continue_rate_by_r2"] == {}
