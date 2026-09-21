"""Regressions for the two defects the final review of spec 1 found.

Both were invisible to the rest of the suite because every existing test builds
the ledger by hand or hand-feeds the worker's result dict.
"""

import inspect

import splunk_subagent
from finding import empty_finding, parse_finding
from premise import PremiseDraft, PremiseLedger, PremiseUpdate


def test_the_worker_returns_the_three_ledger_fields():
    """C1: `_run` copied named keys out of `finding` and dropped these three, so
    `SeniorSession.work`'s `result.get(...)` saw None on every real round and no
    senior premise could ever reach the ledger. The suite stayed green because the
    session tests stub the pool."""
    src = inspect.getsource(splunk_subagent.SplunkWorkerPool._run)
    for key in ("new_premises", "premise_updates", "open_questions"):
        assert f'"{key}"' in src, f"_run drops {key} on the way back to the session"

    # Both finding paths have to supply them or the copy above raises KeyError:
    # the structured one (submit_finding was called) and the prose fallback.
    for finding in (empty_finding(), parse_finding([], "prose answer")):
        for key in ("new_premises", "premise_updates", "open_questions"):
            assert key in finding


def test_a_circular_quote_is_refused_by_apply_not_only_by_the_gate():
    """C2: the runner writes the ledger BEFORE the gates (so SH can cite an id it
    just filed) and a rejected turn is not rolled back. With the circular check
    living only in `sh_update_violations`, the premise flipped to VERIFIED, the
    turn was rejected, and SH re-issued it without the offending update - leaving
    the laundered VERIFIED standing. This is the v1.4.2 Q216 loss exactly."""
    ledger = PremiseLedger()
    p = ledger.add([PremiseDraft(text="the 3333 flow is a download", kind="selection",
                             load_bearing=True, rival="the coinhive HTTPS flows")],
                   author="s1", round_n=1)[0]

    notes = ledger.apply(
        [PremiseUpdate(id=p.id, status="VERIFIED",
                       quote="the attribution was established by SH outside this feed",
                       evidence="SH settled it")],
        author="sh", corpus=["the attribution was established by SH outside this feed"],
        round_n=2)

    assert ledger.premises[p.id].status == "UNVERIFIED"
    assert notes and "cites SH as the authority" in notes[0]


def test_a_genuine_quote_still_settles_the_premise():
    """The guard above must not swallow the honest path."""
    ledger = PremiseLedger()
    p = ledger.add([PremiseDraft(text="dest_port 3333 carries 5.7MB inbound",
                             kind="selection", load_bearing=True,
                             rival="the coinhive HTTPS flows")],
                   author="s1", round_n=1)[0]

    notes = ledger.apply(
        [PremiseUpdate(id=p.id, status="VERIFIED",
                       quote="ibc=5782875 obc=177 dest_port=3333",
                       evidence="inbound bytes dwarf outbound, so it is a download")],
        author="s1", corpus=['{"results": [{"ibc": "5782875", "obc": "177", '
                             '"dest_port": "3333"}]}'],
        round_n=2)

    assert notes == []
    assert ledger.premises[p.id].status == "VERIFIED"
