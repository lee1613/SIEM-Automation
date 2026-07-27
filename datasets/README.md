# Datasets

## BOTSv3 (Boss of the SOC v3)

The contents of `botsv3/` — questions, answers, hints, and lookup tables — are
Splunk's **Boss of the SOC v3** dataset, published by Splunk at
<https://github.com/splunk/botsv3>. They are redistributed here under their
original license for benchmarking purposes; they are **not** covered by this
repository's MIT license, which applies only to the code.

`botsv3_questions.json` (56 questions) is the runner's working set. It omits
two of the 58 official questions:

| Omitted | Why |
|---|---|
| Q1 | Warmup ("which company makes this software?" → `splunk`). No investigation required, so scoring it inflates accuracy. |
| Q220 | The answer is an AWS secret access key that is not derivable from the dataset. Unanswerable by any agent working from the logs. |

Both removals lower the reported score rather than raise it: Q1 is a free
point, and Q220 was already a miss.

`ctf_answers.csv` contains Splunk's planted test credentials (e.g. an
AWS-secret-key-shaped string for Q220). These are fabricated CTF artifacts
published by Splunk, not live secrets. Automated secret scanners may flag
them.
