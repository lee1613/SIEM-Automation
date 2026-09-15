from case_file import finalize_answer


def _deleg(answer):
    return {"answer": f"FINAL ANSWER: {answer}", "status": "solved",
            "worker": "senior#1", "spl_used": [], "sourcetypes": [],
            "iterations": 3, "cap_hit": False}


def test_schema_b_value_is_used_verbatim_without_any_stripping():
    # v1.3 deleted the 'UF = 2059' -> '2059' label strip. It patched a symptom of
    # workers returning prose; schema B's `value` is its own field and cannot
    # carry a label, so a labelled string is now simply not a ledger candidate.
    delegs = [{"value": "2059", "answer": "", "status": "solved",
               "worker": "senior#1", "spl_used": [], "sourcetypes": []}]
    assert finalize_answer("2059", delegs) == "2059"
    # and an unmatched string is passed through untouched rather than mangled
    assert finalize_answer("UF = 2059", delegs) == "UF = 2059"


def test_structured_value_beats_prose_in_the_same_record():
    # A worker that called submit_finding AND wrote prose: the field wins, so a
    # sentence-mangled restatement can never displace the verbatim value.
    delegs = [{"value": "BSTOLL-L.froth.ly", "status": "solved",
               "answer": "FINAL ANSWER: BSTOLL-L", "worker": "senior#1",
               "spl_used": [], "sourcetypes": []}]
    assert finalize_answer("bstoll-l.froth.ly", delegs) == "BSTOLL-L.froth.ly"


def test_a_ledger_value_containing_equals_is_preserved():
    delegs = [_deleg("user=root")]
    assert finalize_answer("user=root", delegs) == "user=root"


def test_plain_value_snaps_case():
    delegs = [_deleg("NullWeb_Admin")]
    assert finalize_answer("nullweb_admin", delegs) == "NullWeb_Admin"


def test_no_label_no_ledger_unchanged():
    assert finalize_answer("mkraeusen", []) == "mkraeusen"


def test_empty_is_safe():
    assert finalize_answer("", []) == ""
