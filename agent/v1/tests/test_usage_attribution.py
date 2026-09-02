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
