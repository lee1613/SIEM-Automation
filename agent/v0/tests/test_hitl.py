
import httpx
import pytest
import splunk_agent as agent_mod
from hitl import RunPaused
from llm_errors import _ErrorBodyTransport
from splunk_subagent import SplunkWorkerPool


class _Fake(httpx.BaseTransport):
    def __init__(self, body): self.body = body
    def handle_request(self, request): return httpx.Response(200, json=self.body, request=request)


def _through(body):
    req = httpx.Request("POST", "https://api.featherless.ai/v1/chat/completions")
    return _ErrorBodyTransport(_Fake(body)).handle_request(req).status_code


def test_error_body_on_200_is_rewritten_so_the_sdk_retries():
    # Featherless reports its own 5xx as HTTP 200 + error body. A 200 is a
    # success to the SDK, so max_retries never fires. Rewrite it to a real 500.
    assert _through({"error": {"message": "boom", "type": "server_error"}}) == 500


def test_valid_completion_is_untouched():
    assert _through({"id": "x", "choices": [{"message": {"content": "hi"}}]}) == 200


def test_completion_with_a_soft_error_field_is_not_hijacked():
    # Stricter than langchain's check (base.py:1771), which raises on any truthy
    # "error" key: a usable completion must survive even if a warning rides along.
    assert _through({"choices": [{"message": {"content": "hi"}}],
                     "error": {"message": "soft warning"}}) == 200


def test_non_json_body_is_passed_through():
    class _Text(httpx.BaseTransport):
        def handle_request(self, request):
            return httpx.Response(200, text="not json", request=request)
    req = httpx.Request("POST", "https://x/v1/chat/completions")
    assert _ErrorBodyTransport(_Text()).handle_request(req).status_code == 200


def test_api_failure_is_tagged_api_failed_not_too_big(monkeypatch):
    # The whole point: a crashed worker's text starts with "ESCALATE:" exactly
    # like an honest give-up, so _classify() collapses both onto "too_big" -
    # which tells SH to DECOMPOSE and dispatch more workers at a dead provider.
    def _boom(*a, **k):
        raise RuntimeError("provider exploded")
    monkeypatch.setattr(agent_mod, "run_agent_traced", _boom)

    pool = object.__new__(SplunkWorkerPool)          # skip graph construction
    pool.senior_base_url = "https://api.featherless.ai/v1"
    pool.tracker = None
    result = pool._run("senior", object(), "zai-org/GLM-5.3", "find it", "Q216", 5)

    assert result["status"] == "api_failed"
    assert result["provider"] == "api.featherless.ai"
    assert "RuntimeError" in result["answer"]


def test_run_sh_lets_a_pause_through_instead_of_swallowing_it():
    # Regression: RunPaused subclasses Exception, so run_sh's blanket guard
    # caught it and returned the empty sentinel - the run then carried on past
    # the exact failure a human was being asked to decide about, and the pause
    # never reached main(). A pause is not a crash.
    from orchestrator import run_sh

    class _Paused:
        def invoke(self, *a, **k):
            raise RunPaused("/tmp/decision_request.json", "api outage on Q216")

    with pytest.raises(RunPaused):
        run_sh(_Paused(), "solve Q216", "sh_run", qid="Q216")


def test_run_sh_resolves_an_interrupt_instead_of_returning_an_empty_answer(tmp_path, monkeypatch):
    # The executor subgraph's hitl node interrupts rather than raising, so
    # invoke() RETURNS with __interrupt__ set. Ignoring it would hand back ""
    # and silently continue past the failure a human was asked about.
    from orchestrator import run_sh

    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)

    class _Interrupting:
        def invoke(self, *a, **k):
            return {"__interrupt__": [type("I", (), {"value": {
                "reason": "api_failed", "qids": [2],
                "provider": "api.featherless.ai", "error": "boom",
                "options": ["retry", "skip", "abort"]}})()]}

    with pytest.raises(RunPaused):
        run_sh(_Interrupting(), "solve Q216", "sh", qid="Q216", run_dir=str(tmp_path))


def test_worker_outage_reaches_the_graph_interrupt():
    # Worker API outages pause inside the executor subgraph's own side-effect-free
    # hitl node, never in a node that makes an LLM call - interrupt() replays its
    # own node, which would re-issue that call each time a human answers.
    # v0.3 removed the SH-level sh_hitl node with the verifier and adjudicator
    # that were its only callers; the executor's hitl is now the single pause point.
    from orchestrator import DelegationContext, build_sh_agent_compiler

    ctx = DelegationContext(pool=None, logger=None)
    graph, _ = build_sh_agent_compiler("sk-fake-key", "gpt-5.4", ctx)
    g = graph.get_graph(xray=True)
    hitl_nodes = [n for n in g.nodes if "hitl" in n]
    assert hitl_nodes, sorted(g.nodes)
