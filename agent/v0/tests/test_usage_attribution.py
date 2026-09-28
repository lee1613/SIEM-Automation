from types import SimpleNamespace

from usage_tracker import UsageTracker


def _fake_llm_result(model, prompt, completion):
    gen = SimpleNamespace(usage_metadata={"input_tokens": prompt, "output_tokens": completion})
    return SimpleNamespace(
        llm_output={"model_name": model, "token_usage":
                    {"prompt_tokens": prompt, "completion_tokens": completion}},
        generations=[[gen]],
    )


def test_by_question_buckets_sh_and_senior_separately():
    t = UsageTracker()
    t.on_llm_end(_fake_llm_result("gpt-5.4", 1000, 100), tags=["SH", "Q200"])
    t.on_llm_end(_fake_llm_result("GLM-5.2-fp8", 5000, 400), tags=["senior", "Q200"])
    bq = t.by_question()
    assert bq["Q200"]["sh"]["input_tokens"] == 1000
    assert bq["Q200"]["senior"]["input_tokens"] == 5000
    assert bq["Q200"]["senior"]["output_tokens"] == 400


def test_senior_call_with_leaked_sh_tag_bills_to_senior_not_sh():
    # Reproduces the real tag shape from a nested Senior graph.invoke() call:
    # LangChain's ambient tags=["SH", qid] from the still-active SH run leak
    # onto the Senior worker's own explicit ["senior", qid] tags. The "senior"
    # tag must win — this call must NOT be counted as SH cost.
    t = UsageTracker()
    t.on_llm_end(_fake_llm_result("GLM-5.2-fp8", 5000, 400),
                 tags=["SH", "Q200", "senior", "Q200"])
    bq = t.by_question()
    assert "sh" not in bq["Q200"]
    assert bq["Q200"]["senior"]["input_tokens"] == 5000
    assert t.sh_question_tokens()["input_tokens"] == 0


def test_extractor_usage_attributed_to_question():
    t = UsageTracker()
    t.add_nim_usage("deepseek-ai/DeepSeek-V4-Flash", inp=200, cached=0, out=10,
                    qid="Q200", role="extractor")
    bq = t.by_question()
    assert bq["Q200"]["extractor"]["input_tokens"] == 200


def test_totals_still_work():
    t = UsageTracker()
    t.on_llm_end(_fake_llm_result("gpt-5.4", 1000, 100), tags=["SH", "Q200"])
    tot = t.totals()
    assert tot["__total__"]["input_tokens"] == 1000


def test_top_level_cached_tokens_is_read():
    # Featherless returns usage.cached_tokens at the top level and omits
    # prompt_tokens_details entirely, unlike OpenAI. Reading only the nested
    # path scored every Featherless call as 0 cached.
    t = UsageTracker()
    t.on_llm_end(SimpleNamespace(
        llm_output={"model_name": "zai-org/GLM-5.3", "token_usage":
                    {"prompt_tokens": 28745, "completion_tokens": 588,
                     "cached_tokens": 28563}},
        generations=[[]],
    ), tags=["senior", "Q216"])
    assert t.by_question()["Q216"]["senior"]["cached_tokens"] == 28563


def test_openai_nested_cached_tokens_still_wins():
    t = UsageTracker()
    t.on_llm_end(SimpleNamespace(
        llm_output={"model_name": "gpt-5.4", "token_usage":
                    {"prompt_tokens": 1000, "completion_tokens": 50,
                     "prompt_tokens_details": {"cached_tokens": 640}}},
        generations=[[]],
    ), tags=["SH", "Q216"])
    assert t.by_question()["Q216"]["sh"]["cached_tokens"] == 640


def test_glm_5_3_priced_at_ai_and_rates():
    # AI& GLM-5.3: $1.00 input, $0.30 cached, $4.00 output per 1M.
    # 28,745 in / 28,563 cached / 588 out = 182*1.00 + 28,563*0.30 + 588*4.00 per 1M.
    t = UsageTracker()
    t.on_llm_end(SimpleNamespace(
        llm_output={"model_name": "zai-org/GLM-5.3", "token_usage":
                    {"prompt_tokens": 28745, "completion_tokens": 588,
                     "prompt_tokens_details": {"cached_tokens": 28563}}},
        generations=[[]],
    ), tags=["senior", "Q216"])
    assert abs(t.by_question()["Q216"]["senior"]["estimated_usd"] - 0.0111029) < 5e-7
