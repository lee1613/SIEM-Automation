# Q224 — SH <-> Senior conversation

### 12:01:11 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:dns', 'aws:cloudwatchlogs'] sources=['stream:Splunk_DNSRequestResponse', 'stream:Splunk_DNSClientQueryTypes', 'stream:Splunk_DNSServerQuery', 'lambda:DNS'] fields=['query', 'query_type', 'record_type', 'src', 'dest', 'host', 'domain', 'message_type']
**Technique:** metrics
**Reason:** This question is a constrained DNS calculation problem: we need the right DNS query feed, correct extraction of third-level subdomains under brewertalk.com, and a precise average over distinct values.

Determine which indexed DNS feed contains queries to brewertalk.com associated with Frothly's Amazon Route 53 web service, extract the distinct third-level subdomains from those queried FQDNs, and compute the average length of those distinct third-level subdomain strings rounded to two decimal places.

