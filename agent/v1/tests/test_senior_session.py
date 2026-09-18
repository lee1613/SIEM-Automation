"""Tests for SeniorSession (spec §2.3, §6, §7)."""
from senior_session import SeniorSession, should_alert, should_compact

WINDOW = 100_000


def test_compaction_triggers_when_the_projected_round_would_pass_80_percent():
    # 60k now + 8 rounds-worth of 3k/iteration = 84k > 80k
    assert should_compact(60_000, mean_per_iter=3_000, window=WINDOW) is True


def test_no_compaction_when_the_projection_stays_under_80_percent():
    # 40k now + 8 * 3k = 64k < 80k
    assert should_compact(40_000, mean_per_iter=3_000, window=WINDOW) is False


def test_the_80_percent_boundary_is_exclusive():
    # exactly 80 000 projected is not yet over the line
    assert should_compact(80_000 - 8 * 1_000, mean_per_iter=1_000, window=WINDOW) is False
    assert should_compact(80_001 - 8 * 1_000, mean_per_iter=1_000, window=WINDOW) is True


def test_the_operator_alert_fires_at_70_percent_of_the_window():
    assert should_alert(70_000, WINDOW) is False
    assert should_alert(70_001, WINDOW) is True


class _Pool:
    """Records the calls a session makes; returns a fixed round result."""

    def __init__(self, **over):
        self.rounds, self.clarifies = [], []
        self.result = {
            "status": "partial", "value": "", "value_kind": "", "evidence": "",
            "confidence": 40, "notes": "", "insight": "NOT_FOUND",
            "report": "## Prior rounds\n- r1: nothing\n\n## This round\n",
            "spl_used": ["index=botsv3 | stats count"], "sourcetypes": ["syslog"],
            "negative_findings": [], "search_space_used": {"sourcetypes": [], "sources": []},
            "iterations": 5, "cap_hit": False, "structured": True,
            "last_prompt_tokens": 1_000, "answer": "", "full_state": [],
        }
        self.result.update(over)

    def run_round(self, **kw):
        self.rounds.append(kw)
        return dict(self.result)

    def clarify(self, **kw):
        self.clarifies.append(kw)
        return "The window was the one you gave me."


def _session(pool, **over):
    kw = dict(sid="s1", pool=pool, qid="Q216", technique="hunter",
              subquestion="Find the flow duration.", brief="BRIEF",
              window=WINDOW, rounds_granted=8)
    kw.update(over)
    return SeniorSession(**kw)


def test_the_first_round_sends_the_spawn_brief_and_the_directive():
    pool = _Pool()
    s = _session(pool)
    s.work("Establish the population first.", rounds_remaining=7)
    sent = pool.rounds[0]["message"]
    assert "BRIEF" in sent and "Establish the population first." in sent


def test_a_later_round_sends_only_the_directive():
    pool = _Pool()
    s = _session(pool)
    s.work("first", rounds_remaining=7)
    s.work("second", rounds_remaining=6)
    assert "BRIEF" not in pool.rounds[1]["message"]
    assert "second" in pool.rounds[1]["message"]


def test_rounds_reuse_one_thread_until_compaction():
    pool = _Pool()
    s = _session(pool)
    s.work("a", rounds_remaining=7)
    s.work("b", rounds_remaining=6)
    assert pool.rounds[0]["thread_id"] == pool.rounds[1]["thread_id"]


def test_compaction_starts_a_new_thread_seeded_with_the_latest_report():
    pool = _Pool(last_prompt_tokens=90_000)
    s = _session(pool)
    s.work("a", rounds_remaining=7)          # comes back at 90k of a 100k window
    s.work("b", rounds_remaining=6)          # must compact before working
    assert pool.rounds[1]["thread_id"] != pool.rounds[0]["thread_id"]
    assert "## Prior rounds" in pool.rounds[1]["message"], \
        "the rebuilt thread is seeded with the senior's own latest report"
    assert s.compactions == 1


def test_the_report_header_is_stamped_with_the_runner_s_numbers():
    pool = _Pool()
    s = _session(pool)
    out = s.work("a", rounds_remaining=7)
    assert out["report"].startswith("# s1 - Q216 - Round 1")
    assert "rounds_remaining=7" in out["report"]
    assert "novel_spl=1" in out["report"]


def test_a_repeated_query_reports_zero_novel_spl():
    pool = _Pool()
    s = _session(pool)
    s.work("a", rounds_remaining=7)
    second = s.work("b", rounds_remaining=6)   # same spl_used as round 1
    assert second["novel_spl_count"] == 0


def test_iterations_accumulate_across_rounds():
    pool = _Pool()
    s = _session(pool)
    s.work("a", rounds_remaining=7)
    s.work("b", rounds_remaining=6)
    assert s.iterations == 10


def test_a_clarify_consumes_no_round():
    pool = _Pool()
    s = _session(pool)
    s.work("a", rounds_remaining=7)
    reply = s.clarify(["Was the window mine?"])
    assert "window" in reply
    assert s.rounds_used == 1, "a clarify must not consume a senior round"
    assert pool.clarifies[0]["thread_id"] == pool.rounds[0]["thread_id"]


