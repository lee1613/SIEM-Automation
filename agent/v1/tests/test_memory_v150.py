# agent/v1/tests/test_memory_v150.py — v1.5.0 memory (design: docs/version_architecture/v1/v1.5.0.md)
# Claude's half of the TDD list. The operator's SummaryQueue tests live in test_summary_queue.py.
import os
import time

import sh_memory
from conversation import SeniorDirective, SHTurn
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sh_loop import run_question
from sh_memory import (
    Entity,
    FeedFact,
    QuestionMemory,
    TimelineEvent,
    cap_knowledge,
    cap_timeline,
    merge_knowledge,
    merge_timeline,
    render_memory,
)

BASE = [SystemMessage(content="system prompt")]
CURRENT = [HumanMessage(content="NEW QUESTION — Q9.")]


def _mem(qid, *, entities=(), feed_facts=(), timeline=()):
    return QuestionMemory(
        qid=qid, question=f"What happened in {qid}?", guidance="", answer=f"ans-{qid}",
        flow=["found A, so looked at B"], derivation=f"derivation of {qid}",
        entities=list(entities), feed_facts=list(feed_facts), working_spl=[],
        timeline=list(timeline), ruled_out="none")


def _write(run_dir, mem):
    sh_memory._write_memory(str(run_dir), mem)
    time.sleep(0.01)                 # load_memories orders by mtime


def _raw(qid, words):
    return [HumanMessage(content=f"NEW QUESTION — {qid}. " + "word " * words),
            AIMessage(content=f"{qid} turn")]


def _text(msgs):
    return "\n".join(str(m.content) for m in msgs)


# ── R2 / D5: quiet below the threshold ────────────────────────────────────────

def test_below_the_threshold_the_prompt_carries_raw_transcripts_only(tmp_path):
    history = {q: _raw(q, 50) for q in ("Q1", "Q2")}
    for q in history:
        _write(tmp_path, _mem(q, entities=[Entity(key="HOTH", fact="server")]))
    view = render_memory(str(tmp_path), history, qid="Q9", base=BASE, current=CURRENT)
    text = _text(view.messages)
    assert "MEMORY INDEX" not in text and "KNOWLEDGE" not in text and "TIMELINE" not in text
    assert view.messages == history["Q1"] + history["Q2"]
    assert view.summarized_count == 0


def test_after_the_first_swap_only_summarized_questions_get_a_block(tmp_path):
    history = {q: _raw(q, 2000) for q in ("Q1", "Q2", "Q3")}
    for q in history:
        _write(tmp_path, _mem(q))
    view = render_memory(str(tmp_path), history, qid="Q9", base=BASE, current=CURRENT,
                         threshold=4000)
    text = _text(view.messages)
    k = view.summarized_count
    assert k >= 1
    for q in view.order[:k]:
        assert f"**{q}**" in text and history[q][0] not in view.messages
    for q in view.order[k:]:
        assert f"**{q}**" not in text, "a question still held raw has no card (D1)"
        assert history[q][0] in view.messages


# ── R1 / D2 / I1: one counter, and the summarized questions are a prefix ────────

def test_the_summarized_questions_are_always_a_prefix_of_question_order(tmp_path):
    history = {}
    for n in range(1, 7):
        q = f"Q{n}"
        history[q] = _raw(q, 800)
        _write(tmp_path, _mem(q))
        view = render_memory(str(tmp_path), history, qid=f"Q{n + 1}", base=BASE,
                             current=CURRENT, threshold=3000)
        k = view.summarized_count
        assert view.order == list(history)
        raw_kept = [q for q in view.order if history[q][0] in view.messages]
        assert raw_kept == view.order[k:], "I1: summarized = order[:k], raw = order[k:]"


def test_the_counter_survives_a_restart(tmp_path):
    history = {q: _raw(q, 2000) for q in ("Q1", "Q2", "Q3")}
    for q in history:
        _write(tmp_path, _mem(q))
    k1 = render_memory(str(tmp_path), history, qid="Q9", base=BASE, current=CURRENT,
                       threshold=4000).summarized_count
    k2 = render_memory(str(tmp_path), history, qid="Q9", base=BASE, current=CURRENT,
                       threshold=10**9).summarized_count
    assert k1 >= 1 and k2 == k1, "once summarized, stays summarized"


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


def _recall(qid, what="summary"):
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


def test_a_recall_of_a_question_held_raw_is_refused_and_costs_nothing(tmp_path):
    _write(tmp_path, _mem("Q1"))
    llm = _Script([_recall("Q1")] * 3 + [_recall("Q1", "ledger")] * 20)
    out = run_question(llm=llm, pool=_NoPool(), qid="Q2", question="q?", guidance="",
                       points=100, run_dir=str(tmp_path), hitl=False,
                       history={"Q1": _raw("Q1", 5)})
    fed = [str(m[-1].content) for m in llm.seen[1:4]]
    assert all("already in your context in full" in f for f in fed), fed
    # Three refused recalls charged no turn and no slot, so both ledger recalls are still
    # served (the prompt shows only the ledger table) before the cap rejects the third.
    assert "RECALLED Q1 ledger" in str(llm.seen[4][-1].content)
    assert "RECALLED Q1 ledger" in str(llm.seen[5][-1].content)
    assert "[B7]" in str(llm.seen[6][-1].content)
    assert out["turns"] == 5


