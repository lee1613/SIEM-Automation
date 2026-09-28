# s1 - Q306 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=7_
**Scope:** sourcetype=access_combined, stream:http (sources stream:Splunk_HTTPClient / Splunk_HTTPURI) | fields: clientip, c_ip, uri_path, request, src_ip, dest_ip, site, _raw
**Insight:** partial — no value
**Candidate:** none   **Confidence:** 20

## Prior rounds
- R1: Mail server = 172.31.38.181 (Postfix/Ubuntu, EC2 us-west-2, host matar) from stream:smtp dest_ip + greeting; no external IP in CloudTrail/aws:description.
- R2: matar's own stream:http = one ClamAV update only; DNS has no mail A/MX; brewertalk /search.php traffic all from internal 172.16.0.149; Splunk_HTTPURI grouped query returned 0 (source quirk unresolved).
- R3 (this round): access_combined exhausted — no external-IP search; mail server's single outbound HTTP request found in Splunk_HTTPClient at 14:14:26Z (151B in / 14363B out / 12.96s) but its URI string was not retrieved; c_ip list truncated at 50 of 60 rows.

## This round
### What I ran
- access_combined | stats count by clientip -> 22 IPs, all read: 6 internal (172.16.0.149=2818, 172.16.1.239=833, 192.168.8.x) + 16 external, 1 event each.
- External clients rex'd from _raw -> 16 rows, all read: 13 bare "GET /" scans + 3 IoT exploits (luci/nslookup-wget, login.cgi Hakai/2.0, GponForm). No search strings, no AWS-range IP, no mail-server link.
- stream:http | stats count by source -> 5 sources: stream:http=10398, Splunk_HTTPClient=2474, Splunk_HTTPResponseTime=2561, Splunk_HTTPStatus=2729, Splunk_HTTPURI=6029.
- Splunk_HTTPClient | stats count by c_ip -> 60 rows, 50 returned (10 UNSEEN, sorted after "36.80.156.172"); c_ip=172.31.38.181 appears exactly once.
- get_raw_events Splunk_HTTPClient keyword=172.31.38.181 -> 1 event: endtime 2018-08-20T14:14:26.186801Z, bytes_in=151, bytes_out=14363, time_taken=12960.
- Splunk_HTTPURI samples -> structure {endtime, dest_ip, site, status, uri_path, bytes, time_taken}, paired with HTTPClient by timestamp/bytes.
- Splunk_HTTPURI "14:14:26" -> 0 events.

### What it means
The mail server made exactly one captured outbound HTTP request — 151 bytes out, a 14,363-byte response over 12.96 seconds, the shape of a search returning results. That request is the leading candidate for the question's "search query originating from an external IP", but the literal string lives in the paired Splunk_HTTPURI event, which my timestamp keyword missed (paired events can differ by a fraction of a second, e.g. .059828 vs .060076). Separately, the c_ip enumeration was truncated before 10 values that plausibly include the mail server's EC2 public IP. No value is submitted: the string was never read.

## Ruled out
- access_combined (brewertalk.com) entirely - all 22 client IPs read in full; the 16 external IPs are one-event scanners/exploit probes with no query strings and no AWS/mail-server linkage.
- brewertalk /search.php from 172.16.0.149 - internal RFC1918 address, excluded by the question's "external IP" wording (per SH).
- matar's own stream:http capture - ClamAV update only (R2).
- stream:dns froth.ly records - no MX, no mail A record (R2).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPClient | stats count by c_ip` (50 of 60 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: end of question (turns)
- Scope I owned: sourcetypes=['stream:http', 'stream:dns', 'stream:ip', 'stream:tcp', 'ms:o365:reporting:messagetrace', 'stream:smtp'] sources=[] fields=['src_ip', 'dest_ip', 'site', 'uri_path', 'url', 'query', 'host', 'http_user_agent', 'src', 'dest']
- Rounds worked: 3/3  (iterations: 33, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=access_combined NOT clientip=172.16.0.0/16 NOT clientip=192.168.0.0/16 | rex field=_raw "\"(?<method>\S+) (?<request>[^ ]+) HTTP" | stats count by clientip, method, request
- index=botsv3 sourcetype=access_combined NOT clientip=172.16.0.0/16 NOT clientip=192.168.0.0/16 | stats count by clientip, uri_path, uri_query, useragent
- index=botsv3 sourcetype=access_combined | stats count by clientip
- index=botsv3 sourcetype=aws:cloudtrail "172.31.38.181" | stats count by eventName, eventSource
- index=botsv3 sourcetype=aws:cloudtrail "ip-172-31-38-181" | stats count by eventName, eventSource
- index=botsv3 sourcetype=aws:description eventtype=aws_description_ec2_instances | stats count by host, ip_address, private_ip_address, instance_id
- index=botsv3 sourcetype=aws:description region=us-west-2 | stats count by source
- index=botsv3 sourcetype=stream:dns query="*froth.ly*" | stats count by query, answer
- index=botsv3 sourcetype=stream:dns record_type=MX | stats count by query, answer
- index=botsv3 sourcetype=stream:dns | stats count by record_type
- index=botsv3 sourcetype=stream:http host=matar | stats count by src_ip, dest_ip, site, uri_path
- index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPClient | stats count by c_ip
- index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPURI "14:14:26" | stats count by endtime, dest_ip, site, uri_path, status
- index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPURI endtime="2018-08-20T14:14:26*" | stats count by endtime, dest_ip, site, uri_path, status
- index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPURI | stats count by host, src_ip
- index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPURI | stats count by uri_path
- index=botsv3 sourcetype=stream:http | stats count by source
