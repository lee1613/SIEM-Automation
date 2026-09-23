# s1 - Q224 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=2_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw (queried FQDN = 4th whitespace token)
**Insight:** partial — feed and field verified, average not yet computed
**Candidate:** none   **Confidence:** 0

## Prior rounds
- None; this is round 1.

## This round
### What I ran
- get_sources keyword=route53 -> 0 rows; no source is literally named route53.
- get_sources keyword=dns -> DNS feeds: stream:dns (175,094 events) and lambda:DNS under sourcetype=aws:cloudwatchlogs.
- get_sourcetype_fields stream:dns -> `query` field carries the FQDN (194,277 events).
- `index=botsv3 sourcetype=stream:dns query="*brewertalk.com" | stats count by query` -> 1 row: www.brewertalk.com, 107 events.
- get_sourcetype_fields aws:cloudwatchlogs source=lambda:DNS -> 115,145 events, no extracted DNS fields; everything is in _raw.
- sample_events lambda:DNS -> Route 53 public query log lines: `1.0 <ts> <zone-id> <query-name> <type> <rcode> <proto> <edge> <resolver-ip> <edns>`; samples users1/ccmail/koko10.brewertalk.com.
- rex of token 4 | stats dc(query_name) -> 114,428 distinct FQDNs.

### What it means
The question's data is located and its field verified: the Route 53 DNS query log is source=lambda:DNS (sourcetype=aws:cloudwatchlogs), and the queried FQDN is the 4th whitespace token of _raw — confirmed by reading raw events, since this feed has zero extracted fields. The distinct-FQDN count (114,428) shows the aggregation must be done in SPL, not by listing. The average label length itself was NOT computed: the iteration budget ran out one step before the final aggregation, so no numeric candidate exists and none is invented. The exact finishing SPL is written out in notes and needs a single query next round.

## Ruled out
- stream:dns as the record set — its only brewertalk.com query is www.brewertalk.com (107 events); it is the on-prem stream capture, not Route 53, and cannot yield a meaningful distinct-subdomain average.
- A source named route53 — none exists; Route 53 logs live under lambda:DNS.
- Extracted fields in lambda:DNS — none exist; rex on _raw is required.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sources: {"keyword": "dns"}` (50 of 100 rows seen). A claim resting on them alone is UNVERIFIED._
