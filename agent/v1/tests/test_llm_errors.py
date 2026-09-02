import httpx
import openai
import pytest
from llm_errors import describe_llm_error, provider_of
from orchestrator import run_sh


def _rate_limit():
    resp = httpx.Response(429, request=httpx.Request("POST", "https://x/v1"),
                          json={"error": {"message": "out of credits"}})
    return openai.RateLimitError("out of credits", response=resp, body=None)


def test_provider_defaults_to_openai_when_no_base_url():
    assert provider_of(None) == "api.openai.com"
    assert provider_of("https://integrate.api.nvidia.com/v1") == "integrate.api.nvidia.com"


def test_description_names_type_status_component_and_provider():
    # The whole point: str(exc) alone prints only the body, so a 429 and a 500
    # read identically in the logs. All four facts must be present.
    line = describe_llm_error(_rate_limit(), "Senior-3-Q204",
                              "https://api.vultrinference.com/v1")
    assert "RateLimitError" in line
    assert "HTTP 429" in line
    assert "Senior-3-Q204" in line
    assert "api.vultrinference.com" in line


def test_description_omits_status_for_transport_errors():
    line = describe_llm_error(
        openai.APITimeoutError(request=httpx.Request("POST", "https://x")), "SH")
    assert "APITimeoutError" in line and "HTTP" not in line


class _DeadGraph:
    """Stands in for the SH graph when the provider is down."""
    def invoke(self, *_a, **_k):
        raise _rate_limit()


def test_run_sh_returns_empty_sentinel_instead_of_killing_the_run(capsys):
    # Regression: run_sh was the only LLM path with no exception guard, so one
    # bad SH turn took the whole multi-hour run down.
    answer, state = run_sh(_DeadGraph(), "solve Q204", "sh_run", qid="Q204")
    assert answer == ""          # sentinel -> caller falls back to best worker answer
    assert state == {}
    out = capsys.readouterr().out
    assert "RateLimitError" in out and "HTTP 429" in out   # failed loudly, not silently


def test_run_sh_still_returns_a_real_answer_when_the_graph_works():
    class _OK:
        def invoke(self, *_a, **_k):
            return {"final_answer": "cloudtrail", "messages": []}
    assert run_sh(_OK(), "q", "t", qid="Q204")[0] == "cloudtrail"
