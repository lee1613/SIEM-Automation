from case_file import CaseFile
from orchestrator import promote_from_verdict


def test_confirmed_promotes_to_verified(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("BSTOLL-L is the miner", source_qid="Q210",
                         status="hypothesis")
    promote_from_verdict(cf, "BSTOLL-L", {"verdict": "confirmed", "correction": ""})
    assert cf.get_finding(fid)["status"] == "verified"


def test_refuted_marks_refuted(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("FYODOR-L is the miner", source_qid="Q210",
                         status="hypothesis")
    promote_from_verdict(cf, "FYODOR-L",
                         {"verdict": "refuted", "correction": "BSTOLL-L"})
    assert cf.get_finding(fid)["status"] == "refuted"


def test_empty_answer_is_noop(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("something", source_qid="Q1", status="hypothesis")
    promote_from_verdict(cf, "", {"verdict": "confirmed", "correction": ""})
    assert cf.get_finding(fid)["status"] == "hypothesis"


def test_no_substring_match_does_not_promote(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("BSTOLL-L is the miner", source_qid="Q210",
                         status="hypothesis")
    promote_from_verdict(cf, "FYODOR-L", {"verdict": "confirmed", "correction": ""})
    assert cf.get_finding(fid)["status"] == "hypothesis"


def test_short_answer_below_min_length_does_not_promote(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("found 9 files in FY2019 share", source_qid="Q210",
                         status="hypothesis")
    promote_from_verdict(cf, "9", {"verdict": "refuted", "correction": ""})
    assert cf.get_finding(fid)["status"] == "hypothesis"


def test_recon_finding_is_skipped(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("BSTOLL-L is the miner", source_qid="RECON",
                         status="verified")
    promote_from_verdict(cf, "BSTOLL-L", {"verdict": "refuted", "correction": ""})
    assert cf.get_finding(fid)["status"] == "verified"
