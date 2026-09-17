import os

from conversation_log import ConversationLog


def _log(tmp_path):
    return ConversationLog(str(tmp_path), "Q216")


def _text(log):
    with open(log.conversation_path, encoding="utf-8") as f:
        return f.read()


def test_it_creates_the_question_directory_tree(tmp_path):
    log = _log(tmp_path)
    assert os.path.isdir(os.path.join(str(tmp_path), "Q216", "reports"))
    assert os.path.isdir(os.path.join(str(tmp_path), "Q216", "handoffs"))
    assert os.path.exists(log.conversation_path)


def test_a_spawn_renders_with_its_constraints_and_reason(tmp_path):
    log = _log(tmp_path)
    log.sh_to_senior("s2", "SPAWN",
                     body="**Constraints:** sourcetype=aws:cloudtrail\n"
                          "**Technique:** hunter\n**Reason:** IAM lives here.")
    t = _text(log)
    assert "SH -> s2" in t and "[SPAWN]" in t
    assert "aws:cloudtrail" in t and "IAM lives here." in t


def test_a_report_renders_as_an_excerpt_with_a_link_to_the_full_file(tmp_path):
    log = _log(tmp_path)
    rel = log.write_report("s2", 1, "# s2 - Q216 - Round 1\nbody text here")
    log.senior_to_sh("s2", round_n=1, insight="NOT_FOUND",
                     excerpt="Scope carries no per-user field.", path=rel)
    t = _text(log)
    assert "s2 -> SH" in t and "[REPORT - round 1 - NOT_FOUND]" in t
    assert "> Scope carries no per-user field." in t
    assert rel in t
    assert os.path.exists(os.path.join(str(tmp_path), "Q216", rel))


def test_every_route_type_has_a_rendering(tmp_path):
    log = _log(tmp_path)
    for route in ("COMMAND", "CRITIC", "CLARIFY", "RETIRE", "ANSWER"):
        log.sh_to_senior("s1", route, body=f"{route} body")
    t = _text(log)
    for route in ("COMMAND", "CRITIC", "CLARIFY", "RETIRE", "ANSWER"):
        assert f"[{route}]" in t


def test_a_clarify_reply_renders_as_its_own_message(tmp_path):
    log = _log(tmp_path)
    log.clarify_reply("s2", "The one you gave me.")
    t = _text(log)
    assert "[CLARIFY REPLY]" in t and "The one you gave me." in t


def test_a_handoff_is_written_and_announced(tmp_path):
    log = _log(tmp_path)
    rel = log.write_handoff("s2", "# s2 handoff\n## What I'd tell my replacement\n- x")
    assert os.path.exists(os.path.join(str(tmp_path), "Q216", rel))
    assert rel in _text(log)


def test_messages_are_appended_in_order(tmp_path):
    log = _log(tmp_path)
    log.sh_to_senior("s1", "SPAWN", body="first")
    log.senior_to_sh("s1", round_n=1, insight="FOUND", excerpt="second", path="reports/x.md")
    log.sh_to_senior("s1", "ANSWER", body="third")
    t = _text(log)
    assert t.index("first") < t.index("second") < t.index("third")
