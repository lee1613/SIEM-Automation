# s2 - Q322 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=5_
**Scope:** sourcetype=stream:tcp; sourcetype=stream:http; sourcetype=WinEventLog (source=WinEventLog:Microsoft-Windows-PowerShell/Operational, WinEventLog:Security) | fields=uri_path, url, ssl_subject, ssl_issuer, app, dest_ip, dest_port, src_ip, EventCode
**Insight:** FOUND
**Candidate:** /images/logos.png   **Confidence:** 72

## Prior rounds
- R1 (s1): stream:http dest 45.77.53.176 → exactly 1 uri_path, /images/logos.png (3333 tool download); recurring 443 traffic had no HTTP-decoded path; stream:http src_ip=C2 and access_combined → 0. SH read p3 as not holding against the 443-channel rival.
- R2 (me): stream:dns (7/7 PTR reverse lookups) and PowerShell/Operational (0 events with the IP, 0 with URL tokens) eliminated as C2 path carriers; stream:tcp branch left unsearched.
- R3 (this round): 443 channel proven structurally unable to carry a path; stream:http re-verified — 1 path only; 4 WinEventLog:Security 4688 events found but unread.

## This round
### What I ran
- stream:tcp C2 IP by direction/port → 5 rows: 443 = 4,955 events (FYODOR-L 3,884 + 192.168.24.128 1,071), 3333 = 1, 8088/40552 = 4.
- get_sourcetype_fields stream:tcp → 46 of 92 rows read: flow metrics + ssl_* only, no payload/uri/url field.
- search_keyword payload → 0 matches in the entire manifest; search_keyword url → only stream:http carries a url field; search_keyword server_name → symantec only, no SNI in stream:tcp.
- 443 channel by ssl_subject/ssl_issuer → "" (4,817) and "C = US" (100); raw 443 events → app=ssl, refused=1, TLS_NULL_WITH_NULL_NULL, empty cert fields.
- stream:http dest_ip=45.77.53.176 → 1 event: uri_path=/images/logos.png, url=http://45.77.53.176:3333:3333/images/logos.png, src 192.168.70.186, port 3333.
- stream:http imgur → 0 events. WinEventLog "45.77.53.176" → 4 EventCode 4688 events in WinEventLog:Security (not read — tools withdrawn).

### What it means
FOUND. The recurring 443 C2 channel cannot record a literal URL or path in any accessible telemetry: no feed in the manifest has a payload field, stream:tcp exposes no SNI or uri field, and the channel is TLS against an empty or self-signed ("C = US") certificate — nothing readable beyond cipher lists. DNS and PowerShell were already empty. The only literal URL path on 45.77.53.176 in the data is /images/logos.png, from FYODOR-L's HTTP GET on port 3333 — re-verified this round with the full result read (1 event). Residual gap: 4 WinEventLog:Security 4688 process-creation command lines mentioning the C2 IP were located but not read before tools were withdrawn; they are the one surface that could corroborate or contradict, filed as a new coverage premise.

## Ruled out
- stream:tcp 443 channel as a path carrier — no payload field exists in any feed; no SNI; TLS with empty/self-signed cert subject.
- stream:dns — 7/7 events are PTR reverse lookups (45.77.53.176.vultr.com); no path.
- PowerShell/Operational script blocks — 0 events with the IP, 0 with any URL token.
- imgur URLs in stream:http — 0 events.
- stream:http src_ip=45.77.53.176, access_combined — s1, 0 events each.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p4 - amend or settle that one. The text you sent was discarded: "The only remaining surface in scope that could hold a literal C2 URL/path is 4 W"

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"min_count": 1, "sourcetype": "stream:tcp"}` (46 of 92 rows seen); `get_raw_events: {"keyword": "45.77.53.176", "limit": 10, "sourcetype": "stream:tcp"}` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
