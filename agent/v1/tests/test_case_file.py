from case_file import CaseFile, parse_case_updates


def test_add_and_render_entity_and_finding(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    cf.add_entity("host", "BSTOLL-L.froth.ly", qid="Q210")
    cf.add_finding("BSTOLL-L mined Monero", evidence="cisco:asa flow",
                   source_qid="Q210", status="hypothesis", confidence=0.6)
    d = cf.render_digest()
    assert "BSTOLL-L.froth.ly" in d
    assert "[?]" in d          # hypothesis marker


def test_finding_status_promote_and_refute(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    fid = cf.add_finding("miner is FYODOR-L", evidence="tcp connect",
                         source_qid="Q210", status="hypothesis", confidence=0.5)
    cf.set_status(fid, "refuted")
    assert cf.get_finding(fid)["status"] == "refuted"
    assert "[X]" in cf.render_digest()


def test_persist_and_reload(tmp_path):
    p = str(tmp_path / "case.json")
    CaseFile(p).add_entity("user", "mkraeusen", qid="Q330")
    assert "mkraeusen" in CaseFile(p).render_digest()


def test_digest_is_bounded(tmp_path):
    cf = CaseFile(str(tmp_path / "case.json"))
    for i in range(500):
        cf.add_finding(f"finding number {i} with some text", evidence="x",
                       source_qid=f"Q{i}", status="verified", confidence=0.9)
    assert len(cf.render_digest(max_chars=4000)) <= 4000


def test_parse_case_updates_block():
    text = '''FINAL ANSWER: BSTOLL-L
CASE UPDATES:
- entity host BSTOLL-L.froth.ly
- finding [verified] BSTOLL-L is the Monero miner | evidence: cisco:asa message_id 113019
'''
    updates = parse_case_updates(text)
    assert any(u["kind"] == "entity" and "BSTOLL-L" in u["value"] for u in updates)
    assert any(u["kind"] == "finding" and u["status"] == "verified" for u in updates)


def test_parse_case_updates_absent_returns_empty():
    assert parse_case_updates("FINAL ANSWER: x\n(no updates)") == []
