# s1 - Q224 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=6_
**Scope:** sourcetype=aws:cloudwatchlogs source=lambda:DNS | sourcetype=stream:dns | fields: _raw, qname, query
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 92

## Prior rounds
- R1: Mapped DNS feeds. stream:dns holds only www.brewertalk.com (107 events); found unsearched Route 53 log source=lambda:DNS (115,145 events, query names in _raw only). NOT_FOUND.
- R2: Opened lambda:DNS. Raw format = `version ts host-id QUERY-NAME qtype rcode proto edge ip edns`; whole feed is brewertalk.com; 114,428 distinct names; label counts 2:1, 3:100,083, 4:13,656, 5:621, 6:42, 7:4, 8:21. Both readings of "third-level" computed: A (third-from-right, ≥3 labels) 8.0994; B (exactly-3-label) 8.1037.

## This round
### What I ran
- `... | head 5 | rex "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | stats count by qname, _raw` -> qname literally = 4th token: ccmail.brewertalk.com, email5.brewertalk.com, koko10.brewertalk.com, users1.brewertalk.com, www.forumtest.brewertalk.com.
- Interpretation B full precision: `| where mvcount(parts)==3 | eval third=mvindex(parts,0) | stats count by third | eval l=len(third) | stats count as nB, avg(l) as avgB | eval avgB=round(avgB,4)` -> nB=100083, avgB=8.1037.
- Union check stream:dns vs Route 53: `stream:dns "brewertalk.com" | stats count by query | appendcols [search lambda:DNS ... | stats dc(qname) as r53_distinct]` -> stream_queries=www.brewertalk.com only, r53_distinct=114428 — stream adds nothing.
- Length distribution (both readings, 48 rows each, read in full): min 1, max 55, no zero-length labels; B sums to n=100,083, total 811,038 chars (811038/100083 = 8.1037, consistent).
- Anomaly check: `| eval anomalous=if(match(qname,"^\.") OR match(qname,"\.$") OR match(qname,"\.\."),"yes","no") | stats ... by anomalous` -> anomalous=no for all 115,145 events / 114,428 names. Case check: has_upper=no for all.

### What it means
FOUND. The queried names live in the Route 53 resolver query log (source=lambda:DNS), 4th token of each raw line, extraction shown literally. The complete distinct set under brewertalk.com is 114,428 names; the bare brewertalk.com (27 events) has no third level and is excluded. Reading A (third label from the right, per the question's own 4-label example my.example.company.com → example): 100,393 distinct labels, avg 8.0994 → 8.10. Reading B (exactly-3-label names only): 100,083 distinct labels, avg 8.1037 → 8.10. Both readings round to 8.10, so the answer is invariant to the interpretation choice. All arithmetic done in SPL (eval len, stats avg, round(x,2)); distributions read in full with no anomalies (no empty labels, no case or dot edge cases).

## Ruled out
- stream:dns as the source of the distinct set — holds only www.brewertalk.com, a strict subset of the Route 53 set (union check).
- Bare brewertalk.com as having a third-level subdomain — 2 labels only, excluded by the question's definition.
- Data-quality distortions — none: all lowercase, no leading/trailing/consecutive dots, no zero-length labels.

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The third-level subdomain of a query name under brewertalk.com is the third labe"
