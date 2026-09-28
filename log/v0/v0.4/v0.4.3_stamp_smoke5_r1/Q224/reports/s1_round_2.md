# s1 - Q224 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=aws:cloudwatchlogs, stream:dns | source=lambda:DNS | fields=_raw (query name = 4th whitespace token)
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 95

## Prior rounds
- R1: Established source=lambda:DNS (115,145 events, 100% brewertalk.com, 114,428 distinct query names, rex on token 4 of _raw, 0 failures); label depths 2-8, all lowercase, all end .brewertalk.com; avg not yet computed (tool cap).

## This round
### What I ran
- sourcetype=stream:dns brewertalk.com -> 0 events; stream:dns alone -> 218,456 events (feed non-empty, negative is meaningful)
- lambda:DNS wildcard/trailing-dot check -> single row: no/no across all 114,428 distinct names
- Final SPL: rex token 4 -> exclude apex + require \.brewertalk\.com$ -> rex "(?<third_level>[^.]+)\.brewertalk\.com$" -> eval tl_len=len(third_level) -> dedup third_level -> stats avg(tl_len), dc, max, min -> **avg_len=8.10, distinct=100,393, max=55, min=1**
- Length distribution (48 rows, all returned, sums exactly to 100,393; weighted sum 813,121 → 8.0994 → 8.10, matches SPL)
- One-char labels -> 36 values: digits 0-9 and letters a-z (ordinary enumeration subdomains, kept)

### What it means
FOUND. The average character length of the distinct third-level subdomains in Route 53 queries to brewertalk.com is **8.10**, computed entirely in SPL (avg(len(third_level)) over the deduped set, round(...,2)). Denominator: 100,393 distinct third-level labels. Field path: query name = 4th whitespace token of _raw in source=lambda:DNS (no extracted field exists — fieldsummary shows only default fields; rex failed on 0 of 115,145 events). Exclusions: apex brewertalk.com (no third-level label). Wildcards: none. Trailing dots: none. Deeper names: third level = label immediately left of brewertalk.com (zone100.cepi.brewertalk.com → "cepi"), per the question's example. 114,427 subdomain-bearing distinct names collapse to 100,393 distinct labels because 4+ label names share third-level labels.

## Ruled out
- stream:dns as a source of brewertalk.com query names — 218,456 events in the feed, zero mention brewertalk.com
- Wildcard labels (*.brewertalk.com) — 0 of 114,428 distinct names contain "*"
- Trailing-dot names — 0 of 114,428 end in "."
- Extracted/indexed fields in lambda:DNS — only default fields exist; name is in raw text only

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The distinct set being averaged is the set of distinct third-level labels (label"
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
