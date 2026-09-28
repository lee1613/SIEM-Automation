# s1 - Q224 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw (qname via rex); stream:dns checked and ruled out
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1: Located the Route 53 resolver query log feed (aws:cloudwatchlogs / source=lambda:DNS, 115,145 events, raw text, qname = 4th token); counted 114,428 distinct brewertalk qnames and their label-depth distribution; the averaging query itself was not reached before the iteration cap.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; DNS-relevant: stream:dns, aws:cloudwatch, aws:cloudwatchlogs.
- `index=botsv3 sourcetype=stream:dns query="*brewertalk.com" | stats count by query` -> only www.brewertalk.com (107 events).
- stream:dns queries/query{}/name{} for brewertalk -> www.brewertalk.com only; name{} shows brewertalk.com NS = ns-1224.awsdns-25.org, ns-2003.awsdns-58.co.uk, ns-259.awsdns-32.com, ns-565.awsdns-06.net (confirms Route 53 hosting).
- get_sources aws:cloudwatch -> no Route 53 source (RDS/EC2/Lambda/EBS/AppELB only).
- get_sources aws:cloudwatchlogs -> single source lambda:DNS (115,145 events).
- get_raw_events lambda:DNS -> format `1.0 <ts> Z149R7NEBZTKPN <qname> <type> <rcode> <proto> <edge> <ip> -` (Route 53 resolver query log).
- `*brewertalk*` + rex qname + stats dc -> 114,428 distinct qnames / 115,145 events.
- Label-count distribution (distinct qnames / events): 2 -> 1/27 (brewertalk.com itself); 3 -> 100,083/100,719; 4 -> 13,656/13,707; 5 -> 621/625; 6 -> 42/42; 7 -> 4/4; 8 -> 21/21.

### What it means
The question's Route 53 pointer resolves to lambda:DNS, which holds the full population of brewertalk.com queries (100,083 distinct x.brewertalk.com names). The averaging computation is exactly one query away (SPL ready in notes) but was not executed before the cap, so no number is submitted.

## Assumptions
- Coverage: stream:dns (query/queries/query{}/name{} — only www.brewertalk.com), aws:cloudwatch (no R53 source), aws:cloudwatchlogs lambda:DNS (the feed, raw text) - VERIFIED. UNVERIFIED: whether any *brewertalk* match does not end in .brewertalk.com (e.g. brewertalk.co.uk); the next query's `qname="*.brewertalk.com"` filter closes this.
- Selection: lambda:DNS over stream:dns because the question names Route 53 and lambda:DNS is the Route 53 resolver query log with 114,428 distinct brewertalk qnames vs stream:dns's single www - VERIFIED by the counts above.
- Definition premise: "third-level subdomain" = label immediately below brewertalk.com. Two readings: (a) only 3-label qnames x.brewertalk.com (SH's framing); (b) third label from the right at any depth (www.forumtest.brewertalk.com -> forumtest), per the question's example my.example.company.com -> example - UNRESOLVED, both SPL variants prepared.
- qname is the 4th whitespace token in _raw - VERIFIED by 5 sampled raw events and consistent rex stats (114,428 distinct from 115,145 events).

## Ruled out
- stream:dns as answer source - only www.brewertalk.com (1 distinct third-level subdomain, "www", avg 3.00); trivial and contradicts the Route 53 pointer.
- aws:cloudwatch - no Route 53 source exists in it.

## Open questions for SH
- Interpretation (a) vs (b): should 4+ label qnames (13,656+ distinct) contribute their third label (e.g. forumtest from www.forumtest.brewertalk.com) to the distinct set, or only exactly-one-label-below names?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_r…` (0 of 1 rows seen). A claim resting on them alone is UNVERIFIED._
