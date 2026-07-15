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
