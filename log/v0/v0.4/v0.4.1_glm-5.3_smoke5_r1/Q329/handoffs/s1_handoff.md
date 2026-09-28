# s1 - Q329 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=9_
**Scope:** sourcetypes=stream:smtp, stream:http, access_combined; fields=_raw, sender, subject, attach_filename{}, mime_type, uri_path, uri_query, form_data, src_ip, http_content_type
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 5

## Prior rounds
- R1: "taedonggang" absent from O365 UserId (12 ids), access_combined, stream:http, code42; all 8 O365 uploads by internal users.
- R2: 3 anonymous S3 uploads to open bucket frothlywebcode (unattributed); brewertalk.com MyBB forum found; account registered from 172.16.0.149 at 13:47:04Z.
- R3: MyBB endpoints mapped — attachment.php serves only ?thumbnail=1..9; no avatar/upload/document path; no username in any URI.
- R4-5: stream:mysql — attacker IP X'ac100095'; finduserthreads&uid=36; no mybb_users/posts/attachments INSERTs; no "taedonggang" string.
- R6: osquery FIM covers only /tmp,/etc,/home on hoth; Symantec feeds carry process names; WinEventLog 4663 shows employee documents.
- R7: Sysmon file-creates are employee downloads + Outlook-cached pwned.jpg; stream:http has no POST bodies (form_data empty at that query), no multipart, no brewertalk POSTs.
- R8 (this round): stream:http form_data DOES exist for brewertalk — 48 POSTs with usernames/passwords (fyodor, Bootyman, Trojaan, bgist, bootyman); attacker's external IP is 174.215.8.112; its do_register POST was never captured; hyunki1984 email is "All your datas belong to us" with a PNG.

## This round
### What I ran
- stream:smtp hyunki1984 raw events -> 2 events, too large to return; structured fields -> subject "All your datas belong to us", recipient ghoppy@froth.ly, attachment 1534778082419.png, multipart/alternative.
- stream:http attachment.php raw events -> revealed attacker external IP 174.215.8.112 (cookie sid=d1a86150f9776974999d54fe4c7eb90a), form_data thumbnail=N, content types image/png and image/jpeg.
- src_ip=174.215.8.112 all requests -> 24 rows: registration agreement, browsing, thumbnail views — NO upload POST.
- All brewertalk POSTs by src_ip -> 48 rows with full form_data: registrations by fyodor,
_[trimmed by the runner to fit the word cap]_

