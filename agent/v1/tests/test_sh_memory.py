# agent/v1/tests/test_sh_memory.py — v1.4.5 SH memory (plan §7)
import os
import re
import time

import pytest
import resume
import sh_memory
from conversation import SeniorDirective, SHTurn
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import LLMResult
from pydantic import ValidationError
from sh_loop import run_question
from sh_memory import (
    Digest,
    Entity,
    FeedFact,
    QuestionMemory,
    WorkingSpl,
    cap_knowledge,
    load_memories,
    merge_knowledge,
    recall,
    render_card,
    render_memory,
    summarize_question,
)
from usage_tracker import UsageTracker

HERE = os.path.dirname(os.path.abspath(__file__))


def _mem(qid, *, entities=(), feed_facts=(), spl=(), flow=("found A, so looked at B",)):
    return QuestionMemory(
        qid=qid, question=f"What happened in {qid}?", guidance="an integer",
        answer=f"ans-{qid}", flow=list(flow), derivation=f"derivation of {qid}",
        entities=list(entities), feed_facts=list(feed_facts), working_spl=list(spl),
        ruled_out=f"dead ends of {qid}")


def _write(run_dir, mem):
    sh_memory._write_memory(str(run_dir), mem)
    time.sleep(0.01)          # load_memories orders by mtime


def _raw(qid, words):
    return [HumanMessage(content=f"NEW QUESTION — {qid}. " + "word " * words),
            AIMessage(content=f"{qid} turn")]


BASE = [SystemMessage(content="system prompt")]
CURRENT = [HumanMessage(content="NEW QUESTION — Q4.")]


# 1. the swap: whole questions, oldest first, never the current one, stops once under
def test_the_swap_replaces_the_oldest_whole_question_and_stops_once_under(tmp_path,
                                                                           monkeypatch):
    monkeypatch.setattr(sh_memory, "SWAP_TARGET", 1.0)     # the plan's swap-just-under
    history = {q: _raw(q, 2000) for q in ("Q1", "Q2", "Q3")}
    for q in history:
        _write(tmp_path, _mem(q))
    history["Q4"] = [AIMessage(content="an earlier pass at Q4")]
    size = sh_memory._msgs_tokens(BASE + CURRENT + render_memory(
        str(tmp_path), history, qid="Q4", base=BASE, current=CURRENT, threshold=10**9))
    out = render_memory(str(tmp_path), history, qid="Q4", base=BASE, current=CURRENT,
                        threshold=size - 1000)      # one question's raw is ~2000 tok
    text = "\n".join(str(m.content) for m in out)
    assert history["Q1"][0] not in out, "the oldest question is swapped out"
    assert history["Q2"][0] in out and history["Q3"][0] in out, "only as many as needed"
    assert "### Q1 — detail" in text and "### Q2 — detail" not in text
    assert out[-1] is history["Q4"][0], "the current question is never swapped"
    log = open(os.path.join(tmp_path, "memory", "compaction_log.md"), encoding="utf-8").read()
    assert "Q1 raw" in log and "→ summary" in log


def test_everything_past_is_swapped_when_nothing_fits_but_the_current_stays(tmp_path):
    history = {"Q1": _raw("Q1", 50), "Q4": [AIMessage(content="Q4 so far")]}
    _write(tmp_path, _mem("Q1"))
    out = render_memory(str(tmp_path), history, qid="Q4", base=BASE, current=CURRENT,
                        threshold=1)
    assert history["Q1"][0] not in out
    assert history["Q4"][0] in out


def test_a_swap_goes_down_to_the_target_and_stays_swapped(tmp_path):
    # Batch swap for the prompt cache: past the threshold the prompt comes down to
    # SWAP_TARGET x threshold, and a swapped question stays summarized afterwards even
    # when it would fit again - otherwise the prompt's start changes every question.
    history = {q: _raw(q, 1000) for q in ("Q1", "Q2", "Q3", "Q4")}
    for q in history:
        _write(tmp_path, _mem(q))
    full = sh_memory._msgs_tokens(BASE + CURRENT + render_memory(
        str(tmp_path), history, qid="Q5", base=BASE, current=CURRENT, threshold=10**9))
    threshold = full - 200                      # just over: a one-at-a-time swap takes Q1 only
    out = render_memory(str(tmp_path), history, qid="Q5", base=BASE, current=CURRENT,
                        threshold=threshold)
    assert sh_memory._msgs_tokens(BASE + CURRENT + out) <= threshold * sh_memory.SWAP_TARGET
    assert sh_memory._load_swapped(str(tmp_path)) == ["Q1", "Q2"]
    # Next question, far under the threshold: Q1 and Q2 stay summarized, nothing new swaps.
    out = render_memory(str(tmp_path), history, qid="Q5", base=BASE, current=CURRENT,
                        threshold=10**9)
    assert history["Q1"][0] not in out and history["Q3"][0] in out
    assert sh_memory._load_swapped(str(tmp_path)) == ["Q1", "Q2"]


