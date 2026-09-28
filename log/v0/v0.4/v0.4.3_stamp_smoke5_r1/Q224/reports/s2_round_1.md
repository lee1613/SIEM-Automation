# s2 - Q224 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw (qname = 4th whitespace token, via rex)
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 88

## Prior rounds
- s1 (stream:dns scope): only brewertalk.com query there was www.brewertalk.com (label www, len 3); provisional 3.00; flagged aws:cloudwatchlogs as the untested Route 53-adjacent feed.

## This round
### What I ran
- get_sources sourcetype=aws:cloudwatchlogs -> one source: lambda:DNS, 115,145 events.
- get_sourcetype_fields -> no FQDN-bearing field (host/index/punct only); 5 events tagged err0r.
- get_raw_events "brewertalk.com" -> Route 53 query-log lines: `1.0 <ts> <zone> <qname> <type> <rcode> <proto> <edge> <resolver> -`.
- `... source="lambda:DNS" brewertalk.com | rex ... | stats count, dc(qname), count(eval(qname="www.brewertalk.com"))` -> 115,145 events, 114,428 distinct qnames, www 135 times, rex unmatched 0.
- Shape classification over the whole feed -> 27 apex + 115,118 subdomain; all lowercase, no trailing dots, no foreign-suffix (brewertalk.com.evil) shapes.
- Primary metric: `rex "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | eval q2=rtrim(qname,".") | where match(q2,"\.brewertalk\.com$") AND q2!="brewertalk.com" | eval stripped=replace(q2,"\.brewertalk\.com$","") | eval label=mvindex(split(stripped,"."),-1) | stats count by label | eval label_len=len(label) | stats dc, avg, min, max` -> 100,393 distinct labels, avg 8.099379, min 1, max 55 -> 8.10.
- Depth distribution -> depth-1: 100,083 distinct; depth-2: 13,656; depth-3: 621; depth-4: 42; depth-5: 4; depth-6: 21.
- Rival reading (`where depth=1`) -> 100,083 distinct labels, avg 8.103654 -> 8.10.

### What it means
lambda:DNS is Route 53 DNS query logging — the "Amazon Route 53 DNS web service" the question names — and every one of its 115,145 events is a query to brewertalk.com. Taking the label immediately left of brewertalk.com (the question's example: my.example.company.com -> example), deduplicating labels, and averaging length in SPL gives 8.099379 -> 8.10. The rival reading — only hosts of the form label.brewertalk.com, excluding deeper hosts like www.forumtest.brewertalk.com — gives 8.103654 -> 8.10, so the depth ambiguity cannot change the answer at two decimals. www, stream:dns's only label, occurs 135 times here, so unioning stream:dns adds no label and leaves 8.10 intact. This supersedes s1's 3.00, which rested on a single label from a feed that carries a vanishingly small share of the queries.

## Ruled out
- aws:cloudwatchlogs extracted fields as FQDN carriers — none exist; qname is raw-text token 4.
- Apex queries (brewertalk.com, 27 events) — carry no third-level label.
- Casing / trailing-dot / foreign-suffix contamination — shape classification over all 115,145 events found none.
- Depth-1-only reading as a different answer — same 8.10.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p4 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