### What it means
NOT_FOUND. The three missing concepts, exactly: ACTOR IDENTITY unsatisfied (username "Taedonggang" never observed anywhere; the attacker's do_register POST was not captured), FILE IDENTITY unsatisfied (no upload event attributable to the actor — its 24 captured requests contain no upload), FILE CONTENTS unsatisfied (no document with an oversized word recovered). Closest artifact: the MyBB attachment thumbnails (aids 1-9) the attacker viewed, and the hyunki1984@naver.com email with 1534778082419.png — neither yielded a filename or styled text.

## Assumptions
- Coverage: content-bearing paths as (a) stream:smtp raw bodies — the hyunki1984 events exist but exceed the tool's return size, so only structured fields were read; (b) stream:http form_data — searched, 48 POSTs read in full, no taedonggang, no upload POST from the attacker; (c) MyBB attachment content — only thumbnail requests captured, no aid= full-file requests; (d) rendered brewertalk HTML — no feed carries response bodies. - VERIFIED b, PARTIALLY VERIFIED a, UNVERIFIED c-d
- Selection: no candidate; nothing ties any file to Taedonggang. - VERIFIED
- Premise: Taedonggang is the brewertalk.com registrant from 174.215.8.112/172.16.0.149. - UNVERIFIED after 8 rounds: the do_register POST carrying the username was never captured.

## Ruled out
- stream:http form_data as the actor-identity source — 48 POSTs read in full; the attacker's do_register POST is absent; no "taedonggang" string.
- The attacker's captured session as an upload source — 24 requests, all browsing/thumbnails, no upload POST.
- hyunki1984@naver.com email as the answer's file — an email attachment (not an upload), a PNG (not a font-styled document), and its raw body could not be read (too large).
- All prior eliminations (R1-R7): O365 uploads, MyBB web-log attribution, mybb_users/posts/attachments INSERTs, osquery FIM, Symantec feeds, WinEventLog 4663, Sysmon file-creates, S3 anonymous uploads (unattributed).

## Open questions for SH
- None remaining within this toolset: the answer requires either the MyBB attachment file contents (aids 1-9) or the attacker's registration record, neither of which was captured in any feed I could query.

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_raw_events: {"keyword": "hyunki1984", "limit": 10, "sourcetype": "stream:smtp"}` (0 of 2 rows seen); `get_raw_events: {"keyword": "1534778082419", "limit": 5, "sourcetype": "stream:smtp"}` (0 of 2 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:http site="www.brewertalk.com" | stats count by uri_path, s…` (50 of 108 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: Rounds exhausted without identifying a file uploaded by Taedonggang or recovering any candidate content. The freshest report is cut off at the iteration cap and leaves the load-bearing concepts unsatisfied, so this senior cannot be used to answer and should hand off the concrete leads: brewertalk/MyBB attachment thumbnails aid=1-9, attacker IP 174.215.8.112, and the hyunki1984@naver.com PNG email path as the closest unrecovered content sources.
- Scope I owned: sourcetypes=['code42:security', 'code42:file', 'code42:api', 'code42:user', 'code42:computer', 'osquery:results', 'bash_history', 'stream:http', 'access_combined', 'aws:s3:accesslogs'] sources=[] fields=['user', 'filename', 'file', 'filepath', 'path', 'md5', 'sha1', 'sha256', 'device_name', 'computer_name', 'url', 'uri_path', 'uri', 'http_method', 'form_data', 'object', 'key', 'bucket', '_raw']
- Rounds worked: 8/8  (iterations: 91, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "taedonggang" | stats count by sourcetype
- index=botsv3 source="/var/log/apache2/access.log" method=POST | stats count by uri, status, clientip
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 CommandLine="*brewertalk*" OR CommandLine="*curl*" OR CommandLine="*wget*" | stats count by CommandLine, host
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11 TargetFilename="*.png" OR TargetFilename="*.jpg" OR TargetFilename="*.gif" OR TargetFilename="*.pdf" OR TargetFilename="*.docx" OR TargetFilename="*.html" | stats count by TargetFilename, host
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11 TargetFilename="*\\Downloads\\*" OR TargetFilename="*\\Desktop\\*" OR TargetFilename="*\\Documents\\*" | stats count by TargetFilename, host
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11 | stats count by TargetFilename, host
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" TargetFilename="*brewertalk*" OR TargetFilename="*upload*" OR TargetFilename="*attach*" OR TargetFilename="*mybb*" | stats count by TargetFilename, host, EventCode
- index=botsv3 sourcetype=access_combined "taedonggang" | stats count by uri_path, method, status
- index=botsv3 sourcetype=access_combined source="/var/log/apache2/access.log" method=POST | stats count by uri, status, clientip
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" method=POST | stats count by uri, status, clientip
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri="*.pdf" OR uri="*.docx" OR uri="*.txt" OR uri="*.doc" OR uri="*.html" | stats count by uri, method, status, clientip
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri="*uploads*" OR uri="*avatar*" | stats count by uri, method, status, clientip
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri="*username*" OR uri="*user=*" OR uri="*name=*" | stats count by uri, method, status
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="*.php" | stats count by uri_path | sort -count
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="/attachment.php" | stats count by uri, clientip, status
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="/member.php" | stats count by uri, status
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="/search.php" | stats count by uri, method, status
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="/showthread.php" | stats count by uri, status
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" uri_path="/xmlhttp.php" | stats count by uri, method, status
- index=botsv3 sourcetype=access_combined source="/var/log/httpd/access_log" | stats count by uri_path | sort -count
- index=botsv3 sourcetype=access_combined source="/var/log/httped/access_log" uri="*uploads*" OR uri="*avatar*"
- index=botsv3 sourcetype=access_combined uri_path="*upload*" | stats count by uri_path, method, status, clientip
- index=botsv3 sourcetype=aws:s3:accesslogs operation="REST.PUT.OBJECT" requester="-" | stats count by key, remote_ip, bucket_name, object_size
- index=botsv3 sourcetype=aws:s3:accesslogs operation="REST.PUT.OBJECT" | stats count by key, requester, remote_ip, bucket_name
- index=botsv3 sourcetype=code42:security | stats count by files{}.fileName
- index=botsv3 sourcetype=o365:management:activity Operation="*upload*" | stats count by Operation, SourceFileName, UserId
- index=botsv3 sourcetype=o365:management:activity UserId="*taedonggang*" | stats count by Operation, SourceFileName, SiteUrl
- index=botsv3 sourcetype=o365:management:activity | stats count by UserId
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" columns.action="CREATED" NOT columns.target_path="/tmp/*" NOT columns.target_path="/etc/*" | stats count by columns.target_path, columns.category, hostIdentifier
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" columns.action="CREATED" | stats count by columns.target_path, columns.category
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" columns.target_path="*/www/*" OR columns.target_path="*uploads*" OR columns.target_path="*html*" | stats count by columns.target_path, columns.action, hostIdentifier
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" | stats count by columns.path
- index=botsv3 sourcetype=osquery:results | stats count by name
- index=botsv3 sourcetype=stream:http "taedonggang" | stats count by uri, method, status
- index=botsv3 sourcetype=stream:http form_data="*" | stats count by uri, method
- index=botsv3 sourcetype=stream:http form_data="*taedonggang*" | stats count by form_data, uri_path, src_ip
- index=botsv3 sourcetype=stream:http http_content_type="*multipart*" | stats count by uri, site, src
- index=botsv3 sourcetype=stream:http http_method=POST | stats count by uri, status
- index=botsv3 sourcetype=stream:http site="www.brewertalk.com" http_method=POST | stats count by src_ip, uri_path, form_data, status
- index=botsv3 sourcetype=stream:http site="www.brewertalk.com" http_method=POST | stats count by uri, status
- index=botsv3 sourcetype=stream:http site="www.brewertalk.com" uri_path="/attachment.php" | stats count by uri, status, src
- index=botsv3 sourcetype=stream:http site="www.brewertalk.com" | stats count by uri_path, status
- index=botsv3 sourcetype=stream:http src_ip="174.215.8.112" form_data="*register*" | stats count by form_data, uri_path
- index=botsv3 sourcetype=stream:http src_ip="174.215.8.112" http_method=POST | stats count by uri_path, form_data, status
- index=botsv3 sourcetype=stream:http src_ip="174.215.8.112" | stats count by uri_path, uri_query, http_method, status
- index=botsv3 sourcetype=stream:http uri="*brewertalk*" | stats count by uri, method, status
- index=botsv3 sourcetype=stream:http uri_path="/xmlhttp.php" | stats count by form_data, src_ip
- index=botsv3 sourcetype=stream:mysql "taedonggang" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*INSERT*" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*INSERT*mybb_posts*" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*INSERT*mybb_users*" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*mybb_attachments*" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*mybb_users*" | stats count by query
- index=botsv3 sourcetype=stream:mysql query="*UPDATE*mybb_sessions*" | stats count by query
- index=botsv3 sourcetype=stream:mysql | stats count by query
- index=botsv3 sourcetype=stream:smtp sender="*hyunki1984*" | stats count by subject, recipient, attach_filename{}, mime_type
- index=botsv3 sourcetype=stream:smtp | stats count by attach_filename{}, sender
- index=botsv3 sourcetype=symantec:ep:behavior:file | stats count by file_name
- index=botsv3 sourcetype=symantec:ep:risk:file | stats count by file_name, risk_name
- index=botsv3 sourcetype=symantec:ep:security:file | stats count by file_name
- index=botsv3 sourcetype=WinEventLog EventCode=4663 | stats count by Object_Name
