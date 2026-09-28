# Q224 — SH <-> Senior conversation

### 14:37:31 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:dns', 'aws:cloudwatchlogs'] sources=['lambda:DNS', 'stream:dns', 'stream:Splunk_DNSRequestResponse', 'stream:Splunk_DNSIntegrity', 'stream:Splunk_DNSServerQuery', 'stream:Splunk_DNSServerResponse', 'stream:Splunk_DNSClientQueryTypes', 'stream:Splunk_DNSClientErrors', 'stream:Splunk_DNSServerErrors'] fields=['query', 'record', 'rrname', 'domain', 'src', 'dest', 'host']
**Technique:** metrics
**Reason:** This question is a numeric DNS computation, so it needs a metrics senior constrained to DNS evidence that can observe queried FQDNs and calculate the average from distinct third-level subdomains.

Using DNS telemetry in index=botsv3, identify all queries to brewertalk.com, extract the distinct third-level subdomains from those queried names, compute each subdomain's character length, and return the average length of those distinct third-level subdomains rounded to two decimal places.

### 14:38:21 - s1 -> SH   [REPORT - round 1 - FOUND]
> Distinct third-level subdomains queried under brewertalk.com resolve to a single label, www. The reported average length is therefore len(www)=3, rounded to two decimals -> 3.00. The stats output includes distinct_count=2 because the query also encountered the apex domain brewertalk.com in the filte
_full: reports/s1_round_1.md_

### 14:38:24 - SH -> s1   [ANSWER]
**3.00** (count) from s1

Senior s1 established that stream:dns is the correct query source, verified that the only distinct third-level subdomain observed under brewertalk.com is `www`, computed its length as 3, and reported the average over distinct subdomains as `3.00`.

### 14:38:24 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

