from orchestrator import build_handoff_digest


def _rec(status="failed", cap_hit=False):
    return {"status": status, "cap_hit": cap_hit, "iterations": 25,
            "answer": "Searched cloudwatch logs... found the cloud-init sourcetype "
                      "but ran out of iterations before reading raw events.",
            "spl_used": ["search index=botsv3 sourcetype=aws:cloudwatchlogs | stats count",
                         "search index=botsv3 sourcetype=lastlog | head 5"],
            "sourcetypes": ["aws:cloudwatchlogs", "lastlog"],
            "worker": "senior#7", "subquestion": "Find the Tomcat password"}


def test_digest_names_sourcetypes_spl_and_trail():
    d = build_handoff_digest(_rec())
    assert "aws:cloudwatchlogs" in d
    assert "sourcetype=lastlog" in d
    assert "do NOT repeat" in d
    assert "ran out of iterations" in d


def test_digest_is_bounded():
    rec = _rec()
    rec["answer"] = "x" * 10000
    rec["spl_used"] = [f"search very long query number {i} " + "y" * 300
                      for i in range(40)]
    assert len(build_handoff_digest(rec)) <= 1500


def test_digest_labels_cap_hit():
    d = build_handoff_digest(_rec(status="solved", cap_hit=True))
    assert "cap-hit" in d.lower()
