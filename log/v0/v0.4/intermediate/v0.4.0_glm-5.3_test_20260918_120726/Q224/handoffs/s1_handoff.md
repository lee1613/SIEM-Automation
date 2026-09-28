# s1 - Q224 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=4_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw (Route 53 resolver query log; query name = 4th whitespace token)
**Insight:** FOUND
**Candidate:** 8.10   **Confidence:** 95

## Prior rounds
- Round 1: DNS feed resolved to lambda:DNS (aws:cloudwatchlogs, 115,145 brewertalk.com queries, 114,428 distinct FQDNs); stream:dns ruled out (www only, 107 events); FQDN level distribution mapped; avg not yet computed.
- Round 2 (this round): finishing aggregation executed; average established and verified.

## This round
### What I ran
- `index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS | rex field=_raw "\s(?<fqdn>\S*brewertalk\.com)\s" | where isnotnull(fqdn) AND fqdn!="brewertalk.com" | eval label=mvindex(split(fqdn,"."),-3) | where isnotnull(label) | stats count by label | eval len=len(label) | stats count as distinct_labels, avg(len) as avg_len, min(len) as min_len, max(len) as max_len | eval avg_len=round(avg_len,2)` -> distinct_labels=100393, avg_len=8.10, min_len=1, max_len=55
- Integrity check `| stats count, count(eval(isnull(fqdn))) as rex_failed, dc(fqdn), count(eval(fqdn=="brewertalk.com"))` -> 115145 events, rex_failed=0, 114428 distinct FQDNs, 27 apex events
- Precision check `| stats count as distinct_labels, sum(len) as total_chars | eval avg_raw=total_chars/distinct_labels, avg_2dp=round(avg_raw,2)` -> 100393 labels, 813121 chars, avg_raw=8.099379438805494, avg_2dp=8.10

### What it means
FOUND: the chain is complete. Every one of the 115,145 lambda:DNS events yielded a query name (rex_failed=0); the apex brewertalk.com (27 events) was excluded; the immediate-left label was taken as the third-level subdomain even for deeper FQDNs (www.forumtest.brewertalk.com -> forumtest); labels were deduplicated via `stats count by label`, so repeated FQDNs and repeated labels both collapse to one distinct third-level label. 100,393 distinct labels sum to 813,121 characters; 813121/100393 = 8.099379..., which rounds unambiguously to 8.10 at two decimal places. min_len=1 confirms no empty labels polluted the set.

## Ruled out
- stream:dns (incl. stream:Splunk_DNSIntegrity, stream:Splunk_DNSRequestResponse) - www.brewertalk.com only, no subdomain variety (round 1)
- apex brewertalk.com - no third-level label, excluded from the average

## Open questions for SH
- None blocking; value 8.10 is ready for the scoreboard. If SH intended "distinct FQDNs" rather than "distinct labels" as the averaging population, that variant was not computed — but the question wording ("distinct third-level subdomains") matches the distinct-label computation performed.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['stream:dns', 'aws:cloudwatchlogs'] sources=['stream:dns', 'stream:Splunk_DNSRequestResponse', 'stream:Splunk_DNSIntegrity', 'stream:Splunk_DNSClientQueryTypes', 'stream:Splunk_DNSServerQuery', 'stream:Splunk_DNSServerResponse', 'lambda:DNS'] fields=['query', 'record', 'domain', 'dest', 'src', 'host', 'message']
- Rounds worked: 2/8  (iterations: 13, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=lambda:DNS brewertalk.com | stats count
- index=botsv3 sourcetype=aws:cloudwatchlogs source="lambda:DNS" | stats count
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS brewertalk.com | stats count
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS | rex field=_raw "\s(?<fqdn>\S*brewertalk\.com)\s" | eval sub=replace(fqdn, "\.?brewertalk\.com$", "") | eval levels=if(sub=="", 0, mvcount(split(sub, "."))) | stats dc(fqdn) as distinct_fqdns by levels
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS | rex field=_raw "\s(?<fqdn>\S*brewertalk\.com)\s" | stats count by fqdn | sort - count
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS | rex field=_raw "\s(?<fqdn>\S*brewertalk\.com)\s" | stats count, count(eval(isnull(fqdn))) as rex_failed, dc(fqdn) as distinct_fqdn, count(eval(fqdn=="brewertalk.com")) as apex_events
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS | rex field=_raw "\s(?<fqdn>\S*brewertalk\.com)\s" | where isnotnull(fqdn) AND fqdn!="brewertalk.com" | eval label=mvindex(split(fqdn,"."),-3) | stats count by label | eval len=len(label) | stats count as distinct_labels, sum(len) as total_chars | eval avg_raw=total_chars/distinct_labels, avg_2dp=round(avg_raw,2), avg_4dp=round(avg_raw,4)
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS | rex field=_raw "\s(?<fqdn>\S*brewertalk\.com)\s" | where isnotnull(fqdn) AND fqdn!="brewertalk.com" | eval label=mvindex(split(fqdn,"."),-3) | stats count by label | eval len=len(label) | stats count as distinct_labels, sum(len) as total_chars, exact(avg(len)) as avg_raw | eval avg_2dp=round(avg_raw,2), avg_4dp=round(avg_raw,4)
- index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS | rex field=_raw "\s(?<fqdn>\S*brewertalk\.com)\s" | where isnotnull(fqdn) AND fqdn!="brewertalk.com" | eval label=mvindex(split(fqdn,"."),-3) | where isnotnull(label) | stats count by label | eval len=len(label) | stats count as distinct_labels, avg(len) as avg_len, min(len) as min_len, max(len) as max_len | eval avg_len=round(avg_len,2)
- index=botsv3 sourcetype=aws:cloudwatchlogs | stats count by source
- index=botsv3 sourcetype=stream:dns brewertalk.com | stats count by query, name
- index=botsv3 sourcetype=stream:dns brewertalk.com | stats count by source
- index=botsv3 sourcetype=stream:dns brewertalk.com | stats count by source, query
