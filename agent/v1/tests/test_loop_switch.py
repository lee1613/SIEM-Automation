"""Task 12: --loop switch wiring the conversational loop into the runner.

Source-inspection style (like the plan's other tests here) — run_all_v1.main()
touches live Splunk/OpenAI/Featherless credentials at import-adjacent call time,
so it cannot be exercised end-to-end in a unit test. These tests assert on the
function's source text instead, same technique the plan itself uses.
"""
import inspect
import re

import run_all_v1

SRC = inspect.getsource(run_all_v1.main)


# ── plan's own tests (Step 1) ───────────────────────────────────────────────

def test_the_runner_exposes_a_loop_switch():
    assert '"--loop"' in SRC
    assert "conversational" in SRC and "compiler" in SRC


def test_conversational_is_the_default_on_this_branch():
    m = re.search(r'add_argument\(\s*"--loop".*?\)', SRC, re.DOTALL)
    assert m and 'default="conversational"' in m.group(0)


def test_both_loops_feed_the_same_submission_path():
    # whichever loop ran, `clean` still goes through finalize_answer before submit
    assert "finalize_answer(clean" in SRC
    assert SRC.index("run_question") < SRC.index("scoreboard.submit")


def test_the_conversational_path_records_the_ceiling_comparison():
    assert "senior_iterations" in SRC and "ceiling" in SRC, \
        "§4.1 requires actual senior-iterations against the ceiling in the run record"


# ── correction 1: SH cost must be tracked ───────────────────────────────────

def test_sh_llm_is_bound_with_tracker_before_run_question():
    """A bare sh_llm.invoke() never reaches the tracker (run_question calls
    llm.invoke(msgs) with no config — see sh_loop.run_question). The runner
    must bind callbacks/tags/metadata onto the model itself, per-question, and
    pass that bound object to run_question, not the raw sh_llm."""
    m = re.search(r'if args\.loop == "conversational":\n(.*?)conv = run_question\(',
                  SRC, re.DOTALL)
    assert m, "expected a conversational branch that binds the llm before calling run_question"
    binding_src = m.group(1)
    assert "sh_llm.with_config(" in binding_src
    assert '"callbacks": [tracker]' in binding_src
    assert '"tags": ["SH", qid]' in binding_src
    assert '"metadata": {"role": "SH", "qid": qid}' in binding_src
    # run_question must receive the bound model, not the bare sh_llm.
    call = re.search(r"conv = run_question\((.*?)\)", SRC, re.DOTALL).group(1)
    assert "llm=sh_llm_bound" in call


def test_with_config_on_structured_output_runnable_still_returns_the_turn_object():
    """with_config() on a .with_structured_output(...) runnable must return a
    RunnableBinding whose .invoke() still yields the structured Pydantic object
    (not a raw AIMessage) — otherwise run_question's `turn.entries` access
    would break the moment the tracker binding was introduced."""
    from conversation import SeniorDirective, SHTurn

    class _FakeStructuredRunnable:
        """Stands in for ChatOpenAI(...).with_structured_output(SHTurn, ...):
        a Runnable whose .invoke() returns a validated SHTurn."""
        def __init__(self, turn):
            self._turn = turn
            self.seen_config = None

        def invoke(self, msgs, config=None, **kw):
            self.seen_config = config
            return self._turn

        def with_config(self, config):
            bound = _FakeStructuredRunnable(self._turn)

            def _invoke(msgs, **kw):
                bound.seen_config = config
                return self._turn
            bound.invoke = _invoke
            return bound

    directive = SeniorDirective(
        senior_id="", r1_scope_alignment="NA", r2_progress="NA",
        r3_answer_readiness="NA", route="ANSWER",
        decision="", rationale="", directive="", basis="", flaw="",
        why_it_fails="", fix_directive="",
        scope_change={"sourcetypes": [], "sources": [], "fields": []},
        clarify_reason="", questions=[],
        constraints={"sourcetypes": [], "sources": [], "fields": []},
        technique="", spawn_type="", subquestion="", reason="",
        value="42", value_kind="count", source_senior="s1", justification="",
        case_updates=[],
    )
    turn = SHTurn(reading="done", entries=[directive])
    raw = _FakeStructuredRunnable(turn)
    bound = raw.with_config({"callbacks": [], "tags": ["SH", "Q1"]})

    result = bound.invoke([])
    assert isinstance(result, SHTurn)
    assert result.entries[0].value == "42"


# ── correction 2: cross-question memory ─────────────────────────────────────

def test_sh_history_is_created_once_before_the_question_loop():
    before_loop, loop_body = SRC.split("for q in selected:", 1)
    assert "sh_history: list = []" in before_loop
    assert "sh_history = []" not in loop_body and "sh_history: list = []" not in loop_body


def test_history_is_threaded_through_every_conversational_call():
    calls = re.findall(r"run_question\((.*?)\n(?:            |                )\)",
                        SRC, re.DOTALL)
    assert calls, "expected at least one run_question(...) call"
    for call in calls:
        assert "history=sh_history" in call


# ── correction 3: no report text on the scoreboard ──────────────────────────

def test_conversational_branch_does_not_call_fallback_answer_on_sh_answer():
    m = re.search(r'if args\.loop == "conversational":\n(.*?)else:\n\s+clean = sh_answer',
                  SRC, re.DOTALL)
    assert m, "expected the clean= block to branch on args.loop"
    conv_branch = m.group(1)
    assert "fallback_answer(sh_answer" not in conv_branch, \
        "conversational path must never route sh_answer through fallback_answer()"
    assert "answer_shaped(sh_answer)" in conv_branch
    assert 'clean = ""' in conv_branch


def test_compiler_branch_fallback_logic_is_unchanged():
    """A/B integrity: the compiler branch's fallback_answer() logic must be
    byte-for-byte the pre-Task-12 code, just re-indented under `else:`."""
    assert 'clean = fallback_answer(sh_answer, ctx.q_delegations)\n' in SRC
    assert 'print("[SH] FAILED for this question; falling back to best worker answer")' in SRC
    assert 'logger.events.emit("sh_failed", qid=qid)' in SRC
    assert 'logger.events.emit("sh_answer_unshaped", qid=qid)' in SRC


# ── correction 4: hint re-run uses the active loop ──────────────────────────

def test_hint_block_branches_on_loop_and_reuses_run_question():
    hint_block = SRC[SRC.index("Hint economy"):]
    assert 'if args.loop == "conversational":' in hint_block
    conv_hint, compiler_hint = hint_block.split('else:', 1)
    assert "run_question(" in conv_hint
    # The actual call, not just a mention in a comment.
    assert "sh_answer, _ = run_sh(" not in conv_hint
    assert "llm=sh_llm_bound" in conv_hint
    assert "history=sh_history" in conv_hint
    assert 'os.path.join(logger.run_dir, "hint")' in conv_hint
    # compiler branch keeps calling run_sh with the hint text unchanged.
    assert "run_sh(" in compiler_hint
    assert "sh_graph" in compiler_hint


def test_hint_conv_measurements_recorded_with_empty_default():
    assert '"hint_conv": dict' in SRC.replace(" ", "") or "hint_conv: dict = {}" in SRC
    assert '"hint_conv"' in SRC
    assert '"end_reason":        hint_result["end_reason"]'.replace(" ", "") in SRC.replace(" ", "")


def test_hint_pass_delegations_reach_the_run_totals():
    src = inspect.getsource(run_all_v1.main)
    hint = src[src.index("hint_result = run_question"):]
    assert "ctx.all_delegations.extend(ctx.q_delegations[n_before:])" in hint
