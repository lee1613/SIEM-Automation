# s2 - Q224 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=0_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw (queried FQDN = whitespace token 4)
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 95

## Prior rounds
- R1 (retired senior): lambda:DNS established as the Route 53 feed, FQDN in _raw token 4; its index-wide exclusivity claim was refuted and not rebuilt on.
- R2 (mine): measured 8.10 — 100,393 distinct third-level labels, 813,121 chars, avg 8.099379438805494; two methods and two extractions agreed (0 mismatches over 115,145 events).
- R3 (mine): stream:dns checked directly (only www.brewertalk.com, 107 events); lambda:DNS www=135; three-way partition apex 27 / subdomain 115,118, no other; premise updates filed, but quotes were reformatted paraphrases and p2/p3/p5 stayed open.
- R4 (this): re-filed p2/p3/p5 with the raw result rows quoted word for word.

## This round
### What I ran
- No new searches — all three premises settle on outputs already received. The literal rows now quoted in premise_updates:
  - p2 partition: `{"results": [{"partition": "apex_brewertalk_com", "count": "27"}, {"partition": "subdomain_brewertalk_com", "count": "115118"}], "meta": {"total_event_count": 2, "returned": 2, "sid": "1790142075.386"}}` — two rows, 2 of 2 returned, no "other" row; 27+115,118=115,145.
  - p3 aggregation: `{"results": [{"distinct_labels": "100393", "total_chars": "813121", "avg_len": "8.099379438805494", "min_len": "1", "max_len": "55", "p25": "6", "p75": "9.811162492273263", "avg_rounded": "8.10"}], "meta": {"total_event_count": 1, "returned": 1, "sid": "1790141858.379"}}`.
  - p5 stream:dns: `{"results": [{"query": "www.brewertalk.com", "count": "107"}], "meta": {"total_event_count": 1, "returned": 1, "sid": "1790142062.385"}}`, with the companion lambda:DNS www count `{"results": [{"count": "135"}], "meta": {"total_event_count": 1, "returned": 1, "sid": "1790142095.387"}}` quoted in evidence.

### What it means
FOUND, unchanged: every lambda:DNS event is apex (27) or *.brewertalk.com (115,118) with no other zone; the unit is one row per distinct third-level label (100,393 rows, 813,121 chars → 8.099379438805494 → 8.10); the only rival route, stream:dns, carries just www.brewertalk.com (107 events) and www already appears 135 times in lambda:DNS, so it adds no distinct label. All quotes are now the literal result rows, so the premises can be VERIFIED.

## Ruled out
- Event-weighted average 7.70 — wrong unit; the question says "distinct".
- 27 apex brewertalk.com events — no third-level label exists.
- stream:dns as measurement feed — carries only www.brewertalk.com (107 events), a label already present 135 times in lambda:DNS.