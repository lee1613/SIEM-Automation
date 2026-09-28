# s1 - Q306 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=6_
**Scope:** sourcetype=stream:http, stream:dns, access_combined | fields: src_ip, dest_ip, site, uri_path, query, answer, clientip
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
- R1: Mail server identified as 172.31.38.181 (Postfix/Ubuntu, EC2 us-west-2, host matar) from stream:smtp dest_ip + greeting; no external IP found in CloudTrail/aws:description; no search query found.
- R2 (this round): matar's own HTTP is only a ClamAV update; DNS has no mail A/MX record; brewertalk.com access log searched — only internal clients so far; Splunk_HTTPURI source query returned 0 (anomalous).

## This round
### What I ran
- get_sourcetype_fields stream:http -> 24191 events; sources include stream:Splunk_HTTPURI (6029) and stream:Splunk_HTTPStatus (2729); dest 172.16.0.178 (brewertalk.com) and 169.254.169.254 prominent; field list truncated before uri_query.
- sourcetype=stream:http host=matar | stats count by src_ip,dest_ip,site,uri_path -> 1 row: 172.31.38.181 -> 104.16.185.138 db.local.clamav.net /daily-24783.cdiff (ClamAV update only).
- stream:dns record_type=MX -> 0; query="*froth.ly*" -> 15 rows: splunk=34.215.24.225, store=34.197.89.81/54.88.106.216, vpn=24.8.40.184, autodiscover=O365 IPs. No mail record.
- source=stream:Splunk_HTTPURI | stats count by host,src_ip -> 0 rows (contradicts field summary's 6029 events — source-value or field quirk, unresolved).
- get_raw_events access_combined keyword=search -> 10 rows, all client 172.16.0.149 on brewertalk.com /search.php, incl. automated "GET /search.php" with user-agent "__main__/0.2".

### What it means
NOT_FOUND: neither half of the chain is closed. The mail server's external IP is not in DNS, CloudTrail, aws:description, or matar's own HTTP capture; the only search traffic found so far comes from internal 172.16.0.149, not the mail server. Two strong leads remain: the Splunk_HTTPURI source (HTTP to the Splunk server, where a search query from a public IP would be recorded) and public client IPs in the brewertalk.com access log.

## Ruled out
- matar's own stream:http capture - only a ClamAV update; no search from the mail server's own telemetry.
- stream:dns froth.ly records - no MX and no mail-server A record; the A records found belong to splunk/store/vpn/autodiscover.
- brewertalk.com /search.php requests from 172.16.0.149 - internal corporate IP (172.16.0.0/23), not the mail server's external address.
- aws:cloudtrail / aws:description - no events naming 172.31.38.181 or its hostname; no EC2 instance inventory (from R1).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- update ignored: p1 is not a premise on this question

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:http"}` (28 of 57 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPURI | stats count by uri_path` (50 of 1996 rows seen). A claim resting on them alone is UNVERIFIED._