def test_the_part_that_changes_between_questions_comes_last(tmp_path):
    # The prompt cache bills an identical leading run at a tenth of the price, so what
    # grows every question (cards, knowledge) must come AFTER the raw transcripts.
    history = {"Q1": _raw("Q1", 50), "Q2": _raw("Q2", 50)}
    _write(tmp_path, _mem("Q1"))
    _write(tmp_path, _mem("Q2"))
    first = render_memory(str(tmp_path), history, qid="Q3", base=BASE, current=CURRENT)
    history["Q3"] = _raw("Q3", 50)
    _write(tmp_path, _mem("Q3"))
    second = render_memory(str(tmp_path), history, qid="Q4", base=BASE, current=CURRENT)
    assert first[:4] == second[:4] == history["Q1"] + history["Q2"]
    assert "MEMORY INDEX" in str(first[4].content)


def test_the_case_file_comes_after_the_memory(tmp_path):
    class Case:
        def render_digest(self):
            return "entity host HOTH"
    _write(tmp_path, _mem("Q1"))
    llm = _Script([_recall_turn()] * 2 + [SHTurn(reading="r", entries=[])] * 10)
    run_question(llm=llm, pool=_NoPool(), qid="Q2", question="q?", guidance="",
                 points=100, run_dir=str(tmp_path), hitl=False, case_file=Case(),
                 history={"Q1": _raw("Q1", 5)})
    kinds = [str(m.content)[:12] for m in llm.seen[0]]
    assert kinds.index("MEMORY INDEX") < kinds.index("CASE FILE (k")


# 2. below the threshold nothing moves
def test_no_swap_below_the_threshold(tmp_path):
    history = {q: _raw(q, 100) for q in ("Q1", "Q2")}
    for q in history:
        _write(tmp_path, _mem(q))
    out = render_memory(str(tmp_path), history, qid="Q3", base=BASE, current=CURRENT)
    text = "\n".join(str(m.content) for m in out)
    assert all(m in out for q in history for m in history[q])
    assert "DETAILED SUMMARIES" not in text
    assert "MEMORY INDEX" in text and '"What happened in Q1?"' in text


def test_an_old_flat_history_with_no_summary_is_dropped_first(tmp_path):
    history = {"": _raw("Q0", 3000), "Q1": _raw("Q1", 10)}
    out = render_memory(str(tmp_path), history, qid="Q2", base=BASE, current=CURRENT,
                        threshold=500)
    assert history[""][0] not in out and history["Q1"][0] in out


# 3. the summarizer never sees the answer key or a verdict
class _Summarizer:
    def __init__(self):
        self.seen = None

    def invoke(self, msgs, **kw):
        # The data sent, not the instructions: the system prompt itself says the
        # summarizer is "not told whether the answer is correct".
        self.seen = str(msgs[-1].content)
        return Digest(flow=["found the flow, which named the host"], derivation="d",
                      entities=[Entity(key="HOTH", fact="the Tomcat server")],
                      feed_facts=[], working_spl=[], ruled_out="none")


def test_the_summarizer_input_carries_no_answer_key_or_verdict(tmp_path):
    sentinel = "SENTINEL-OFFICIAL-ANSWER-7f3a"
    with open(os.path.join(tmp_path, "botsv3_answers.json"), "w") as fh:
        fh.write(f'[{{"id": "Q1", "answer": "{sentinel}"}}]')
    llm = _Summarizer()
    summarize_question(llm, run_dir=str(tmp_path), qid="Q1", question="q?", guidance="",
                       answer="1666", transcript=_raw("Q1", 5), ledger=None)
    assert sentinel not in llm.seen
    assert not re.search(r"\b(correct|incorrect|wrong|verdict)\b", llm.seen, re.I)


