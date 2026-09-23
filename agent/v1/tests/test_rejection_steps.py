"""Every rejection line names the SOP step it enforces (v1.4.4).

SH's prompt is a numbered procedure. A rejection that says only what went wrong leaves
SH to hunt for the instruction it broke; `[C3] ... → re-read C3.` makes it a lookup.
These tests are the guarantee that the pointer stays reliable: a gate added later
without a tag fails here, instead of quietly shipping an unpointed rejection.
"""
import inspect
import re

import sh_loop
from conversation import (
    SeniorDirective,
    directive_violations,
    grade_violations,
    with_step,
)
from question_state import QuestionState

TAGGED = re.compile(r"^\[(?:[A-G]\d(?:–[A-G]?\d)?|REFERENCE: GATES)\] .+ → re-read .+\.$",
                    re.S)

# Gates that tag their own lines because one gate spans several steps.
SELF_TAGGING = {"grade_violations", "directive_violations"}

BLANK = {
    "senior_id": "", "r1_scope_alignment": "NA", "r2_progress": "NA",
    "r3_answer_readiness": "NA", "r4_premise_verification": "NA", "route": "RETIRE",
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


def entry(**kw):
    return SeniorDirective(**{**BLANK, **kw})


def test_the_tag_format():
    line = with_step("C3", "p4 stamp gives no holds_reason")
    assert line == "[C3] p4 stamp gives no holds_reason → re-read C3."
    assert TAGGED.match(line)


def test_every_gate_in_the_turn_check_is_tagged():
    """Source-level: each *_violations call in run_question's gate chain is wrapped in
    at_step(...) unless the gate tags its own lines. A new gate added bare fails here."""
    src = inspect.getsource(sh_loop.run_question)
    chain = src[src.index("problems = grade_violations("):
                src.index("# A refused update is not a gate violation")]
    called = set(re.findall(r"(\w+_violations)\(", chain))
    wrapped = set(re.findall(r'at_step\(\s*"[^"]+",\s*(\w+_violations)\(', chain))
    bare = called - wrapped - SELF_TAGGING
    assert not bare, f"untagged gate(s) in the turn check: {sorted(bare)}"
    assert "at_step(\"C7\", [\"the runner refused a premise update" in src.replace("\n", "") \
        or 'at_step("C7", ["the runner refused a premise update: "' in src


def _all_tagged(lines):
    assert lines, "the scenario was meant to trigger at least one violation"
    for ln in lines:
        assert TAGGED.match(ln), f"untagged rejection line: {ln!r}"


def test_the_self_tagging_gates_tag_every_line_they_emit():
    st = QuestionState(points=1000)
    # grade_violations: missing grades, an unrouted report, grading an explorer.
    _all_tagged(grade_violations(
        [entry(route="COMMAND", senior_id="s1", decision="continue", directive="go"),
         entry(route="COMMAND", senior_id="e2", decision="continue", directive="go",
               r1_scope_alignment="PASS", r2_progress="PASS",
               r3_answer_readiness="PASS", r4_premise_verification="PASS")],
        graded={"s1", "s3"}, exploration={"e2"}))
    # directive_violations: routing at seniors that were never spawned, twice.
    _all_tagged(directive_violations(
        [entry(route="RETIRE", senior_id="s9", reason="done"),
         entry(route="COMMAND", senior_id="s8", decision="continue", directive="go"),
         entry(route="CLARIFY", senior_id="s7", clarify_reason="unclear",
               questions=["?"]),
         entry(route="RETIRE", senior_id="s7", reason="done")],
        st))
