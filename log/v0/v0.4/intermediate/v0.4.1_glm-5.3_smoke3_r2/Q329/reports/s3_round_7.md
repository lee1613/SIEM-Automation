# s3 - Q329 - Round 7
_stamped by runner: rounds_remaining=1 novel_spl=10_
**Scope:** sourcetypes=stream:http, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, o365:management:activity, access_combined (+ stream:smb/smtp, messagetrace, ess_content_importer, aws:s3:accesslogs, aws:cloudtrail, WinHostMon as content routes); fields=site, uri_path, http_method, form_data, src_ip, TargetFilename, Image, Operation, ObjectId, SourceFileName.
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 5

## Prior rounds
- R1: Sysmon located both files on MKRAEUS-L — PDF downloaded via Chrome (hash only), PPTX named in one unread registry event; no content reached.
- R2: Read the PPTX registry event (opened from SharePoint in PowerPoint, never saved locally); swept stream:http/smb/smtp and all 6 local FileCreate events — no bytes, no derivatives.
- R3: o365 cloud activity fully enumerated — PPTX has 2 metadata-only records (upload + ExportWorker access), PDF has none; all other cloud feeds empty.
- R4 (this round): stream:http carries no SharePoint traffic at all; MKRAEUS-L's HTTP is brewertalk.com browsing; forum POSTs are registration events, not uploads; access_combined has no PPTX.

## This round
### What I ran
- stream:http src_ip=107.77.212.175 / 104.209.132.239 -> 0 events each (both verified cloud IPs absent).
- stream:http "frothly-my.sharepoint.com" / "sharepoint" -> 0 events (feed has no SharePoint traffic at all).
- stream:http host=MKRAEUS-L | stats count by site, uri_path -> 71 rows (50 read): brewertalk.com browsing, OCSP, MS-store images, ipinfo.io — no document transfers.
- stream:http brewertalk.com POST -> 3 rows: member.php (22) and xmlhttp.php (38) from gacrux hosts; raw reads show registration form_data (action=register, step=agreement), src 174.215.8.112, Mac Chrome UA.
- stream:http newreply/editpost/newthread POST -> 0 events.
- access_combined "frothly_gabf_deck" -> 0 events.

### What it means
NOT_FOUND: the upload transfer is not in the network feed (no SharePoint traffic captured at all), the forum POSTs captured are registration steps rather than attachment uploads, and no feed carries either file's bytes. The oversized-font word is not recoverable from any source I could reach.

## Assumptions
- Coverage: content could appear via (a) stream:http SharePoint/upload traffic — searched by IP, host, filename, and full MKRAEUS-L destination list, absent; (b) forum upload POSTs — searched all POST endpoints, only registration form_data exists; (c) web-server access logs — searched for the filename, 0; (d) MyBB upload/attachment directory URIs in access logs — NOT SEARCHED (iterations exhausted) - UNVERIFIED; (e) xmlhttp.php POST form_data (38 events unread) - UNVERIFIED.
- Selection: the PPTX is the stronger candidate (only file with an upload record, matching the question's "uploaded" act) — VERIFIED as the upload act, but its content was never reached.
- Premise: the oversized word is recoverable from telemetry — UNVERIFIED after exhausting every content route in scope.

## Ruled out
- stream:http — no SharePoint traffic, no document transfers, no upload POSTs with file form_data.
- access_combined — no PPTX filename.
- o365:management:activity, messagetrace, ess_content_importer, aws:s3:accesslogs, aws:cloudtrail, stream:smb, stream:smtp, WinHostMon — all 0 for both filenames (R1-R3).
- Local copies on MKRAEUS-L — PDF is hash-only; PPTX never written to disk.

## Open questions for SH
- Should a future round list access_combined URIs under /uploads/ or /attachments/ on brewertalk.com (MyBB's upload directories), or read the 38 unread xmlhttp.php POSTs' form_data?
- Is there a known artifact holding either file's bytes (e.g., the forum thread page HTML on the web-server host)?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:http host=MKRAEUS-L | stats count by site, uri_path` (50 of 71 rows seen). A claim resting on them alone is UNVERIFIED._
