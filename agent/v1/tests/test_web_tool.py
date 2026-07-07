from unittest.mock import patch
import web_tool


SAMPLE_HTML = '''
<div class="result__snippet">Symantec rates Backdoor.PsEmpire severity: Medium.</div>
<div class="result__snippet">Second snippet about the threat.</div>
'''


def test_web_lookup_returns_snippets():
    with patch("web_tool._fetch", return_value=SAMPLE_HTML):
        out = web_tool.web_lookup.invoke({"query": "Backdoor.PsEmpire severity"})
    assert "Medium" in out


def test_web_lookup_network_failure_is_graceful():
    with patch("web_tool._fetch", side_effect=Exception("no network")):
        out = web_tool.web_lookup.invoke({"query": "anything"})
    assert "unavailable" in out.lower() or "no result" in out.lower()
    # must not raise
