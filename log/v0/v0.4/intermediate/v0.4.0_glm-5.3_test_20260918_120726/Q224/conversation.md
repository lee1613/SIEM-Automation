# Q224 — SH <-> Senior conversation

### 12:07:50 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:dns', 'aws:cloudwatchlogs'] sources=['stream:dns', 'stream:Splunk_DNSRequestResponse', 'stream:Splunk_DNSIntegrity', 'stream:Splunk_DNSClientQueryTypes', 'stream:Splunk_DNSServerQuery', 'stream:Splunk_DNSServerResponse', 'lambda:DNS'] fields=['query', 'record', 'domain', 'dest', 'src', 'host', 'message']
**Technique:** hunter
**Reason:** This question is confined to DNS query telemetry, but the exact usable feed may sit in either network DNS stream data or AWS DNS log sources; one senior with DNS-scoped ownership can resolve the feed and compute the required distinct-subdomain average.

Identify which DNS feed in index=botsv3 contains queries to brewertalk.com, establish the distinct third-level subdomains present in those queries, and produce the average character length of those distinct third-level subdomains rounded to two decimal places.

### 12:13:11 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> FEED RESOLVED (part 1 of task): the usable DNS feed is source=lambda:DNS, sourcetype=aws:cloudwatchlogs (AWS Route 53 Resolver Query Logging via CloudWatch Logs). 115,145 events, every one a brewertalk.com query; 114,428 distinct FQDNs - a subdomain-enumeration wordlist (russianwomen, dunhill, scyll
_full: reports/s1_round_1.md_

### 12:13:16 - SH -> s1   [COMMAND]
**continue** — The case now has the correct DNS feed and the correct interpretation boundary for what counts as a third-level subdomain, but the scoreboard value itself is still missing. One finishing pass should establish the exact average from the already-identified Route 53 query log population.
**New scope:** sourcetypes=['aws:cloudwatchlogs'] sources=['lambda:DNS'] fields=['_raw']

Using source lambda:DNS under sourcetype aws:cloudwatchlogs, establish the exact set of distinct query names ending in brewertalk.com that contain a label immediately to the left of brewertalk.com, treat that immediate-left label as the third-level subdomain even when deeper labels exist, exclude the apex brewertalk.com, and produce the average character length of those distinct labels rounded to two decimal places. Also state explicitly whether repeated FQDNs or repeated labels collapse to one distinct third-level label for the final computation, and use the interpretation that matches the question wording.

### 12:14:47 - s1 -> SH   [REPORT - round 2 - FOUND]
> ANSWER: 8.10 (average character length of the distinct third-level subdomains in brewertalk.com DNS queries). FEED: source=lambda:DNS, sourcetype=aws:cloudwatchlogs (AWS Route 53 Resolver Query Logging via CloudWatch Logs) — 115,145 events, 100% brewertalk.com queries, 114,428 distinct FQDNs. DISTIN
_full: reports/s1_round_2.md_

### 12:14:51 - SH -> (new)   [ANSWER]
**8.10** (count) from s1

Senior s1 established that the relevant data is Route 53 query logging in sourcetype aws:cloudwatchlogs, source lambda:DNS; excluded apex brewertalk.com; extracted the immediate-left label before brewertalk.com as the third-level subdomain; deduplicated to distinct labels; and reported avg_raw=8.099379438805494, which rounds to 8.10.

### 12:14:51 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

