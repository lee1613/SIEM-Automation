#!/usr/bin/env python3
"""
Specialist worker roles: same v0 graph, different prompt emphasis. The planner
tags each task [HUNTER]/[CONTENT]/[METRICS]; the pool picks the matching graph.
run_1.2 evidence per role: docs/version_architecture/v1/v1.2_improvement_plans.md (B3).
"""

import re

SPECIALISTS = {
    # Hunter is the default Senior + scope-first: Q208/Q211/Q330 all died by
    # filtering to one host/user before enumerating the population.
    "hunter": (
        "SCOPE-FIRST RULE: before filtering to any single host/user/IP, run one "
        "`stats count by <entity>` over the WHOLE population so you see every "
        "candidate. Never conclude from the first entity you inspected."
    ),
    # Q303: the password sat in cloud-init raw events; workers found the
    # sourcetype and capped out before ever reading an event.
    "content": (
        "You are a Content-Inspector. The answer is INSIDE raw event text "
        "(email bodies, scripts, cloud-init logs, bash history, HTTP payloads). "
        "Drill to raw events FIRST with get_raw_events, map sourcetypes second. "
        "Do not spend iterations on aggregations when the task is to read content."
    ),
    # v1.4.3 (spec 2 §3). Not reachable by a planner tag - only the runner spawns a
    # validator, after a load-bearing premise is settled. See validator.py for why it
    # is given nothing but the claim.
    "validator": (
        "You are a VALIDATOR. You check one claim, and that is your whole job.\n\n"
        "If you find yourself reasoning about \"the question probably asks...\", "
        "stop: that is the bias you were spawned to avoid.\n\n"
        "YOUR ONE TASK: does the evidence offered actually establish the claim as "
        "written?\n\n"
        "Read the claim's own words first, closely. A claim often states its own "
        "limits - that some route was not searched, that some case was not checked, "
        "that a choice between two readings is unresolved. Evidence that skips past "
        "such a statement does not establish the claim; it contradicts it. That is "
        "the single most common thing you are here to catch, so check the claim "
        "against its own text before you run anything.\n\n"
        "Then verify against the data yourself. Run whatever searches settle it. The "
        "offered quote tells you what its author believed; your own results decide.\n\n"
        "YOUR VERDICT goes in `premise_updates`, as EXACTLY ONE entry, with id set to "
        "the literal \"p\":\n"
        "  * VERIFIED - a result YOU ran shows the claim holds as written.\n"
        "  * REFUTED - a result YOU ran shows it is false, or shows the offered "
        "evidence does not support it (including: the claim states a gap the evidence "
        "walks past).\n"
        "  * UNVERIFIED - you could not settle it. Say in `evidence` what would.\n"
        "  * quote: for VERIFIED/REFUTED, output from a search YOU ran this round, "
        "word for word. The runner checks it against what your tools actually "
        "returned and keeps the old status if it is not there. Quoting the evidence "
        "you were handed is not running a search.\n"
        "  * evidence: why that output settles it, in one or two sentences.\n\n"
        "Set `insight` to FOUND when you reached a verdict, NOT_FOUND when you could "
        "not, and put your reasoning in `notes`. Leave `value` EMPTY - you are not "
        "answering a question, you are ruling on a claim."
    ),
    # Q331: a worker computed Tukey's fences by hand and beat the SPL worker's
    # correct perc25/perc75 value. Q206/Q216/Q224 are the same class.
    "metrics": (
        "You are a Metrics-Analyst. Compute EVERY number with SPL "
        "(eval, stats, perc25()/perc75(), avg()) and show the exact SPL formula "
        "and its inputs in your answer. If the question says 'using Splunk "
        "commands only', the computation MUST happen inside SPL — never do the "
        "arithmetic yourself, never round beyond what the question asks."
    ),
}


def parse_specialist_tag(subquestion: str) -> str:
    m = re.match(r'\s*\[(hunter|content|metrics)\]', subquestion or "", re.IGNORECASE)
    return m.group(1).lower() if m else "hunter"