def test_the_handoff_is_the_last_report_plus_advice_for_a_replacement():
    pool = _Pool()
    s = _session(pool)
    s.work("a", rounds_remaining=7)
    h = s.handoff("two dead rounds")
    assert "# s1 - Q216 - Round 1" in h
    assert "What I'd tell my replacement" in h
    assert "two dead rounds" in h


def test_a_handoff_before_any_round_still_renders():
    s = _session(_Pool())
    assert "What I'd tell my replacement" in s.handoff("never started")


def test_compaction_fires_again_after_a_previous_compaction():
    """Compaction mean must be per-thread, not cumulative across threads."""
    # Each round returns 50k tokens from 8 iterations = 6_250 tokens/iter for THIS thread.
    # Projection: 50k + 8*6.25k = 100k > 80k → must compact.
    pool = _Pool(iterations=8, last_prompt_tokens=50_000)
    s = _session(pool, window=WINDOW)
    s.work("a", rounds_remaining=7)                # round 1, no compact yet
    assert s.compactions == 0
    s.work("b", rounds_remaining=6)                # round 2, must compact (50k + 8*6.25k > 80k)
    assert s.compactions == 1
    s.work("c", rounds_remaining=5)                # round 3, must compact AGAIN (new thread also 50k + 8*6.25k > 80k)
    assert s.compactions == 2


def test_failed_round_does_not_overwrite_state():
    """api_failed or runaway rounds must not overwrite last_prompt_tokens or last_report."""
    pool = _Pool(iterations=5, last_prompt_tokens=1_000)
    s = _session(pool)
    s.work("a", rounds_remaining=7)
    assert "## Prior rounds" in s.last_report
    first_report = s.last_report
    first_tokens = s.last_prompt_tokens
    assert first_tokens == 1_000
    first_thread_iters = s.thread_iterations

    # Round 2 fails: api_failed, report empty, tokens 0, but has many iterations
    pool.result.update(status="api_failed", report="", last_prompt_tokens=0, spl_used=[], iterations=8)
    out2 = s.work("b", rounds_remaining=6)
    # State must not change
    assert s.last_report == first_report, "last_report must not be overwritten on api_failed"
    assert s.last_prompt_tokens == first_tokens, "last_prompt_tokens must not be overwritten on api_failed"
    assert s.thread_iterations == first_thread_iters, "thread_iterations must not increase on failed round"
    assert s.iterations == first_thread_iters + 8, "cumulative iterations still increases"
    assert s.status == "api_failed"  # but status does update
    assert s.rounds_used == 2  # and round count increases
    # But the returned dict has the stamped fallback
    assert "**Insight:**" in out2["report"]


def test_original_spl_text_is_preserved():
    """Handoff renders original SPL spelling, not normalized."""
    pool = _Pool(spl_used=["index=botsv3 EventCode=4688"])
    s = _session(pool)
    s.work("a", rounds_remaining=7)
    h = s.handoff("test")
    assert "EventCode=4688" in h, "handoff must contain original case SPL"


def test_compaction_seed_lists_spl_already_run():
    """Compaction message includes a list of SPL already run, so novel_spl still diffs correctly."""
    pool = _Pool(last_prompt_tokens=90_000, spl_used=["index=botsv3 | stats count"])
    s = _session(pool)
    s.work("a", rounds_remaining=7)
    s.work("b", rounds_remaining=6)  # compacts
    # The compaction message sent to the pool should include the SPL from round 1
    message = pool.rounds[1]["message"]
    assert "## SPL you already ran" in message or "SPL you already" in message, \
        "compaction message must list prior SPL"
    assert "index=botsv3 | stats count" in message, \
        "compaction message must include the round 1 query in original case"


def test_fallback_report_renders_with_stamped_header():
    """When a result has no report field, _fallback_report fills in with stamped header."""
    pool = _Pool(report="", insight="NOT_FOUND", value="candidate123", confidence=50)
    s = _session(pool)
    out = s.work("a", rounds_remaining=7)
    assert out["report"].startswith("# s1 - Q216 - Round 1"), \
        "stamped header must be present even in fallback"
    assert "**Insight:** NOT_FOUND" in out["report"]
    assert "**Candidate:** candidate123" in out["report"]


def test_a_round_that_used_every_iteration_says_so_at_the_end_of_its_report():
    # Q216 smoke test: s1 spent all 8 iterations and SH read a blank report with
    # no hint that the round was cut off rather than finished.
    pool = _Pool(iterations=9, cap_hit=True)          # forced-submit path: step 9 > 8
    out = _session(pool).work("a", rounds_remaining=7)
    assert out["report"].rstrip().endswith("_Iteration cap reached: 8/8 iterations used "
                                           "this round — cut off, not finished._")


def test_the_cap_note_survives_the_fallback_report():
    pool = _Pool(report="", iterations=8)
    out = _session(pool).work("a", rounds_remaining=7)
    assert "Iteration cap reached: 8/8" in out["report"].splitlines()[-1]


def test_a_round_under_the_cap_carries_no_note():
    out = _session(_Pool(iterations=5)).work("a", rounds_remaining=7)
    assert "Iteration cap reached" not in out["report"]


def test_a_senior_with_no_technique_gets_the_plain_graph_not_hunter():
    # "" used to fall back to "hunter", which silently re-injected the pruned prompt.
    pool = _Pool()
    s = _session(pool, technique="")
    s.work("Begin.", rounds_remaining=7)
    assert pool.rounds[0]["technique"] == "senior"
