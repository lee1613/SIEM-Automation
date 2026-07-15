from case_file import extract_candidate, build_ledger, snap_to_ledger


def _deleg(answer, status="solved", spl=None, worker="senior#1"):
    return {"answer": answer, "status": status, "worker": worker,
            "spl_used": spl or [], "sourcetypes": [], "iterations": 3,
            "cap_hit": False}


def test_extract_final_answer_value_verbatim():
    d = _deleg("Ran stats.\nFINAL ANSWER: BSTOLL-L.froth.ly\nSPL: search ...",
               spl=["search index=botsv3 | stats count by host"])
    c = extract_candidate(d)
    assert c["value"] == "BSTOLL-L.froth.ly"
    assert c["status"] == "solved"
    assert c["spl"] == ["search index=botsv3 | stats count by host"]


def test_extract_partial_answer_value():
    c = extract_candidate(_deleg("PARTIAL ANSWER: nullweb_admin\nUNCERTAINTY: ...",
                                 status="partial"))
    assert c["value"] == "nullweb_admin"


def test_extract_none_when_no_tag():
    assert extract_candidate(_deleg("ESCALATE: nothing found", status="too_big")) is None
    assert extract_candidate(_deleg("")) is None


def test_build_ledger_dedupes_case_insensitively_keeps_first_form():
    ledger = build_ledger([_deleg("FINAL ANSWER: NullWeb_Admin"),
                           _deleg("FINAL ANSWER: nullweb_admin"),
                           _deleg("FINAL ANSWER: 1367.875", status="partial")])
    assert [c["value"] for c in ledger] == ["NullWeb_Admin", "1367.875"]


def test_snap_restores_verbatim_ledger_form():
    ledger = build_ledger([_deleg("FINAL ANSWER: BSTOLL-L.froth.ly")])
    assert snap_to_ledger("bstoll-l.froth.ly", ledger) == "BSTOLL-L.froth.ly"


def test_snap_never_changes_a_different_value():
    ledger = build_ledger([_deleg("FINAL ANSWER: BSTOLL-L.froth.ly")])
    # A truncation is a DIFFERENT pick, not a casing slip — snap must not "fix" it.
    assert snap_to_ledger("BSTOLL-L", ledger) == "BSTOLL-L"
    assert snap_to_ledger("mkraeusen", ledger) == "mkraeusen"
