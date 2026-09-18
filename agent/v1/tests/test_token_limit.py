"""The token cap must survive langchain-openai's field rename.

Probed 2026-09-18 against zai-org/GLM-5.3 on Featherless: `max_tokens=12000`
produced 8211 tokens, `max_completion_tokens=12000` stopped dead at 4096. The
code asked for 16384 via `max_tokens`, langchain-openai 1.3.2 rewrote it to
`max_completion_tokens`, Featherless ignored that and applied its own 4096
default - which truncated every GLM senior's round report mid-reasoning.
"""

from langchain_openai import ChatOpenAI
from splunk_agent import token_limit_kwargs


def test_a_non_openai_endpoint_gets_the_raw_field():
    assert token_limit_kwargs("https://api.featherless.ai/v1") == {
        "extra_body": {"max_tokens": 16384}}


def test_openai_keeps_the_field_it_requires():
    assert token_limit_kwargs(None) == {"max_completion_tokens": 16384}
    assert token_limit_kwargs("") == {"max_completion_tokens": 16384}


def test_the_limit_is_caller_settable():
    assert token_limit_kwargs("https://x/v1", 2048) == {"extra_body": {"max_tokens": 2048}}


def test_max_tokens_really_does_reach_the_wire_as_max_tokens():
    # The regression guard: if a langchain-openai upgrade starts rewriting
    # extra_body too, this fails here instead of silently capping seniors at
    # 4096 again in a paid run.
    llm = ChatOpenAI(api_key="sk-fake", model="zai-org/GLM-5.3",
                     base_url="https://api.featherless.ai/v1",
                     **token_limit_kwargs("https://api.featherless.ai/v1"))
    payload = llm._get_request_payload([("human", "hi")], stop=None)
    assert payload.get("extra_body") == {"max_tokens": 16384}


def test_the_plain_field_is_what_broke_so_it_must_not_be_used():
    llm = ChatOpenAI(api_key="sk-fake", model="zai-org/GLM-5.3",
                     base_url="https://api.featherless.ai/v1", max_tokens=16384)
    payload = llm._get_request_payload([("human", "hi")], stop=None)
    assert "max_tokens" not in payload and payload["max_completion_tokens"] == 16384, \
        "langchain-openai no longer renames max_tokens - token_limit_kwargs can be simplified"
