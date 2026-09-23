# s2 - Q224 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=9_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw (queried FQDN = whitespace token 4)
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 90

## Prior rounds
- R1 (retired senior): established lambda:DNS as the Route 53 feed and that the FQDN sits in _raw; its "exactly two feeds" coverage claim was refuted by SH and was not rebuilt on. This is my first active round.

## This round
### What I ran
- get_raw_events source=lambda:DNS (3 rows) -> Route 53 public query log: `1.0 <ts> <zone> <QUERY_NAME> <qtype> <rcode> <proto> <edge> <resolver_ip> <qid>`; FQDN = token 4.
- Shape/coverage: rex FQDN + `(?<third>[^.]+)\.brewertalk\.com$` + label counts -> 115,145 events; 115,118 carry *.brewertalk.com; 100,393 distinct third-level labels (dc(lower(third)) identical, so case cannot change the set); 14,399 events have 4+ labels.
- `search NOT fqdn="*.brewertalk.com" | stats count by fqdn` -> only the apex `brewertalk.com`, 27 events; 115,118+27 = 115,145, every event accounted for, no other zone queried.
- Distinct-unit measurement: `stats count by third | eval l=len(third) | stats count, sum(l), avg(l), min(l), max(l), perc25(l), perc75(l)` -> 100,393 labels, 813,121 chars, avg 8.099379438805494, min 1, max 55, p25 6, p75 9.81; round(avg,2) = 8.10.
- Independent method 2: `eval third=mvindex(split(fqdn,"."),-3) | dedup third | stats avg(eval(len(third)))` -> identical 8.099379438805494 -> 8.10.
- Extraction agreement: rex third vs mvindex(split(fqdn,"."),-3) over all 115,145 events -> 0 mismatches, 0 unexpected nulls.
- 4+-label sample -> `0907_n_hn.m.brewertalk.com`, `10dc-g-siteoffice-mfp-bw.csg.brewertalk.com`; third-level label = the label directly under brewertalk.com (`m`, `csg`), exactly the question's example pattern (my.example.company.com -> example).

### What it means
FOUND: every lambda:DNS queried name is brewertalk.com or *.brewertalk.com; the third-level label is the one immediately left of brewertalk.com (per the question's own 4-label example); there are 100,393 distinct such labels totalling 813,121 characters; 813,121/100,393 = 8.099379438805494, rounded to two decimals = 8.10. Two independent SPL methods (group-then-average, dedup-then-average) agree exactly, and two independent extractions (rex, mvindex) agree on all 115,145 events. All arithmetic and rounding done inside SPL.

## Ruled out
- Event-weighted average 7.70 (avg over 115,118 events) - wrong unit; the question averages over DISTINCT subdomains.
- 27 apex `brewertalk.com` events - no third-level label exists.
- sourcetype=stream:dns - not the Route 53 log the question names; not used.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p3 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
