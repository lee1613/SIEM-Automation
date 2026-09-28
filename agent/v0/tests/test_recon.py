from case_file import CaseFile
from recon import RECON_TASKS, seed_case_from_recon


def test_recon_task_set_nonempty():
    assert len(RECON_TASKS) >= 4
    assert all(isinstance(t, str) and t.strip() for t in RECON_TASKS)


def test_seed_writes_verified_findings_and_entities(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    fake = [{"subquestion": RECON_TASKS[0], "status": "solved",
             "answer": "FINAL ANSWER: key hosts are BSTOLL-L, FYODOR-L and ABUNGST-L"}]
    n = seed_case_from_recon(cf, fake)
    assert n >= 1
    d = cf.render_digest()
    assert "[OK]" in d                      # seeded as verified baseline
    assert "BSTOLL-L" in d                  # entity regex caught the hostname


def test_seed_skips_failed_results(tmp_path):
    cf = CaseFile(str(tmp_path / "c.json"))
    assert seed_case_from_recon(cf, [{"subquestion": "x", "status": "failed",
                                      "answer": ""}]) == 0
