# s1 - Q224 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=3_
**Scope:** sourcetype=stream:dns (all 8 sources) | source=lambda:DNS (aws:cloudwatchlogs) | fields: query, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
(none — round 1)

## This round
### What I ran
- get_source_types -> 102 sourcetypes; stream:dns and aws:cloudwatchlogs are the DNS-data carriers.
- get_sources sourcetype=stream:dns -> 8 sources, 217,566 events (stream:dns 175,094 dominant).
- get_sourcetype_fields stream:dns -> `query` field carries queried names.
- `index=botsv3 sourcetype=stream:dns query="*brewertalk.com" | stats count by query` -> 1 row: www.brewertalk.com, 107 events.
- `index=botsv3 sourcetype=stream:dns "brewertalk.com" | stats count by source, query` -> 3 rows / 107 events, all www.brewertalk.com (stream:dns 60, Splunk_DNSIntegrity 24, Splunk_DNSRequestResponse 23).
- get_sources aws:cloudwatchlogs -> single source lambda:DNS, 115,145 events.
- get_sourcetype_fields aws:cloudwatchlogs/lambda:DNS -> no extracted DNS fields (host=serverless, punct only); query names live in _raw.

### What it means
NOT_FOUND. The complete distinct set of queried names under brewertalk.com is not yet established. Within stream:dns (raw-text search across all 8 sources) the only queried name is www.brewertalk.com — alone that yields one third-level label "www" (length 3, average 3.00) — but the question's preamble names Route 53, and the dataset holds a 115,145-event Route 53 resolver query log (source=lambda:DNS, sourcetype=aws:cloudwatchlogs, host=serverless) whose query names sit unextracted in _raw. That feed is the likely holder of the full distinct subdomain set and was never searched for brewertalk.com, so 3.00 is not a submittable candidate. Next round: `index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "brewertalk.com" | rex field=_raw "\"query_name\":\"(?<qname>[^\"]+)\"" | stats count by qname`, then `| search qname="*.brewertalk.com" qname!="*.*.brewertalk.com" | dedup qname | eval sub=mvindex(split(qname,"."),0) | stats avg(len(sub)) as avg_len | eval avg_len=round(avg_len,2)`.

## Ruled out
- stream:dns as the complete source of brewertalk.com queries — raw-text search over the whole sourcetype returns only www.brewertalk.com (107 events); it cannot supply a multi-label distinct set, so the answer's set must come from the Route 53 feed (untested) or the two feeds agree on www only.
- No other sourcetype checked yet (aws:cloudtrail, osquery:results, Sysmon) — still open, not eliminated.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_field_values: {"field": "query", "source": "stream:dns", "sourcetype": "stream:dns", "top_n": 20}` (20 of 5063 rows seen). A claim resting on them alone is UNVERIFIED._
