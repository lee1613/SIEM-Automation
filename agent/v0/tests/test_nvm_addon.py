"""Is the Cisco NVM add-on actually doing anything to the BOTSv3 NVM feed?

Integration check - needs a live Splunk. Skipped unless SIEM_INTEGRATION=1, so
the unit suite stays runnable offline:

    SIEM_INTEGRATION=1 python -m pytest agent/v0/tests/test_nvm_addon.py -v

Installing a TA is not the same as it taking effect. A TA's extractions are
keyed to a SOURCETYPE, and sourcetype is assigned at INDEX time - so dropping
TA-Cisco-NVM into etc/apps does nothing for events that were already indexed
under a different sourcetype. In this index the NVM feed sits at
`sourcetype=syslog, source=cisconvmflowdata`, while the TA binds to
`[cisco:nvm:flowdata]`. These tests are what tells the two states apart.

Note what the TA does NOT provide: there is no `duration` field anywhere in
its props.conf - only FIELDALIASes (fss AS flow_start_sec, fes AS
flow_end_sec) and CIM EVALs. So no amount of re-indexing makes a duration
appear; it stays `fes - fss`, computed by hand.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SIEM_INTEGRATION") != "1",
    reason="needs a live Splunk; set SIEM_INTEGRATION=1 to run")

NVM_SOURCE = "cisconvmflowdata"
# The sourcetype TA-Cisco-NVM's flow stanza is keyed to.
TA_SOURCETYPE = "cisco:nvm:flowdata"


@pytest.fixture(scope="module")
def splunk():
    from dotenv import load_dotenv
    from splunk_client import SplunkClient
    here = os.path.dirname
    agent_dir = here(here(here(os.path.abspath(__file__))))
    load_dotenv(os.path.join(agent_dir, ".env"))
    if not os.getenv("SPLUNK_PASS"):
        pytest.skip("SPLUNK_PASS not set")
    try:
        return SplunkClient(os.getenv("SPLUNK_HOST", "https://localhost:8089"),
                            os.getenv("SPLUNK_USER", "admin"),
                            os.getenv("SPLUNK_PASS"))
    except Exception as exc:
        pytest.skip(f"Splunk unreachable: {exc}")


def _rows(splunk, spl, n=100):
    return splunk.search(spl, earliest="0", max_results=n).get("results", [])


# ── is the add-on reaching the data at all? ────────────────────────────────────

def test_the_nvm_feed_carries_the_sourcetype_the_ta_binds_to(splunk):
    """The single thing that decides whether the add-on is live.

    FAILING HERE means the TA is installed but inert. Sourcetype is set at
    index time, so re-typing the feed needs one of:
      - re-index the NVM data with sourcetype=cisco:nvm:flowdata, or
      - bind the extractions to the source instead, in
        etc/apps/TA-Cisco-NVM/local/props.conf:
            [source::...cisconvmflowdata]
            sourcetype = cisco:nvm:flowdata
      - or copy the [cisco:nvm:flowdata] stanza's EXTRACT/FIELDALIAS/EVAL
        lines under a [syslog] stanza (blunt - it would apply to every other
        syslog feed in the index too).
    """
    rows = _rows(splunk, f"index=botsv3 source={NVM_SOURCE} | stats count by sourcetype")
    assert rows, f"no events at source={NVM_SOURCE}"
    types = {r["sourcetype"] for r in rows}
    assert TA_SOURCETYPE in types, (
        f"NVM feed is typed {sorted(types)}, not {TA_SOURCETYPE!r} - "
        "TA-Cisco-NVM is installed but does not apply to these events")


def test_the_tas_field_aliases_resolve(splunk):
    """A consequence of the above, asserted separately so a failure says which
    layer broke: the sourcetype is right but the aliases still are not."""
    rows = _rows(splunk, f"index=botsv3 source={NVM_SOURCE} | head 1 "
                         "| table fss flow_start_sec fes flow_end_sec sa src_ip dh dest_hostname", 1)
    assert rows, "no NVM events"
    r = rows[0]
    assert r.get("fss"), "raw field fss missing - the feed itself is wrong"
    for raw, alias in (("fss", "flow_start_sec"), ("fes", "flow_end_sec"),
                       ("sa", "src_ip"), ("dh", "dest_hostname")):
        assert r.get(alias), (
            f"alias {alias} (from {raw}) does not resolve - "
            "TA-Cisco-NVM's FIELDALIASes are not being applied")


# ── the trap that cost Q216, independent of the add-on ────────────────────────

def test_fst_and_fet_are_display_strings_not_epochs(splunk):
    """`fst`/`fet` are human-readable ("Mon Aug 20 10:47:05 2018"); the epoch
    pair is `fss`/`fes`. Splunk returns NULL for arithmetic on the strings -
    silently, with no error - which is how two v0.3 workers that were on the
    correct feed both came back with an empty value.

    This is a property of the data, not of the add-on, so it holds either way.
    """
    rows = _rows(splunk, f"index=botsv3 source={NVM_SOURCE} | head 1 "
                         "| eval bad=fet-fst, good=fes-fss | table fst fss bad good", 1)
    assert rows, "no NVM events"
    r = rows[0]
    assert not r.get("bad"), (
        "fet-fst now yields a number - the fields changed shape, "
        "so the Q216 analysis in docs/future_work.md #5 needs redoing")
    assert r.get("good"), "fes-fss must be computable; it is the only duration source"
    assert not r["fst"].isdigit(), f"fst should be a display string, got {r['fst']!r}"


def test_the_ta_provides_no_duration_field(splunk):
    """Recorded so nobody re-runs the "install the TA and duration appears"
    hypothesis. It does not exist in props.conf, and it does not exist here."""
    # `| table duration` alone returns ZERO rows when the field is absent, which
    # reads as "query failed" rather than "field missing". Anchor on a field
    # that always exists so an empty result means a broken query, nothing else.
    rows = _rows(splunk, f"index=botsv3 source={NVM_SOURCE} | head 1 "
                         "| table fss duration", 1)
    assert rows, "NVM feed returned nothing - the query, not the field, is wrong"
    assert rows[0].get("fss"), "anchor field fss missing"
    assert not rows[0].get("duration"), (
        "a `duration` field now exists - re-check Q216 against it")


# ── what the mining traffic actually sums to ──────────────────────────────────

def test_q216_ground_truth_is_still_not_1666(splunk):
    """Q216 wants seconds of Monero mining, official answer 1666.

    The closest reachable value is 1660: sum(fes-fss) over
    192.168.70.186 -> 45.77.53.176:443 where ppn=powershell.exe. Brute-forced
    across groupings by sa/da/dp/pn/ppn/udid/liuidp with sum, span and interval
    union, nothing else lands on 1666 (the one exact hit in the whole feed is
    SearchUI.exe -> 204.79.197.254, which is Bing).

    If this test ever fails because the number moved, the add-on or a re-index
    changed the field semantics and Q216 is worth re-attempting.
    """
    rows = _rows(splunk,
                 "index=botsv3 source=cisconvmflowdata sa=192.168.70.186 "
                 "da=45.77.53.176 dp=443 ppn=powershell.exe "
                 "| eval dur=fes-fss | stats sum(dur) as total count as n")
    assert rows, "the mining conversation is missing from the feed"
    assert int(rows[0]["total"]) == 1660, f"expected 1660, got {rows[0]['total']}"
    assert int(rows[0]["n"]) == 1821
