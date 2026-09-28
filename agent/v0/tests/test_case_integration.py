from case_file import CaseFile
from orchestrator import apply_case_updates


def test_apply_case_updates_writes_entities_and_findings(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    joiner_text = ("FINAL ANSWER: BSTOLL-L\n"
                   "CASE UPDATES:\n"
                   "- entity host BSTOLL-L.froth.ly\n"
                   "- finding [verified] BSTOLL-L is the miner | evidence: cisco:asa")
    n = apply_case_updates(cf, joiner_text, source_qid="Q210")
    assert n == 2
    d = cf.render_digest()
    assert "BSTOLL-L.froth.ly" in d and "miner" in d


def test_apply_case_updates_noop_when_absent(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    assert apply_case_updates(cf, "FINAL ANSWER: x", source_qid="Q1") == 0
