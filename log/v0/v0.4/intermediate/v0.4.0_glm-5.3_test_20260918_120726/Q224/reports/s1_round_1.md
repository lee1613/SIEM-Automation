# s1 - Q224 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=9_
**Scope:** sourcetype=aws:cloudwatchlogs | source=lambda:DNS | fields=_raw (Route 53 resolver query log; query name = 4th whitespace token)
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 25

## Prior rounds
- Round 1 (this round): DNS feed resolved to lambda:DNS (aws:cloudwatchlogs); stream:dns ruled out (www only); FQDN level distribution mapped; final average not yet computed.

## This round
### What I ran
- get_sources(keyword="dns") -> two DNS feeds: stream:dns (175,094 evts) and lambda:DNS under sourcetype=aws:cloudwatchlogs (115,145 evts)
- `index=botsv3 sourcetype=stream:dns brewertalk.com | stats count by source, query` -> 107 evts, ALL query=www.brewertalk.com (stream:dns 60, stream:Splunk_DNSIntegrity 24, stream:Splunk_DNSRequestResponse 23)
- `index=botsv3 sourcetype=aws:cloudwatchlogs source=lambda:DNS brewertalk.com | stats count` -> 115,145 (100% of feed)
- sample_events -> raw: `1.0 2018-08-20T15:08:14Z Z149R7NEBZTKPN users1.brewertalk.com AAAA NXDOMAIN UDP ICN51 52.78.247.225 -`
- rex + `stats dc(fqdn) by label-count` -> apex 1; 1 label 100,083; 2 labels 13,656; 3 labels 621; 4 labels 42; 5 labels 4; 6 labels 21 = 114,428 distinct FQDNs

### What it means
NOT_FOUND for the final number solely because iterations expired. The usable feed is lambda:DNS (AWS Route 53 Resolver Query Logging): 115,145 brewertalk.com queries, 114,428 distinct FQDNs — a subdomain-enumeration wordlist (russianwomen, dunhill, scylla, autodiscover.backup, www.forumtest, testdomainx334-com...). stream:dns carries only www.brewertalk.com, so it cannot yield a distinct-subdomain average. Distinct third-level subdomains = labels immediately left of brewertalk.com (>=100,083, enlarged by deeper FQDNs). The avg(len) aggregation was never executed, so no value is submitted — inventing one was not an option.

## Ruled out
- stream:dns + sources stream:Splunk_DNSIntegrity / stream:Splunk_DNSRequestResponse - www.brewertalk.com only, zero subdomain variety
- apex brewertalk.com (27 evts) - no third-level label; must be excluded from the average

## Open questions for SH
- Grant one more round on lambda:DNS to run the finishing aggregation (exact SPL in notes) — it is a single query.
- Confirm interpretation: "third-level subdomain" = the label immediately preceding brewertalk.com (e.g., "forumtest" in www.forumtest.brewertalk.com).

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