def test_the_runner_passes_the_summarizer_nothing_from_the_scoreboard():
    src = open(os.path.join(HERE, "..", "run_all_v1.py"), encoding="utf-8").read()
    call = src[src.index("sh_memory.summarize_question("):]
    call = call[:call.index("ledger=ledgers.get(qid))")]
    for leaked in ("correct", "sb_correct", "verdict", "answers[", "pts_earned"):
        assert leaked not in call, leaked


def test_a_summary_is_written_once_as_json_and_markdown(tmp_path):
    mem = summarize_question(_Summarizer(), run_dir=str(tmp_path), qid="Q1", question="q?",
                             guidance="", answer="1666", transcript=_raw("Q1", 5),
                             ledger=None)
    assert load_memories(str(tmp_path))["Q1"] == mem
    md = open(os.path.join(tmp_path, "memory", "Q1.md"), encoding="utf-8").read()
    assert "**Answer: 1666**" in md and "HOTH: the Tomcat server" in md


def test_a_failed_summary_is_logged_and_not_fatal(tmp_path):
    class Boom:
        def invoke(self, msgs, **kw):
            raise RuntimeError("provider down")
    assert summarize_question(Boom(), run_dir=str(tmp_path), qid="Q1", question="q",
                              guidance="", answer="x", transcript=[], ledger=None) is None
    assert load_memories(str(tmp_path)) == {}


# 4. the card, and a card with no flow
def test_a_card_renders_the_verbatim_question_the_answer_and_the_flow():
    card = render_card(_mem("Q9", flow=["step one", "step two"]))
    assert '"What happened in Q9?" (an integer)' in card
    assert "**Answer: ans-Q9**" in card
    assert "1. step one\n2. step two" in card


def test_a_memory_without_a_flow_is_rejected_by_the_schema():
    with pytest.raises(ValidationError):
        Digest(flow=[], derivation="d", entities=[], feed_facts=[], working_spl=[],
               ruled_out="x")
    with pytest.raises(ValidationError):
        Digest(flow=["  "], derivation="d", entities=[], feed_facts=[], working_spl=[],
               ruled_out="x")


# 5. knowledge: same key replaces, the cap drops the least recent, nothing is lost
def test_knowledge_merge_replaces_the_same_key_with_the_later_question():
    k = merge_knowledge([_mem("Q1", entities=[Entity(key="hoth", fact="old")]),
                         _mem("Q2", entities=[Entity(key="HOTH", fact="new")])])
    assert list(k["Entities"].values()) == [("HOTH: new", "Q2", 1)]


def test_working_spl_keeps_the_newest_few_per_sourcetype():
    mems = [_mem(f"Q{i}", spl=[WorkingSpl(sourcetype="st", purpose=f"p{i}", spl="s",
                                          returns="r")]) for i in range(5)]
    purposes = [t for t, *_ in merge_knowledge(mems)["Working SPL"].values()]
    assert len(purposes) == sh_memory.SPL_PER_SOURCETYPE
    assert "p4" in purposes[-1] and not any("p0" in p for p in purposes)


def test_the_cap_drops_the_least_recent_and_the_entry_survives_on_disk(tmp_path):
    old = _mem("Q1", feed_facts=[FeedFact(sourcetype="stream:smtp", fact="x " * 300)])
    new = _mem("Q2", feed_facts=[FeedFact(sourcetype="osquery", fact="y " * 300)])
    _write(tmp_path, old)
    _write(tmp_path, new)
    text, dropped = cap_knowledge(merge_knowledge([old, new]), cap=400)
    assert dropped == 1 and "osquery" in text and "stream:smtp" not in text
    assert "stream:smtp" in open(os.path.join(tmp_path, "memory", "Q1.json")).read()


# 6. RECALL
def test_recall_returns_the_named_file(tmp_path):
    _write(tmp_path, _mem("Q1"))
    os.makedirs(os.path.join(tmp_path, "Q1", "reports"))
    with open(os.path.join(tmp_path, "Q1", "reports", "s2_round_3.md"), "w") as fh:
        fh.write("round three report")
    assert "derivation of Q1" in recall(str(tmp_path), "Q1", "summary")
    assert "round three report" in recall(str(tmp_path), "q1", "report:s2:3")


def test_recall_truncates_at_8k_tokens_and_says_so(tmp_path):
    os.makedirs(os.path.join(tmp_path, "Q1"))
    with open(os.path.join(tmp_path, "Q1", "conversation.md"), "w") as fh:
        fh.write("token " * 20_000)
    out = recall(str(tmp_path), "Q1", "conversation")
    assert "truncated at 8,000 tokens" in out
    assert sh_memory.count_tokens(out) < 8_200


