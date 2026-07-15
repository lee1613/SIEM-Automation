from case_file import build_ledger, render_ledger, snap_to_ledger


def test_render_contains_verbatim_values_and_contract():
    ledger = build_ledger([{"answer": "FINAL ANSWER: 1367.875", "status": "solved",
                            "worker": "senior#2", "spl_used": ["| stats perc25(x)"],
                            "sourcetypes": [], "iterations": 5, "cap_hit": False}])
    r = render_ledger(ledger)
    assert "1367.875" in r and "character-for-character" in r


def test_snap_pipeline_restores_worker_form():
    delegs = [{"answer": "FINAL ANSWER: nullweb_admin", "status": "solved",
               "worker": "senior#1", "spl_used": [], "sourcetypes": [],
               "iterations": 2, "cap_hit": False}]
    ledger = build_ledger(delegs)
    assert snap_to_ledger("NULLWEB_ADMIN", ledger) == "nullweb_admin"


def test_empty_delegations_render_empty():
    assert render_ledger(build_ledger([])) == ""
