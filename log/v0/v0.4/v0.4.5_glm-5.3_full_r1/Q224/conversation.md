# Q224 — SH <-> Senior conversation

### 18:06:35 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['stream:dns'] sources=['stream:dns', 'stream:Splunk_DNSRequestResponse', 'stream:Splunk_DNSIntegrity', 'stream:Splunk_DNSServerQuery', 'stream:Splunk_DNSClientQueryTypes'] fields=['query', 'host', 'src_ip', 'dest_ip', 'record_type', 'answer']
**Technique:** metrics
**Reason:** The question measures DNS query names, and the dataset’s DNS stream feeds carry those queried domains directly. This is a numeric result that must be computed from the distinct third-level labels actually seen in brewertalk.com queries.

Using DNS query data, determine the average length of the distinct third-level subdomains in queries to brewertalk.com. Identify the complete distinct set of queried names under brewertalk.com, extract the third-level label from each applicable query, decide which queries actually have a third-level subdomain, and compute the average label length rounded to two decimal places.

### 18:08:45 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> Round 1 established the DNS feed landscape but did NOT reach the answer. Facts: (1) stream:dns has 8 sources; a raw-text search for "brewertalk.com" across the whole sourcetype returns exactly one query name, www.brewertalk.com, 107 events (stream:dns 60, stream:Splunk_DNSIntegrity 24, stream:Splunk
_full: reports/s1_round_1.md_

### 18:08:51 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] Do not use 3.00 yet. It comes only from stream:dns, and your own report leaves lambda:DNS unsearched even though it is the likely fuller DNS-query source named by the Route 53 preamble.
[q2] Settle coverage in the DNS feeds first: establish whether lambda:DNS contains brewertalk.com query names and whether it expands the distinct third-level set beyond www.

**continue** — This round established the stream:dns floor and identified the likely missing coverage path in lambda:DNS. The answer depends on the complete distinct set of brewertalk.com query names, so the next work must parse and measure that Route 53-style feed.
**New scope:** sourcetypes=['aws:cloudwatchlogs', 'stream:dns'] sources=['lambda:DNS'] fields=['_raw', 'query', 'query_name', 'qname']

Search aws:cloudwatchlogs source=lambda:DNS for brewertalk.com query names, extract the queried domain field from _raw, and establish the complete distinct set of names under brewertalk.com there. Then decide which queried names actually have a third-level subdomain, compute the average length over the distinct qualifying labels, and restate the rounded value if unchanged or new.

### 18:15:13 - s1 -> SH   [REPORT - round 2 - NOT_FOUND]
> 
_full: reports/s1_round_2.md_

### 18:15:19 - SH -> s1   [COMMAND]
**retry** — The right feed has been found, but the approach is not yet trustworthy because it produced two rival readings and at least one result was only partially returned. The case now needs the raw shape of lambda:DNS brewertalk.com records established before any average is accepted.
**New scope:** sourcetypes=['aws:cloudwatchlogs', 'stream:dns'] sources=['lambda:DNS'] fields=['_raw', 'query', 'qname']

First establish what field in lambda:DNS actually holds the queried name for brewertalk.com by reading representative raw events and showing the extracted qname literally. Then decide which names count for this question: whether it wants the label immediately left of brewertalk.com on every qualifying query, and whether deeper names under brewertalk.com are included or only exact three-label names. After that, compute the average length over the distinct qualifying labels and restate the rounded value.

### 18:18:04 - s1 -> SH   [REPORT - round 3 - FOUND]
> The Route 53 resolver query log (source=lambda:DNS, sourcetype=aws:cloudwatchlogs) is the answer's feed: its entire 115,145 events are brewertalk.com queries (114,428 distinct names), and it is the DNS query source the question's preamble names. Raw format: "version timestamp host-id query-name qtyp
_full: reports/s1_round_3.md_

### 18:18:13 - SH -> s1   [ANSWER]
**8.10** (count) from s1

s1 established from aws:cloudwatchlogs source=lambda:DNS that queried names are the fourth token of each raw Route 53-style DNS log line and that this feed contains the complete distinct brewertalk.com name set, while stream:dns contributes only www.brewertalk.com. It then computed the average distinct third-level-label length two ways—third-from-right on all qualifying names and exact three-label names only—and both rounded to 8.10, making the submitted value stable against the remaining wording ambiguity.

**Premises it rests on:** p1, p2

### 18:18:13 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

