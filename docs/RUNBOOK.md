# Runbook

## Offline evaluation (no API key, no Splunk)

Requires Python 3.10 or newer. The evaluator uses only the Python standard library.

```bash
git clone https://github.com/lee1613/SIEM-Automation.git
cd SIEM-Automation
python3 scripts/run_eval.py                 # full latest run
python3 scripts/run_eval.py --tier 1000     # the hard tier: 2/9
python3 scripts/run_eval.py --ids Q332,Q333 # the two CVE hits
python3 scripts/run_eval.py --run run_1.1   # 26/56 for $0.63
```

Verified output for the hard tier (`python3 scripts/run_eval.py --tier 1000`):

```text
Run:      run_1.2
Accuracy: 2/9 = 22.2%
Points:   2000 / 9000

By tier:
  1000 pt    2/9    22.2%

Cost:     $31.36 (whole run)
  zai-org/GLM-5.2-FP8          $26.5326
  gpt-5.4-2026-03-05           $4.8297
  Qwen/Qwen3.6-27B             $0.0000
```

## Running the tests

```bash
pip install -r agent/requirements.txt pytest ruff && pytest -q && ruff check .
```

## Live runs (requires Splunk + API keys)

Install and load Splunk and the BOTSv3 data first; see [the BOTSv3 setup guide](BOTS_V3_SETUP.md). Copy `agent/.env.example` to `agent/.env` and provide the Splunk credentials and API keys it describes.

Run this five-question smoke test before any full run:

```bash
python agent/v1/run_all_v1.py --ids Q216,Q217,Q224,Q328,Q329
```

A full 56-question v1.2 run cost **$31.36**. Smoke tests cover five questions and write their logs to `log/temp/`.

## Regenerating the leaderboard after a run

```bash
python3 scripts/run_eval.py --write
```

CI verifies the generated leaderboard with `python3 scripts/run_eval.py --check`.
