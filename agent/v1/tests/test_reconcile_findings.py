from case_file import CaseFile, reconcile_findings


def test_wrong_verdict_demotes_verified_to_hypothesis(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("endpoint mined for 0 seconds", source_qid="Q216",
                         status="verified")
    other = cf.add_finding("password is ilovedavidverve", source_qid="Q303",
                           status="verified")
    n = reconcile_findings(cf, "Q216", correct=False)
    assert n == 1
    assert cf.get_finding(fid)["status"] == "hypothesis"
    assert cf.get_finding(other)["status"] == "verified"   # other qid untouched


def test_correct_verdict_keeps_verified(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fid = cf.add_finding("password is ilovedavidverve", source_qid="Q303",
                         status="verified")
    assert reconcile_findings(cf, "Q303", correct=True) == 0
    assert cf.get_finding(fid)["status"] == "verified"


def test_refuted_and_hypothesis_untouched_on_wrong(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    h = cf.add_finding("maybe", source_qid="Q330", status="hypothesis")
    r = cf.add_finding("nope", source_qid="Q330", status="refuted")
    assert reconcile_findings(cf, "Q330", correct=False) == 0
    assert cf.get_finding(h)["status"] == "hypothesis"
    assert cf.get_finding(r)["status"] == "refuted"
