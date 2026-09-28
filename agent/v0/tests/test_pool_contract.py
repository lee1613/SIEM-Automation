"""The pool must expose exactly what SplunkClient does, with kwargs intact.

This file exists because of a live failure. `SplunkClient` was widened to the
`source` axis; `SplunkConnectionPool` hand-mirrored four of its methods and was
not. Workers hold the POOL, so every source-scoped discovery call they made came
back as:

    'SplunkConnectionPool' object has no attribute 'get_sources'
    SplunkConnectionPool.get_sourcetype_fields() got an unexpected keyword
        argument 'source'

and the run degraded on every worker while `test_source_axis.py` stayed green -
because it exercised SplunkClient directly and never touched the layer the agent
actually holds.

So these tests assert the CONTRACT BETWEEN THE LAYERS, not the behaviour of
either one.
"""

import inspect

import pytest
from splunk_client import SplunkClient
from splunk_pool import SplunkConnectionPool

# Every SplunkClient method the agent's tools call. Explicit on purpose: adding a
# tool that reaches a new client method should force a conscious update here.
TOOL_FACING_METHODS = ("search", "get_sources", "get_sourcetype_fields",
                       "get_field_values", "sample_events")


class _FakeClient:
    """Records the call it received, verbatim."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def _rec(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return {"results": [], "_meta": {}}
        return _rec


@pytest.fixture
def pool(monkeypatch):
    """A pool whose connection is a fake - no Splunk, no network, no login."""
    p = SplunkConnectionPool.__new__(SplunkConnectionPool)
    client = _FakeClient()
    p._client = client
    monkeypatch.setattr(SplunkConnectionPool, "_call",
                        lambda self, name, *a, **kw: getattr(client, name)(*a, **kw))
    return p


# ── the contract ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", TOOL_FACING_METHODS)
def test_pool_exposes_every_method_the_tools_call(name):
    assert callable(getattr(SplunkClient, name, None)), \
        f"SplunkClient lost {name}, which agent tools call"
    bare = SplunkConnectionPool.__new__(SplunkConnectionPool)
    assert callable(getattr(bare, name)), f"the pool cannot reach {name}"


@pytest.mark.parametrize("name", TOOL_FACING_METHODS)
def test_pool_accepts_every_keyword_the_client_accepts(name, pool):
    """The drift that broke the run was a signature mismatch, not a missing name.

    Call each method through the pool with every keyword its client counterpart
    declares, and assert the kwargs arrive unchanged.
    """
    sig = inspect.signature(getattr(SplunkClient, name))
    kwargs = {}
    for prm in sig.parameters.values():
        if prm.name == "self" or prm.kind in (prm.VAR_KEYWORD, prm.VAR_POSITIONAL):
            continue
        kwargs[prm.name] = prm.default if prm.default is not prm.empty else ""
    getattr(pool, name)(**kwargs)
    called, _args, got = pool._client.calls[-1]
    assert called == name
    assert set(got) == set(kwargs), f"{name}: pool dropped {set(kwargs) - set(got)}"


def test_the_source_axis_reaches_the_client_through_the_pool(pool):
    """The exact call that failed in the live run."""
    pool.get_sourcetype_fields(source="cisconvmflowdata")
    name, _args, kwargs = pool._client.calls[-1]
    assert name == "get_sourcetype_fields"
    assert kwargs["source"] == "cisconvmflowdata"


def test_get_sources_is_reachable_through_the_pool(pool):
    pool.get_sources(keyword="cisco", top_n=50)
    name, _args, kwargs = pool._client.calls[-1]
    assert name == "get_sources"
    assert kwargs == {"keyword": "cisco", "top_n": 50}


# ── the delegation's own edges ────────────────────────────────────────────────

def test_unknown_method_raises_attribute_error_naming_the_cause():
    bare = SplunkConnectionPool.__new__(SplunkConnectionPool)
    with pytest.raises(AttributeError) as exc:
        bare.get_nonexistent_thing
    assert "SplunkClient does not define it" in str(exc.value)


def test_private_names_are_not_proxied():
    # Guards __init__-time recursion: __getattr__ fires before instance attrs
    # exist, so a private lookup must fail fast rather than try to proxy.
    bare = SplunkConnectionPool.__new__(SplunkConnectionPool)
    with pytest.raises(AttributeError):
        bare._not_yet_assigned


def test_pool_introspection_still_resolves_to_itself():
    # __getattr__ only fires when normal lookup fails; these must not be proxied.
    for name in ("checkout", "available", "in_use"):
        assert hasattr(SplunkConnectionPool, name)
