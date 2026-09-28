# s1 - Q224 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=2_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw, qname (rex-extracted)
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 97

## Prior rounds
- Round 1: Located the Route 53 query log feed (aws:cloudwatchlogs / lambda:DNS, 115,145 events, qname = 4th raw token); 114,428 distinct brewertalk qnames; averaging query not reached.
- Round 2: Verified coverage (all *brewertalk* records end in .brewertalk.com or are brewertalk.com itself; zero parse failures), computed avg = 8.10 with sum/count cross-check; extremes inspected. One Ruled out line (3-label reading "same label set") was inference and is retracted.
- Round 3: Re-ran population check and computation as fully read single-row results; both reproduce round 2 exactly.

## This round
### What I ran
- Population check: rex qname -> where ends .brewertalk.com and != brewertalk.com -> stats count, dc(qname) -> 1 row: 115,118 events, 114,427 distinct queried names.
- Computation: same base -> sub = label adjacent to brewertalk.com -> stats dc(qname) by sub -> len -> stats count, sum, avg -> 1 row: 100,393 distinct subs, 813,121 total chars, avg 8.099379, round(avg,2) = 8.10; check = sum/count = 8.099379.

### What it means
114,427 distinct queried names under .brewertalk.com (brewertalk.com itself excluded) yield 100,393 distinct third-level subdomain labels; their average character length is 8.099379, which rounds to 8.10. Both SPL formulations (avg() and sum/count) agree exactly, and both results this round are single-row, fully read — no partial listings contributed.

## Assumptions
- Coverage: every *brewertalk* record in lambda:DNS either is exactly brewertalk.com or ends in .brewertalk.com; no substring-only matches - VERIFIED (round 2 category eval, 2 of 2 rows read; re-confirmed this round by the population count matching the round-2 total).
- Definition: third-level subdomain = label immediately below brewertalk.com, from queried names at any depth, brewertalk.com itself excluded - VERIFIED as applied (per SH's ruling).
- qname = 4th whitespace token of _raw - VERIFIED (round 1 samples; zero rex failures across all events).

## Ruled out
- stream:dns as source (only www.brewertalk.com); aws:cloudwatch (no Route 53 source); the retracted round-2 claim that the 3-label-only reading produces the same label set (3-label qnames = 100,083 distinct vs 100,393 labels at any depth — the readings differ; the submitted value follows the any-depth definition).

## Open questions for SH
- None.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['stream:dns', 'aws:cloudwatchlogs'] sources=['stream:Splunk_DNSRequestResponse', 'stream:Splunk_DNSIntegrity', 'stream:Splunk_DNSServerQuery', 'stream:Splunk_DNSClientQueryTypes', 'stream:Splunk_DNSClientErrors', 'stream:Splunk_DNSServerResponse', 'stream:Splunk_DNSServerErrors', 'lambda:DNS'] fields=['query', 'record', 'rrname', 'domain', 'src', 'dest']
- Rounds worked: 3/8  (iterations: 29, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | eval category=case(isnull(qname),"rex_failed", match(qname,"(?i)^brewertalk\.com$"),"brewertalk_com_exact", match(qname,"(?i)\.brewertalk\.com$"),"ends_dot_brewertalk_com", true(),"other_contains_brewertalk") | eval flags=case(isnull(qname),"null", match(qname,"\.$"),"trailing_dot", match(qname,"[A-Z]"),"has_upper", true(),"clean") | stats count as events, dc(qname) as distinct_qnames by category, flags
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | eval labels=mvcount(split(qname,".")) | stats dc(qname) as distinct_qnames, count as events by labels
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | stats count as events, dc(qname) as distinct_qnames, values(qname) as qnames
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | stats dc(qname) as distinct_qnames, count as events
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | eval sub_len = len(sub) | stats count as distinct_subs, sum(sub_len) as total_chars, avg(sub_len) as avg_len | eval check = round(total_chars/distinct_subs, 6), avg_len = round(avg_len, 2)
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | eval sub_len = len(sub) | stats count as distinct_subs, avg(sub_len) as avg_len, min(sub_len) as min_len, max(sub_len) as max_len
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | eval sub_len = len(sub) | stats count as distinct_subs, sum(sub_len) as total_chars, avg(sub_len) as avg_len | eval avg_len = round(avg_len, 2), check = round(total_chars/distinct_subs, 6)
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | eval sub_len = len(sub) | stats count as distinct_subs, sum(sub_len) as total_chars, exact(avg(sub_len)) as avg_len | eval check = round(total_chars/distinct_subs, 6), avg_len = round(avg_len, 2)
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | eval sub_len = len(sub) | where sub_len<=2 OR sub_len>=40 | sort sub_len | fields sub, sub_len, distinct_qnames
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | eval sub_len = len(sub) | where sub_len>=40 | sort - sub_len | fields sub, sub_len, distinct_qnames
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | stats count as distinct_subs, avg(len(sub)) as avg_len | eval avg_len = round(avg_len, 2) | fields distinct_subs, avg_len
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | stats count as distinct_subs, avg(len(sub)) as avg_len | eval avg_len = tostring(round(avg_len, 2)) | fields distinct_subs, avg_len
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | stats count as distinct_subs, round(avg(len(sub)), 2) as avg_len, min(len(sub)) as min_len, max(len(sub)) as max_len
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | eval sub = mvindex(split(replace(qname, "\.brewertalk\.com$", ""), "."), -1) | stats dc(qname) as distinct_qnames by sub | stats dc(sub) as distinct_subs, sum(distinct_qnames) as distinct_qnames, avg(len(sub)) as avg_len, min(len(sub)) as min_len, max(len(sub)) as max_len | eval avg_len = round(avg_len, 2)
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS "*brewertalk*" | rex field=_raw "^\S+\s+\S+\s+\S+\s+(?<qname>\S+)" | where match(qname, "\.brewertalk\.com$") AND qname!="brewertalk.com" | stats count as events, dc(qname) as distinct_qnames
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS eventtype=err0r | stats count by _raw
- index=botsv3 sourcetype=stream:dns (queries="*brewertalk.com" OR name{}="*brewertalk.com" OR query{}="*brewertalk.com") | stats count by queries, name{}, query{}
- index=botsv3 sourcetype=stream:dns query="*brewertalk.com" | stats count by query | sort - count
