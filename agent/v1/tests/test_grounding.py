from grounding import is_grounded, best_candidate


def test_grounded_when_answer_in_a_task_result():
    tr = {1: {"status": "solved", "answer": "FINAL ANSWER: 199.66.91.253"}}
    assert is_grounded("199.66.91.253", tr, "What is the C2 IP?") is True


def test_grounded_is_case_insensitive():
    tr = {1: {"status": "solved", "answer": "found host BSTOLL-L.froth.ly"}}
    assert is_grounded("bstoll-l.froth.ly", tr, "") is True


def test_grounded_when_answer_in_question_text():
    # some answers legitimately echo the question (e.g. a term to confirm)
    assert is_grounded("column chart", {}, "Which chart type: column chart or bar?") is True


def test_ungrounded_when_answer_appears_nowhere():
    tr = {1: {"status": "partial", "answer": "candidates: /images/index1.jpeg"}}
    assert is_grounded("taedonggang.jpeg", tr, "Name the defacement image") is False


def test_empty_answer_is_ungrounded():
    assert is_grounded("", {1: {"answer": "x"}}, "q") is False


def test_best_candidate_prefers_solved_over_partial():
    tr = {
        1: {"status": "partial", "answer": "maybe FYODOR-L"},
        2: {"status": "solved", "answer": "FINAL ANSWER: BSTOLL-L"},
    }
    # returns the answer text of the highest-confidence non-empty task
    assert "BSTOLL-L" in best_candidate(tr)


def test_best_candidate_none_when_all_empty():
    assert best_candidate({1: {"status": "failed", "answer": ""}}) is None


# ── run_1.2 Q200 regression: comma-joined list answers ────────────────────────

def test_comma_list_grounded_when_every_part_in_evidence():
    tr = {1: {"answer": "Users seen: **bstoll** (615 events), **btun** (73), "
                        "also splunk_access and web_admin appear.",
              "status": "solved"}}
    assert is_grounded("bstoll,btun,splunk_access,web_admin", tr)


def test_comma_list_ungrounded_when_any_part_fabricated():
    tr = {1: {"answer": "Users seen: bstoll, btun.", "status": "solved"}}
    assert not is_grounded("bstoll,btun,ghost_user", tr)


def test_comma_list_parts_may_span_multiple_workers():
    tr = {1: {"answer": "found bstoll", "status": "partial"},
          2: {"answer": "found btun", "status": "partial"}}
    assert is_grounded("bstoll,btun", tr)
