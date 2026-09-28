#!/usr/bin/env python3
"""
Phase-0 recon: build the incident skeleton once, before the question loop,
and seed the case file as verified baseline. run_0.2: Q310 chased the wrong
phishing wave, Q329 read the wrong uploaded file — both are scoping errors a
one-time incident narrative prevents.
"""

import concurrent.futures
import re

RECON_TASKS = [
    "[HUNTER] Inventory the BOTSv3 dataset: list every sourcetype in "
    "index=botsv3 with its event count and earliest/latest event time "
    "(| metadata or | tstats). Name the 10 highest-volume sourcetypes.",
    "[HUNTER] Enumerate the key Frothly endpoint hosts and their users: "
    "stats count by host over the Windows/endpoint sourcetypes; for each of "
    "the top hosts name the primary user account seen on it.",
    "[CONTENT] Map the phishing story: find every inbound email with an "
    "attachment in the email sourcetype(s); for EACH wave give the send time, "
    "sender, recipients, attachment filename and type.",
    "[HUNTER] Map external attack infrastructure: suspicious/repeated external "
    "IPs and domains in web, firewall and DNS sourcetypes (scanning, C2 "
    "beaconing, cryptomining pools), each with its role and time window.",
    "[HUNTER] Summarize the AWS/cloud story: which IAM users and access keys "
    "appear in aws:cloudtrail, which S3 buckets are touched (esp. public "
    "access/policy changes), and any EC2 activity worth noting.",
]

_HOSTLIKE = re.compile(r'\b[A-Z][A-Z0-9]+-L\b')          # BSTOLL-L, FYODOR-L, ...


def seed_case_from_recon(case_file, results: list) -> int:
    """Write usable recon answers into the case file as verified baseline.
    Returns number of findings written."""
    n = 0
    for r in results:
        answer = (r.get("answer") or "").strip()
        if not answer or r.get("status") in ("failed", "too_big"):
            continue
        case_file.add_finding(answer[:600], evidence="recon",
                              source_qid="RECON", status="verified",
                              confidence=0.8)
        n += 1
        for host in set(_HOSTLIKE.findall(answer)):
            case_file.add_entity("host", host, qid="RECON")
    return n


def run_recon(ctx) -> list[dict]:
    """Dispatch RECON_TASKS in parallel through the existing pool (mirrors
    executor_node's ThreadPoolExecutor pattern; qid label 'RECON')."""
    from langsmith.run_helpers import get_current_run_tree
    from orchestrator import MAX_WORKERS, _run_senior

    ctx.reset_question("RECON", points=0, question="Phase-0 incident recon")
    parent = get_current_run_tree()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        futs = {}
        for t in RECON_TASKS:
            widx = ctx.logger.next_worker("senior", "RECON")
            futs[exe.submit(_run_senior, ctx, t, widx, parent)] = t
        for fut, t in futs.items():
            try:
                r = fut.result()
            except Exception as exc:
                r = {"status": "failed", "answer": f"recon worker crashed: {exc}"}
            r["subquestion"] = t
            results.append(r)
    return results
