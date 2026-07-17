from adjudicator import majority_answer


def _rec(value_line, status):
    return {"answer": value_line, "status": status, "spl_used": [],
            "sourcetypes": [], "iterations": 3, "cap_hit": False}


def test_two_of_three_majority_wins():
    recs = [_rec("FINAL ANSWER: 2.94", "solved"),
            _rec("PARTIAL ANSWER: 2.94", "partial"),
            _rec("FINAL ANSWER: 2.9348", "solved")]
    win = majority_answer(recs)
    assert win is recs[0]          # 2.94 majority; solved beats partial


def test_all_distinct_returns_none():
    recs = [_rec("FINAL ANSWER: 1", "solved"),
            _rec("FINAL ANSWER: 2", "solved"),
            _rec("FINAL ANSWER: 3", "solved")]
    assert majority_answer(recs) is None


def test_votes_are_case_and_space_insensitive():
    recs = [_rec("FINAL ANSWER: BSTOLL-L", "partial"),
            _rec("FINAL ANSWER:  bstoll-l ", "solved"),
            _rec("FINAL ANSWER: FYODOR-L", "solved")]
    win = majority_answer(recs)
    assert win is recs[1]          # majority value, solved holder wins


def test_records_without_answer_tag_dont_vote():
    recs = [_rec("ESCALATE: nothing found", "too_big"),
            _rec("ESCALATE: nope", "too_big"),
            _rec("FINAL ANSWER: 42", "solved")]
    assert majority_answer(recs) is None   # 1 vote is not a majority
