from case_file import finalize_answer


def _deleg(answer):
    return {"answer": f"FINAL ANSWER: {answer}", "status": "solved",
            "worker": "senior#1", "spl_used": [], "sourcetypes": [],
            "iterations": 3, "cap_hit": False}


def test_strips_label_prefix():
    # Q331 regression: extractor kept 'UF = ' and it reached the scoreboard.
    assert finalize_answer("UF = 2059", []) == "2059"


def test_strip_then_snap_restores_ledger_form():
    delegs = [_deleg("1374")]
    assert finalize_answer("UF = 1374", delegs) == "1374"


def test_snap_wins_before_strip():
    # A verbatim ledger value containing '=' must never be stripped.
    delegs = [_deleg("user=root")]
    assert finalize_answer("user=root", delegs) == "user=root"


def test_plain_value_snaps_case():
    delegs = [_deleg("NullWeb_Admin")]
    assert finalize_answer("nullweb_admin", delegs) == "NullWeb_Admin"


def test_no_label_no_ledger_unchanged():
    assert finalize_answer("mkraeusen", []) == "mkraeusen"


def test_empty_is_safe():
    assert finalize_answer("", []) == ""
