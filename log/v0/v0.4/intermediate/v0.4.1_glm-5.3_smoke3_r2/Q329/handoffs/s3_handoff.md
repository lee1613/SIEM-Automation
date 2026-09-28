# s3 - Q329 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=11_
**Scope:** sourcetypes=access_combined, stream:http (fields uri_path, uri_query, http_method, status, form_data, clientip, bytes, referer); prior rounds covered Sysmon, o365:management:activity, and all other content routes.
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 5

## Prior rounds
- R1: Sysmon located both files on MKRAEUS-L — PDF downloaded via Chrome (hash only), PPTX named in one unread registry event.
- R2: PPTX opened from SharePoint URL in PowerPoint, never saved locally; stream:http/smb/smtp and all 6 local FileCreate events — no bytes, no derivatives.
- R3: o365 cloud activity — PPTX has 2 metadata-only records (upload + ExportWorker access), PDF has none; messagetrace, ess_content_importer, S3, CloudTrail all 0.
- R4: stream:http has no SharePoint traffic at all; MKRAEUS-L's HTTP is brewertalk.com browsing; forum POSTs are registration events.
- R5 (this round): brewertalk web-server artifacts fully enumerated — no attachment downloads, no upload POSTs, no document URIs, no multipart bodies.

## This round
### What I ran
- access_combined uri_path="/attachment.php" -> 55 events, all thumbnail=N previews (9 distinct queries, all from internal IPs); raw reads confirm portal.php referer, small image sizes.
- access_combined aid=* / /uploads/* / /attachments/* -> 0 events.
- access_combined *.pptx/*.pdf/*.docx/*.xlsx URIs -> 0 events.
- access_combined http_method=POST -> 0 events (feed is GET-only).
- access_combined full non-asset URI enumeration -> 46 paths, all read: forum pages, jscripts, suitecrm; /suitecrm/blargh.tgz is 739 bytes (too small for documents).
- stream:http form_data="*filename*" -> 0 events (no multipart upload body captured anywhere).
- stream:http xmlhttp.php POST form_data -> 32 events, all read: username-availability checks (Airwave, Trojaan, bgist@froth.ly, fyodor, bootyman, Richenip, dherrald@splunk.com) — registration chatter, not attachments.

### What it means
NOT_FOUND: the forum's web-server logs contain no attachment downloads, no upload POSTs (the feed records GETs only), and no document-extension URIs; the network feed carries no multipart upload body. No reachable artifact holds either file's bytes or text, so the oversized-font word cannot be read from the evidence available to me.

## Assumptions
- Coverage: content could appear via (a) MyBB attachment-serving endpoints — searched (attachment.php, aid=, /uploads/, /attachments/), only thumbnail previews exist; (b) document-extension URIs — searched, 0; (c) upload POSTs — searched both feeds, 0 in access_combined and no filename-bearing form_data in stream:http; (d) forum thread page HTML (showthread.php response bodies) — NOT SEARCHED (iterations exhausted) - UNVERIFIED; (e) web-server host filesystem feeds (bash_history, osquery on gacrux/hoth/mars) — NOT SEARCHED - UNVERIFIED.
- Selection: the PPTX remains the stronger candidate (only file with an upload record, matching the question's "uploaded" act) — VERIFIED as the upload act, but its content was never reached.
- Premise: the oversized word is recoverable from telemetry — UNVERIFIED after exhausting every content route in scope across five rounds.

## Ruled out
- access_combined — GET-only feed; no attachment downloads, no document URIs, no upload POSTs.
- stream:http — no SharePoint traffic, no document transfers, no multipart upload bodies (form_data with filename: 0 events).
- o365:management:activity, messagetrace, ess_content_importer, aws:s3:accesslogs, aws:cloudtrail, stream:smb, stream:smtp, WinHostMon — all 0 for both filenames (R1-R4).
- Local copies on MKRAEUS-L — PDF is hash-only; PPTX never written to disk.
- /suitecrm/blargh.tgz — 739 bytes, too small to be the documents.

## Open questions for SH
- Can a future round read stream:http response bodies of showthread.php/portal.php (the thread HTML may name or preview the uploaded attachment), or the brewertalk web-server host's own filesystem feeds (bash_history/osquery on gacrux) for MyBB's uploads directory?
- Is the intended evidence the PDF's Zone.Identifier HostUrl (showing where Chrome downloaded it from), which would tie it to the forum upload?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=access_combined | stats count by uri_path, status` (50 of 115 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: end of question (rounds)
- Scope I owned: sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon', 'Script:InstalledApps', 'Script:GetEndpointInfo', 'Script:ListeningPorts', 'openPorts'] sources=[] fields=['host', 'TargetFilename', 'Image', 'CommandLine', 'User', 'CurrentDirectory', 'process', 'path', 'file', 'filename']
- Rounds worked: 8/8  (iterations: 75, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "ba_advertising_code_overview.pdf" | stats count by sourcetype, source
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "ba_advertising_code_overview.pdf" | stats count by host, EventCode
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "frothly_gabf_deck" | stats count by host, EventCode
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=MKRAEUS-L TargetFilename="*MalloryKraeusen*" EventCode=11 | stats count by TargetFilename
- index=botsv3 sourcetype=access_combined "frothly_gabf_deck" | stats count by clientip, uri_path
- index=botsv3 sourcetype=access_combined (uri_path="*.pptx" OR uri_path="*.pdf" OR uri_path="*.docx" OR uri_path="*.xlsx") | stats count by uri_path, status
- index=botsv3 sourcetype=access_combined (uri_query="aid=*" OR uri_path="/uploads/*" OR uri_path="*/attachments/*") | stats count by uri_path, uri_query, status
- index=botsv3 sourcetype=access_combined http_method=POST | stats count by uri_path, uri_query, status
- index=botsv3 sourcetype=access_combined uri_path!="*.css" uri_path!="*.png" uri_path!="*.ico" uri_path!="/images/*" uri_path!="/cache/*" | stats count by uri_path, status
- index=botsv3 sourcetype=access_combined uri_path="/attachment.php" | stats count by clientip, uri_query, status
- index=botsv3 sourcetype=access_combined uri_path="/attachment.php" | stats count by uri_query, status, clientip
- index=botsv3 sourcetype=access_combined uri_path="/suitecrm/blargh.tgz" | stats count by clientip, status, bytes
- index=botsv3 sourcetype=access_combined | stats count by uri_path, status
- index=botsv3 sourcetype=aws:cloudtrail "frothly_gabf_deck" | stats count by eventName
- index=botsv3 sourcetype=aws:s3:accesslogs "frothly_gabf_deck" | stats count by bucket, operation
- index=botsv3 sourcetype=ess_content_importer "frothly_gabf_deck" | stats count by sourcetype
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "frothly_gabf_deck" | stats count by event_id
- index=botsv3 sourcetype=o365:management:activity "ba_advertising" | stats count by Operation, Workload
- index=botsv3 sourcetype=o365:management:activity "ba_advertising*" | stats count by Operation, SourceFileName
- index=botsv3 sourcetype=o365:management:activity "ba_advertising_code_overview.pdf" | stats count by Operation, UserId
- index=botsv3 sourcetype=o365:management:activity "frothly_gabf_deck" | stats count by Operation, UserId
- index=botsv3 sourcetype=o365:management:activity "Frothly_GABF_Deck-2018-MK.pptx" | stats count by Operation, Workload
- index=botsv3 sourcetype=o365:management:activity "gabf" | stats count by Operation, Workload
- index=botsv3 sourcetype=o365:management:activity ListItemUniqueId="0e758dde-f8a6-4376-be5c-6956a9ca84cb" | stats count by Operation, UserId
- index=botsv3 sourcetype=o365:management:activity ObjectId="*Frothly_GABF_Deck*" | stats count by Operation, UserId, UserAgent
- index=botsv3 sourcetype=o365:management:activity UserId="mkraeusen@froth.ly" | stats count by Operation, SourceFileName
- index=botsv3 sourcetype=stream:http "*.pdf" | stats count by http_method, status, uri
- index=botsv3 sourcetype=stream:http "*.pptx" | stats count by http_method, status, uri
- index=botsv3 sourcetype=stream:http "ba_advertising_code_overview.pdf" | stats count by http_method, status
- index=botsv3 sourcetype=stream:http "frothly-my.sharepoint.com" | stats count by http_method, status
- index=botsv3 sourcetype=stream:http "frothly_gabf_deck" | stats count by http_method, status
- index=botsv3 sourcetype=stream:http "sharepoint" | stats count by http_method, status, uri
- index=botsv3 sourcetype=stream:http earliest="2018-08-20T09:50:00.000Z" latest="2018-08-20T11:35:00.000Z" | stats count by http_method, status
- index=botsv3 sourcetype=stream:http earliest=2018-08-20T09:50:00 latest=2018-08-20T11:35:00 | stats count by http_method, status
- index=botsv3 sourcetype=stream:http form_data="*filename*" | stats count by site, uri_path, http_method
- index=botsv3 sourcetype=stream:http host=MKRAEUS-L | stats count by dest_host, uri
- index=botsv3 sourcetype=stream:http host=MKRAEUS-L | stats count by site, uri_path
- index=botsv3 sourcetype=stream:http site="www.brewertalk.com" (uri_path="/newreply.php" OR uri_path="/editpost.php" OR uri_path="/newthread.php") http_method=POST | stats count by host, uri_path, form_data
- index=botsv3 sourcetype=stream:http site="www.brewertalk.com" http_method=POST | stats count by host, uri_path
- index=botsv3 sourcetype=stream:http site="www.brewertalk.com" uri_path="/xmlhttp.php" http_method=POST | stats count by form_data
- index=botsv3 sourcetype=stream:http src_ip=104.209.132.239 | stats count by http_method, status
- index=botsv3 sourcetype=stream:http src_ip=107.77.212.175 | stats count by http_method, status
- index=botsv3 sourcetype=stream:http uri_path="/attachment.php" | stats count by host, uri_query, status
- index=botsv3 sourcetype=stream:http | stats count by date_hour, date_minute
- index=botsv3 sourcetype=stream:http | stats count by host
- index=botsv3 sourcetype=stream:smb "frothly_gabf_deck" | stats count by host
- index=botsv3 sourcetype=stream:smtp "ba_advertising_code_overview.pdf" | stats count by host
- index=botsv3 sourcetype=stream:smtp "frothly_gabf_deck" | stats count by host
- index=botsv3 sourcetype=WinHostMon source=process "ba_advertising*" | stats count by host, CommandLine
- index=botsv3 sourcetype=WinHostMon source=process "ba_advertising_code_overview.pdf" | stats count by host, CommandLine
- index=botsv3 sourcetype=WinHostMon source=process "frothly_gabf_deck*" | stats count by host, CommandLine
