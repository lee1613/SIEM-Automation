# s2 - Q224 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=4_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw (qname = 4th whitespace token, via rex)
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 95

## Prior rounds
- s1 (stream:dns): only brewertalk.com query there was www.brewertalk.com (label www, len 3); provisional 3.00; flagged aws:cloudwatchlogs as untested.
- Round 2 (mine): lambda:DNS found under aws:cloudwatchlogs — 115,145 Route 53 query-log events, all brewertalk.com; label-dedup avg 8.099379 (100,393 labels) and depth-1-only 8.103654 (100,083) both -> 8.10; submitted 8.10 at confidence 88.

## This round
### What I ran
- One SPL computing all three readings side by side -> R1 (immediate-left label, every qname): n=100393, avg 8.099379, 8.10; R2 (only label.brewertalk.com form): n=100083, avg 8.103654, 8.10; R3 (dedup on full qname): n=114427, avg 7.712725, 7.71.
- err0r-tagged events: `stats count by _raw` and `rare _raw` both dropped the text column; `eval raw=_raw | stats count by raw` -> all 5 are ordinary query lines (error., fatal., www.error., www.fatal., fatal-encount-com.brewertalk.com).

### What it means
The question's example (my.example.company.com -> example) counts labels from the right, so the third-level subdomain of any brewertalk.com qname is the label immediately left of brewertalk.com — reading R1, 8.099379 -> 8.10. The rival reading R2 gives 8.103654 -> 8.10. Both readings SH named converge on 8.10, so the ambiguity cannot affect scoring; p4 is settled VERIFIED on that output. R3 (7.71) is not a reading of "third-level subdomain" at all — it dedups full qnames, while the question's example defines the subdomain as the label, so distinct subdomains means distinct labels; excluded on wording. The 5 err0r events are genuine queries whose labels legitimately belong to the set — the last unchecked rows in the feed are now read. www, stream:dns's only label, occurs 135 times here, so the union adds no label and 8.10 stands either way. The answer-ready metric is 8.10.

## Ruled out
- R3 qname-dedup weighting (7.71) — dedups qnames, not subdomains; contradicts the question's own example.
- err0r-tagged events as contamination — all 5 read; ordinary Route 53 query lines.
- Apex queries (brewertalk.com, 27 events) — no third-level label to measure.
- stream:dns union changing the value — www already in the label set (135 events in lambda:DNS).