def test_a_recall_of_a_summarized_question_is_served(tmp_path):
    history = {q: _raw(q, 2000) for q in ("Q1", "Q2")}
    for q in history:
        _write(tmp_path, _mem(q))
    llm = _Script([_recall("Q1")] + [SHTurn(reading="r", entries=[])] * 10)
    run_question(llm=llm, pool=_NoPool(), qid="Q3", question="q?", guidance="",
                 points=100, run_dir=str(tmp_path), hitl=False, history=history,
                 memory_threshold=3000)
    assert str(llm.seen[1][-1].content).startswith("RECALLED Q1 summary")


# ── I3: the swap waits for summaries still in flight, and only then ─────────────

class _Queue:
    def __init__(self):
        self.waits = 0

    def wait(self):
        self.waits += 1


def test_render_memory_waits_for_the_queue_only_over_the_threshold(tmp_path):
    history = {q: _raw(q, 2000) for q in ("Q1", "Q2")}
    q = _Queue()
    render_memory(str(tmp_path), history, qid="Q9", base=BASE, current=CURRENT, queue=q)
    assert q.waits == 0, "under the threshold the next question starts immediately"
    render_memory(str(tmp_path), history, qid="Q9", base=BASE, current=CURRENT,
                  threshold=3000, queue=q)
    assert q.waits == 1


# ── R3: incident timeline ────────────────────────────────────────────────────────

def _ev(time, entity, event):
    return TimelineEvent(time=time, entity=entity, event=event, evidence="stream:http uri")


def test_the_timeline_normalizes_times_and_sorts_across_questions():
    a = _mem("Q1", timeline=[_ev("2018-08-20 19:09:48", "hoth", "Struts RCE writes /tmp/colonel")])
    b = _mem("Q2", timeline=[_ev("1534770106", "bstoll", "first CloudTrail access"),
                             _ev("2018-08-20T13:57:54Z", "web_admin", "S3 bucket made public")])
    rows = merge_timeline([a, b])
    assert [r.entity for r in rows] == ["bstoll", "web_admin", "hoth"]
    assert rows[0].time_utc.startswith("2018-08-20T13:01:46")


def test_the_timeline_merges_duplicates_before_capping():
    same = [_ev("2018-08-20T13:57:54Z", "web_admin", "S3 bucket made public"),
            _ev("2018-08-20 13:57:10", "web_admin", "S3 bucket made public")]
    rows = merge_timeline([_mem("Q1", timeline=same[:1]), _mem("Q2", timeline=same[1:])])
    assert len(rows) == 1 and rows[0].qids == ["Q1", "Q2"]


def test_an_over_cap_timeline_drops_the_oldest_and_names_every_drop(tmp_path):
    evs = [_ev(f"2018-08-20T13:{m:02d}:00Z", f"host{m}", "lateral movement " + "x " * 60)
           for m in range(40)]
    rows = merge_timeline([_mem("Q1", timeline=evs)])
    text, dropped = cap_timeline(rows, cap=1500, run_dir=str(tmp_path))
    assert dropped and sh_memory.count_tokens(text) <= 1500
    log = open(os.path.join(tmp_path, "memory", "compaction_log.md"), encoding="utf-8").read()
    for d in dropped:
        assert d in log, "R4: every dropped entry is logged in full"


# ── R4: verbose knowledge cap ────────────────────────────────────────────────────

def test_an_over_cap_knowledge_block_logs_every_dropped_entry(tmp_path):
    old = _mem("Q1", feed_facts=[FeedFact(sourcetype="stream:smtp", fact="x " * 300)])
    new = _mem("Q2", feed_facts=[FeedFact(sourcetype="osquery", fact="y " * 300)])
    text, dropped = cap_knowledge(merge_knowledge([old, new]), cap=400, run_dir=str(tmp_path))
    assert len(dropped) == 1 and "stream:smtp" in dropped[0] and "osquery" in text
    log = open(os.path.join(tmp_path, "memory", "compaction_log.md"), encoding="utf-8").read()
    assert "CAP knowledge" in log and dropped[0] in log


# ── consequence of threading: a late summary's cost reaches its metrics row ──────

def test_metrics_rows_are_refreshed_with_cost_that_arrived_after_they_were_written():
    from run_all_v1 import refresh_cost_by_role
    rows = [{"qid": "Q1", "cost_by_role": {"sh": 0.1}}]
    refresh_cost_by_role(rows, {"Q1": {"sh": {"estimated_usd": 0.1},
                                       "memory": {"estimated_usd": 0.012}}})
    assert rows[0]["cost_by_role"] == {"sh": 0.1, "memory": 0.012}
