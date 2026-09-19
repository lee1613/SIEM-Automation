"""Featherless out of credit -> the same GLM-5.3 on AI& takes the call (2026-09-19)."""
import httpx
import openai
import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from splunk_agent import with_fallback
from usage_tracker import _call_cost


def _refused(status):
    req = httpx.Request("POST", "https://api.featherless.ai/v1/chat/completions")
    resp = httpx.Response(status, json={"error": {"message": "insufficient credits"}}, request=req)

    def call(_):
        raise openai.APIStatusError("insufficient credits", response=resp, body=None)
    return RunnableLambda(call)


def test_a_refused_call_is_answered_by_the_fallback():
    out = with_fallback(_refused(402), FakeListChatModel(responses=["from AI&"])).invoke("q")
    assert out.content == "from AI&"


def test_a_connection_error_is_not_swapped():
    def boom(_):
        raise openai.APIConnectionError(request=httpx.Request("POST", "https://x"))
    chain = with_fallback(RunnableLambda(boom), FakeListChatModel(responses=["no"]))
    with pytest.raises(openai.APIConnectionError):
        chain.invoke("q")


def test_no_fallback_leaves_the_primary_untouched():
    primary = FakeListChatModel(responses=["x"])
    assert with_fallback(primary, None) is primary


def test_ai_and_and_featherless_price_the_same_model_apart():
    # 1M input, of which 500K cached, + 100K output.
    assert _call_cost("aiand:GLM-5.3", 1_000_000, 500_000, 100_000) == pytest.approx(
        0.5 * 1.00 + 0.5 * 0.30 + 0.1 * 4.00)
    assert _call_cost("zai-org/GLM-5.3", 1_000_000, 500_000, 100_000) == pytest.approx(
        0.5 * 1.40 + 0.5 * 0.26 + 0.1 * 4.40)
    assert _call_cost("GLM-5.3", 1_000_000, 0, 0) == pytest.approx(1.40)  # normalized -> Featherless


def test_a_price_as_tag_bills_the_call_under_its_own_row():
    from langchain_core.outputs import ChatGeneration, LLMResult
    from langchain_core.messages import AIMessage
    from usage_tracker import UsageTracker
    t = UsageTracker()
    res = LLMResult(generations=[[ChatGeneration(message=AIMessage("ok"))]],
                    llm_output={"model_name": "zai-org/GLM-5.3", "token_usage":
                                {"prompt_tokens": 1_000_000, "completion_tokens": 0}})
    t.on_llm_end(res, tags=["senior", "Q216", "price_as:aiand:GLM-5.3"])
    assert t._models["aiand:GLM-5.3"]["estimated_usd"] == pytest.approx(1.00)
    assert "zai-org/GLM-5.3" not in t._models
