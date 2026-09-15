"""The source axis must survive from tool argument to emitted SPL.

Q216 was lost because 78,459 Cisco NVM flow events sit under sourcetype=syslog
and are addressable only as source="cisconvmflowdata" — a filter no tool could
express. These assert the plumbing exists end to end.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from splunk_agent import make_tools
from splunk_client import _scope


class FakeSplunk:
    """Captures the SPL each helper builds, without touching Splunk."""
    def __init__(self):
        self.queries = []

    def search(self, query, earliest="0", latest="now", max_results=50):
        self.queries.append(query)
        return {"results": [], "fields": []}

    # real implementations, so the SPL under test is the shipped SPL
    from splunk_client import SplunkClient
    get_sources          = SplunkClient.get_sources
    get_sourcetype_fields = SplunkClient.get_sourcetype_fields
    get_field_values     = SplunkClient.get_field_values
    sample_events        = SplunkClient.sample_events


def _tools():
    fake = FakeSplunk()
    return fake, {t.name: t for t in make_tools(fake)}


def test_scope_builds_either_axis_or_both():
    assert _scope("syslog", "") == ' sourcetype="syslog"'
    assert _scope("", "cisconvmflowdata") == ' source="cisconvmflowdata"'
    assert _scope("syslog", "cisconvmflowdata") == \
        ' sourcetype="syslog" source="cisconvmflowdata"'
    assert _scope("", "") == ""


def test_get_sources_pairs_source_with_sourcetype():
    fake, tools = _tools()
    assert "get_sources" in tools, "get_sources must be registered as a tool"
    tools["get_sources"].invoke({"keyword": "cisco"})
    spl = fake.queries[-1]
    # the pivot query: both axes in the group-by, keyword-filtered
    assert "stats count by source, sourcetype" in spl
    assert "*cisco*" in spl


def test_get_sources_lists_feeds_hiding_under_one_sourcetype():
    fake, tools = _tools()
    tools["get_sources"].invoke({"sourcetype": "syslog"})
    assert 'sourcetype="syslog"' in fake.queries[-1]


def test_fieldsummary_accepts_a_source_with_no_sourcetype():
    fake, tools = _tools()
    tools["get_sourcetype_fields"].invoke({"source": "cisconvmflowdata"})
    spl = fake.queries[-1]
    assert 'source="cisconvmflowdata"' in spl
    assert "sourcetype=" not in spl      # must not fabricate a sourcetype filter
    assert "fieldsummary" in spl


def test_sample_and_field_values_reach_the_source_axis():
    fake, tools = _tools()
    tools["sample_events"].invoke({"source": "cisconvmflowdata"})
    assert 'source="cisconvmflowdata"' in fake.queries[-1]
    tools["get_field_values"].invoke({"field": "fss", "source": "cisconvmflowdata"})
    assert 'source="cisconvmflowdata"' in fake.queries[-1]


def test_prompt_no_longer_forbids_a_source_only_search():
    import splunk_agent
    assert "Never run a search without a sourcetype filter" not in splunk_agent.SYSTEM_PROMPT
    assert "get_sources" in splunk_agent.SYSTEM_PROMPT
