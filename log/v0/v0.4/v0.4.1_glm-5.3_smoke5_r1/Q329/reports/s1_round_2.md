# s1 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=8_
**Scope:** sourcetypes=aws:s3:accesslogs, aws:cloudtrail, stream:smtp, symantec:ep:*:file, osquery:results, WinEventLog, XmlWinEventLog:Sysmon; sources=/var/log/httpd/access_log, /var/log/apache2/access.log; fields=key, requester, uri, method, attach_filename{}, sender, clientip
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
- Round 1: "taedonggang" absent from O365 UserId (12 ids), access_combined, stream:http, code42; all 8 O365 upload events by internal froth.ly users.
- Round 2 (this round): 3 anonymous S3 uploads to open bucket frothlywebcode; brewertalk.com MyBB forum found behind /var/log/httpd/access_log with an account registration from 172.16.0.149; SuiteCRM behind apache2 log; SMTP attachments enumerated.

## This round
### What I ran
- get_sourcetype_fields aws:s3:accesslogs -> key/requester/operation confirmed.
- REST.PUT.OBJECT by key/requester -> 337 events; requester="-" subset = 3 uploads (see below).
- stream:smtp attach_filename by sender -> 10 rows, only external sender hyunki1984@naver.com (1534778082419.png).
- stream:http POST -> 0 events; access_combined uri_path="*upload*" -> 0 events.
- get_sources access_combined -> httpd/access_log (brewertalk.com MyBB) + apache2/access.log (SuiteCRM).
- httpd POSTs -> member.php x22 + xmlhttp.php?action=username_availability x38 from 172.16.0.149; raw events show account registration at 2018-08-20T13:47:04Z and profile views uid=35/uid=31.

### What it means
NOT_FOUND: no upload event attributable to Taedonggang, no document contents, no oversized word. The three anonymous S3 uploads (smart-quote-disguised frothly_html_memcached.tar.gz from 54.241.141.120; OPEN_BUCKET_PLEASE_FIX.txt from 52.66.146.128; frothly_html_memcached.tar.gz from 35.182.246.222) are unattributed and none is yet shown to be a formatted document. The strongest new lead is the brewertalk.com forum account registered from 172.16.0.149 — MyBB forums accept avatar/attachment uploads, which is the most plausible "file uploaded by Taedonggang" path, but the username is not visible in access logs.

## Assumptions
- Coverage: uploads as (a) S3 anonymous PUTs — searched, 3 found, unattributed; (b) SMTP attachments — 10 enumerated, none tied to Taedonggang; (c) web POSTs — stream:http 0 POSTs, no *upload* URI in access_combined, MyBB member.php POST is registration not file upload, SuiteCRM 1 POST (302 login); (d) MyBB avatar/attachment endpoints (usercp.php?action=avatar, newthread/newreply) — NOT YET SEARCHED; (e) endpoint file writes (Sysmon/osquery/WinEventLog/Symantec) — NOT YET SEARCHED. - VERIFIED a-c, UNVERIFIED d-e
- Selection: no candidate selected; nothing found passes the "uploaded by Taedonggang" test. - VERIFIED
- Premise: Taedonggang is the brewertalk.com account registered from 172.16.0.149 at 13:47:04Z. - UNVERIFIED: POST body not logged; only circumstantial (38 username_availability checks then registration).
- Premise: the target file is a formatted document (font sizes imply HTML/docx/pdf), so tar.gz archives of web code are unlikely to be it. - UNVERIFIED: contents not yet read.

## Ruled out
- stream:http as upload path — 0 POST events in the feed.
- access_combined *upload* URIs — 0 events.
- O365 uploads (round 1) — all internal users.
- SuiteCRM POST — single 302 login redirect, no upload.

## Open questions for SH
- Is Taedonggang known to be the brewertalk.com forum account registered from 172.16.0.149 on 2018-08-20? If yes, next round targets MyBB upload endpoints (usercp.php?action=avatar, /uploads/ paths) in /var/log/httpd/access_log.
- If the forum path fails, should I pivot to endpoint telemetry (Sysmon/osquery) for the file's contents, or to the smart-quote-disguised S3 tar.gz from 54.241.141.120?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "aws:s3:accesslogs"}` (38 of 76 rows seen); `run_splunk_search: index=botsv3 sourcetype=aws:s3:accesslogs operation="REST.PUT.OBJECT" | stats count by key…` (25 of 337 rows seen). A claim resting on them alone is UNVERIFIED._
