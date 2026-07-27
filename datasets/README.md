# Datasets

The repository's root MIT license covers project-authored software and
documentation. It does not relicense the source datasets or Splunk challenge
materials described below.

## BOTSv3 event dataset

`botsv3/botsv3_data_set/` is the extracted pre-indexed event dataset published
by Splunk's official [`splunk/botsv3`](https://github.com/splunk/botsv3)
repository. The official download is
[`botsv3_data_set.tgz`](https://botsdataset.s3.amazonaws.com/botsv3/botsv3_data_set.tgz)
(320.1 MB, MD5
`d7ccca99a01cff070dff3c139cdc10eb`), and both the primary repository and the
bundled dataset license identify it as CC0-1.0. The lookup tables under the
extracted app belong to this event-dataset lineage.

## BOTSv3 challenge and scoreboard materials

`botsv3/ctf_questions.csv`, `botsv3/ctf_answers.csv`, and
`botsv3/ctf_hints.csv` have a separate, auditable lineage. Project history
records the acquisition channel as the three-file Splunk package requested
from `bots@splunk.com`: commit `84d21d7` documents that route, commit
`44842b2` adds the files under `botsv3content/`, and commit `a5853aa` moves
them here. Their current Git blob IDs match the originally added blobs.

Those CSVs do **not** come from `splunk/botsv3`. They are also absent from the
official
[`SA-ctf_scoreboard`](https://github.com/splunk/SA-ctf_scoreboard) and
[`SA-ctf_scoreboard_admin`](https://github.com/splunk/SA-ctf_scoreboard_admin)
repositories: the scoreboard README tells operators to obtain and import the
three files, but the repositories distribute the reusable apps, not BOTSv3's
challenge content. Both app repositories declare CC0-1.0 for their own
contents; that is app provenance, not evidence that the CSVs were acquired
from either repository.

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