def test_recall_of_a_missing_file_lists_what_exists(tmp_path):
    _write(tmp_path, _mem("Q1"))
    assert "What exists for Q1: summary" in recall(str(tmp_path), "Q1", "ledger")
    assert "Past questions with a memory: Q1" in recall(str(tmp_path), "Q7", "summary")


BLANK = {
    "senior_id": "", "r1_scope_alignment": "NA", "r2_progress": "NA",
    "r3_answer_readiness": "NA", "r4_premise_verification": "NA", "route": "RECALL",
    "open_question_answers": [], "new_premises": [], "answer_premise_ids": [],
    "premise_stamps": [], "nominate_premise_id": "",
    "decision": "", "rationale": "", "directive": "",
    "basis": "", "flaw": "", "why_it_fails": "", "fix_directive": "",
    "scope_change": {"sourcetypes": [], "sources": [], "fields": []},
    "clarify_reason": "", "questions": [],
    "constraints": {"sourcetypes": [], "sources": [], "fields": []},
    "technique": "", "spawn_type": "", "subquestion": "", "reason": "",
    "deviation": "", "inherited_entities": "", "recall_qid": "", "recall_what": "",
    "value": "", "value_kind": "", "source_senior": "", "justification": "",
    "case_updates": [],
}


def _recall_turn(qid="Q1", what="summary"):
    return SHTurn(reading="r", entries=[SeniorDirective(
        **{**BLANK, "recall_qid": qid, "recall_what": what})])


class _Script:
    def __init__(self, turns):
        self.turns, self.seen = list(turns), []

    def invoke(self, msgs, **kw):
        self.seen.append(list(msgs))
        return self.turns.pop(0)


class _NoPool:
    senior_model = "gpt-5.4-mini"


def test_recall_needs_a_question_id_and_a_known_file_kind():
    with pytest.raises(ValidationError):
        SeniorDirective(**{**BLANK, "recall_qid": "", "recall_what": "summary"})
    with pytest.raises(ValidationError):
        SeniorDirective(**{**BLANK, "recall_qid": "Q1", "recall_what": "everything"})


def test_an_all_recall_turn_costs_no_turn_and_the_third_is_rejected(tmp_path):
    _write(tmp_path, _mem("Q1"))
    llm = _Script([_recall_turn() for _ in range(20)])
    out = run_question(llm=llm, pool=_NoPool(), qid="Q2", question="q?", guidance="",
                       points=100, run_dir=str(tmp_path), hitl=False)
    fed = [str(m[-1].content) for m in llm.seen[1:]]
    assert fed[0].startswith("RECALLED Q1 summary") and fed[1].startswith("RECALLED Q1")
    assert "[B7]" in fed[2], "the third RECALL turn is rejected"
    # Two free recall turns, then every rejected one is charged until the 5 run out.
    assert out["turns"] == 5 and len(llm.seen) == 7
    assert out["answer"] == "SH retired without answering"


# 7. resume
def test_per_question_history_round_trips_through_resume(tmp_path):
    history = {"Q1": _raw("Q1", 3), "Q2": _raw("Q2", 3)}
    resume.save_history(str(tmp_path), history)
    back = resume.load_history(str(tmp_path))
    assert list(back) == ["Q1", "Q2"]
    assert [m.content for m in back["Q2"]] == [m.content for m in history["Q2"]]


def test_an_old_flat_history_still_loads_as_one_unnamed_segment(tmp_path):
    resume._write(os.path.join(tmp_path, "sh_history.pkl"), _raw("Q1", 3))
    assert list(resume.load_history(str(tmp_path))) == [""]
    assert resume.load_history(str(tmp_path / "nowhere")) == {}


# cost: the summarizer is billed under its own role
def test_the_summarizer_is_costed_under_role_memory():
    t = UsageTracker()
    t.on_llm_end(LLMResult(generations=[], llm_output={
        "model_name": "gpt-5.4-mini",
        "token_usage": {"prompt_tokens": 10_000, "completion_tokens": 1_000}}),
        tags=["memory", "Q1"])
    bucket = t.by_question()["Q1"]["memory"]
    assert bucket["estimated_usd"] == pytest.approx(10_000 * 0.75e-6 + 1_000 * 4.5e-6)
