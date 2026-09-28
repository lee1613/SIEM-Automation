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

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['aws:cloudwatchlogs'] sources=['lambda:DNS'] fields=['_raw']
- Rounds worked: 3/8  (iterations: 17, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=bbotsv3 placeholder
- index=botserch placeholder
- index=botsv3 source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | rex field=fqdn "(?<third>[^.]+)\.brewertalk\.com$" | eval label_count=mvcount(split(fqdn,".")) | stats count as total_events, count(third) as with_third_label, dc(third) as distinct_third, dc(eval(lower(third))) as distinct_third_lower, count(eval(label_count>3)) as deeper_label_events
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | eval label_count=mvcount(split(fqdn,".")) | search label_count>3 | stats count by fqdn | head 12
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | eval partition=case(fqdn="brewertalk.com","apex_brewertalk_com", match(fqdn,"(?i)\.brewertalk\.com$"),"subdomain_brewertalk_com", true(),"other") | stats count by partition
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | rex field=fqdn "(?<third>[^.]+)\.brewertalk\.com$" | eval label_count=mvcount(split(fqdn,".")) | stats count as total_events, count(third) as with_third_label, dc(third) as distinct_third, dc(eval(lower(third))) as distinct_third_lower, count(eval(label_count>3)) as deeper_label_events
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | rex field=fqdn "(?<third>[^.]+)\.brewertalk\.com$" | search third=* | stats count by third | eval l=len(third) | stats count as distinct_labels, sum(l) as total_chars, avg(l) as avg_len, min(l) as min_len, max(l) as max_len, perc25(l) as p25, perc75(l) as p75 | eval avg_rounded=round(avg_len,2)
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | rex field=fqdn "(?<third>[^.]+)\.brewertalk\.com$" | search third=* | stats dc(third) as distinct_labels, avg(eval(len(third))) as avg_len | eval avg_len_rounded=round(avg_len,2)
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | rex field=fqdn "(?<third_rex>[^.]+)\.brewertalk\.com$" | eval third_mv=mvindex(split(fqdn,"."),-3) | stats count as total, count(eval(third_rex!=third_mv)) as mismatches, count(eval(isnull(third_rex) AND fqdn!="brewertalk.com")) as null_rex_non_apex
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | search fqdn="*.brewertalk.com" | eval third=mvindex(split(fqdn,"."),-3) | dedup third | stats count as distinct_labels, avg(eval(len(third))) as avg_len | eval avg_len_rounded=round(avg_len,2)
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | search fqdn="www.brewertalk.com" | stats count
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<fqdn>\S+)" | search NOT fqdn="*.brewertalk.com" | stats count by fqdn
- index=botsv3 sourcetype=stream:dns | where isnotnull(query) AND match(query,"(?i)brewertalk\.com\.?$") | stats count by query
