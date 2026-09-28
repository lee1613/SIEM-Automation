from unittest.mock import MagicMock

import splunk_agent


def test_get_raw_events_registered_and_bounded():
    fake = MagicMock()
    fake.sample_events.return_value = {"results": [{"_raw": "x"} for _ in range(50)]}
    tools = {t.name: t for t in splunk_agent.make_tools(fake)}
    assert "get_raw_events" in tools
    # limit is clamped to <= 20
    tools["get_raw_events"].invoke({"sourcetype": "stream:smtp",
                                    "keyword": "financial", "limit": 999})
    # the clamp happens before the splunk call; assert splunk got count<=20
    assert True  # presence + no exception is the contract; clamp asserted below


def test_get_raw_events_clamps_limit(monkeypatch):
    fake = MagicMock()
    fake.sample_events.return_value = {"results": []}
    tools = {t.name: t for t in splunk_agent.make_tools(fake)}
    tools["get_raw_events"].invoke({"sourcetype": "stream:smtp", "limit": 999})
    call = fake.sample_events.call_args
    passed = call.kwargs.get("count")
    assert passed is not None and passed <= 20
