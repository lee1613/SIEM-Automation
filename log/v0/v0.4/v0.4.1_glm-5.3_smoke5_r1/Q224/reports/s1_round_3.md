# s1 - Q224 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=2_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw, qname (rex-extracted)
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 97

## Prior rounds
- Round 1: Located the Route 53 query log feed (aws:cloudwatchlogs / lambda:DNS, 115,145 events, qname = 4th raw token); 114,428 distinct brewertalk qnames; averaging query not reached.
- Round 2: Verified coverage (all *brewertalk* records end in .brewertalk.com or are brewertalk.com itself; zero parse failures), computed avg = 8.10 with sum/count cross-check; extremes inspected. One Ruled out line (3-label reading "same label set") was inference and is retracted.
- Round 3: Re-ran population check and computation as fully read single-row results; both reproduce round 2 exactly.

## This round
### What I ran
- Population check: rex qname -> where ends .brewertalk.com and != brewertalk.com -> stats count, dc(qname) -> 1 row: 115,118 events, 114,427 distinct queried names.
- Computation: same base -> sub = label adjacent to brewertalk.com -> stats dc(qname) by sub -> len -> stats count, sum, avg -> 1 row: 100,393 distinct subs, 813,121 total chars, avg 8.099379, round(avg,2) = 8.10; check = sum/count = 8.099379.

### What it means
114,427 distinct queried names under .brewertalk.com (brewertalk.com itself excluded) yield 100,393 distinct third-level subdomain labels; their average character length is 8.099379, which rounds to 8.10. Both SPL formulations (avg() and sum/count) agree exactly, and both results this round are single-row, fully read — no partial listings contributed.

## Assumptions
- Coverage: every *brewertalk* record in lambda:DNS either is exactly brewertalk.com or ends in .brewertalk.com; no substring-only matches - VERIFIED (round 2 category eval, 2 of 2 rows read; re-confirmed this round by the population count matching the round-2 total).
- Definition: third-level subdomain = label immediately below brewertalk.com, from queried names at any depth, brewertalk.com itself excluded - VERIFIED as applied (per SH's ruling).
- qname = 4th whitespace token of _raw - VERIFIED (round 1 samples; zero rex failures across all events).

## Ruled out
- stream:dns as source (only www.brewertalk.com); aws:cloudwatch (no Route 53 source); the retracted round-2 claim that the 3-label-only reading produces the same label set (3-label qnames = 100,083 distinct vs 100,393 labels at any depth — the readings differ; the submitted value follows the any-depth definition).

## Open questions for SH
- None.