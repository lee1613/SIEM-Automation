# s3 - Q329 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=8_
**Scope:** sourcetype=o365:management:activity | stream:smtp | ms:o365:reporting:messagetrace | XmlWinEventLog:Sysmon | fields=Operation, SourceFileName, ClientIP, UserAgent, ObjectId, attach_filename, _raw
**Insight:** partial
**Candidate:** none   **Confidence:** 10

## Prior rounds
- R1: upload-feed enumeration — 7 O365 FileUploaded docs, code42/S3 tarballs only; stream:http POST search later found invalid (field absent). NOT_FOUND.
- R2: ransom email PNG 1534778082419.png; read_image -> FOUR. Partial.
- R3: hyunki1984@naver.com = only external SMTP sender, one file (the PNG); tied to intrusion via fyodor's exfil rule. Partial, FOUR, conf 62.
- R4: no "Taedonggang" string in any reachable raw feed; base64 body undecodable. Partial, FOUR, conf 55.
- R5: actor IP 104.207.83.63 = bgist's 4 uploads; FOUR refuted (same point size); PNG was an attachment, not an upload. Partial, none.
- R6: NaenaraBrowser/ko-KP actor fingerprint; uploads metadata-only in O365; Sysmon 0 hits for image names. Partial, none.

## This round
### What I ran
- "Quarentined email" "morebeer" -> 0 hits (earlier "stout OR morebeer" matched "stout" alone); notices are quoted-printable, about a spoofed phishing mail.
- messagetrace RecipientAddress=bgist -> 45 rows; identified the "Wild Birthday Extravaganza!!!" thread as the birthday-pics distribution.
- stream:smtp "Wild Birthday Extravaganza" -> 2 events: image002.jpg (bstoll), image001.jpg (pcerf).
- read_image image002.jpg -> 252x56 pixels, output "N" — an email signature banner, not a document with an oversized word, and not an actor upload.

### What it means
No value. The uploaded file set is established beyond doubt (bgist's four from attacker IP 104.207.83.63, NaenaraBrowser/ko-KP), but the unreadable-content wall is now proven with quotes: O365 raw events for the uploads carry only ObjectId/ListId/CorrelationId metadata; Sysmon returns zero events for "morebeer" OR "stout"; stream:smtp has no attachment with those names; the uploads went to OneDrive over HTTPS, which stream:http (port 80 only) cannot carry. The one image content reachable on the birthday thread is a 252x56 signature banner. The word is not recoverable from the feeds I reached.

## Ruled out
- FOUR / ransom PNG - not a larger point size; an attachment, not an upload.
- image002.jpg "N" - 252x56 signature banner, internal email, not an actor upload.
- O365 audit, Sysmon, stream:smtp, messagetrace as content carriers for the uploaded images - metadata-only or zero hits (quoted above).
- stream:http upload bodies - HTTPS destination, port-80-only capture.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: s3 is out of rounds and established that its O365/mail/Sysmon scope holds only metadata references for the attacker-linked uploads, not readable image bytes. Further progress requires a different feed family, which must be assigned on the next turn after this retirement frees the slot.
- Scope I owned: sourcetypes=['access_combined', 'aws:elb:accesslogs', 'aws:s3:accesslogs', 'aws:cloudtrail', 'code42:api', 'code42:computer', 'code42:org', 'code42:security', 'code42:user', 'stream:http', 'stream:smtp', 'symantec:ep:agent:file', 'symantec:ep:behavior:file', 'symantec:ep:packet:file', 'symantec:ep:risk:file', 'symantec:ep:scm_system:file', 'symantec:ep:security:file', 'symantec:ep:traffic:file'] sources=[] fields=['_raw', 'source', 'uri', 'url', 'http_method', 'form_data', 'filename', 'file_name', 'name', 'subject', 'sender', 'recipient', 'object', 'key', 'path']
- Rounds worked: 8/8  (iterations: 82, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "taedonggang" | stats count by sourcetype, source
- index=botsv3 sourcetype=* "taedonggang" | stats count by sourcetype, source
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "morebeer" OR "stout" OR "BRUCE BIRTHDAY" | stats count by SenderAddress, Subject
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "taedonggang" | stats count
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace hyunki1984 | stats count by SenderAddress, RecipientAddress, Subject
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace RecipientAddress="bgist@froth.ly" | stats count by SenderAddress, Subject
- index=botsv3 sourcetype=o365:management:activity "taedonggang" | stats count
- index=botsv3 sourcetype=o365:management:activity 104.207.83.63 | stats count by Operation, UserId, ClientIP
- index=botsv3 sourcetype=o365:management:activity ClientIP=104.207.83.63 Operation="FileModified" | stats count by SourceFileName, CreationTime
- index=botsv3 sourcetype=o365:management:activity ClientIP=104.207.83.63 Operation="FilePreviewed" | stats count by SourceFileName, SiteUrl
- index=botsv3 sourcetype=o365:management:activity ClientIP=104.207.83.63 | stats count by UserAgent, Operation
- index=botsv3 sourcetype=o365:management:activity hyunki1984 | stats count by Operation, UserId
- index=botsv3 sourcetype=o365:management:activity Operation IN ("Uploaded","FileUploaded","Upload","SharePointFileOperation") | stats count by Operation, UserId
- index=botsv3 sourcetype=o365:management:activity Operation="FileUploaded" | stats count by UserId, SourceFileName, ClientIP, CreationTime
- index=botsv3 sourcetype=o365:management:activity Operation="FileUploaded" | stats count by UserId, SourceFileName, ObjectId, SourceRelativeUrl
- index=botsv3 sourcetype=o365:management:activity Operation="FileUploaded" | stats count by UserId, SourceFileName, SiteUrl
- index=botsv3 sourcetype=stream:http http_method=POST | stats count by uri_host, uri_path
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "boundary=[\\\\\"-]+(?<bnd>[A-Za-z0-9_=-]+)" | stats count by bnd
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "Content-Transfer-Encoding: (?<cte>[^\\\\\r\n]+)" | stats count by cte
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "Content-Transfer-Encoding: base64[\\\\r\\\\n]+(?<b64>[A-Za-z0-9+/=]{200,})" | eval decoded=if(isnotnull(b64), substr(b64, 1, 4000), "") | stats count by decoded
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "From: (?<from_hdr>[^\\\\]+)" | rex field=_raw "smtp\\.mailfrom=(?<mailfrom>[^\\\\\"]+)" | rex field=_raw "Return-Path: <(?<return_path>[^>]+)>" | stats count by from_hdr, mailfrom, return_path
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "Content-Transfer-Encoding: base64(?<b64>.{1300})" | rex field=_raw "quoted-printable(?<qp>.{1300})" | stats count by from_addr, substr(b64,1,1300), substr(qp,1,1300)
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "mailfrom=(?<mailfrom>[^;]+)" | stats count by from_addr, mailfrom
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "To: (?<to_hdr>[^\\\\]+)" | rex field=_raw "Date: (?<date_hdr>[^\\\\]+)" | stats count by from_addr, to_hdr, date_hdr
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "quoted-printable(?<body>.{2200})" | stats count by substr(body,1,2200)
- index=botsv3 sourcetYpe=stream:smtp "All your datas belong to us" | rex field=_raw "quoted-printable(?<qp>.{1300})" | stats count by substr(qp,1,1300)
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "quoted-printable[\\\\r\\\\n]+(?<body>.{2200})" | rex field=_raw "quoted-printable[\\\\r\\\\n]+(?<body2>.{2200})" | stats count by substr(body,1,2200), substr(body2,1,2200)
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "quoted-printable[\\\\r\\\\n]+(?<body>.{2200})" | stats count by substr(body,1,2200)
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | stats count
- index=botsv3 sourcetype=stream:smtp "Birthday" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "Subject: (?<subj>[^\\\\]+)" | rex field=_raw "\"attach_filename\":\[(?<attaches>[^\]]*)\]" | stats count by from_addr, subj, attaches
- index=botsv3 sourcetype=stream:smtp "BRUCE BIRTHDAY" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "Subject: (?<subj>[^\\\\]+)" | rex field=_raw "\"attach_filename\":\[(?<attaches>[^\]]*)\]" | stats count by from_addr, subj, attaches
- index=botsv3 sourcetype=stream:smtp "Employee New Hire Dates.xlsx" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "To: (?<to_hdr>[^\\\\]+)" | rex field=_raw "Subject: (?<subj>[^\\\\]+)" | stats count by from_addr, to_hdr, subj
- index=botsv3 sourcetype=stream:smtp "Fw: All your datas belong to us" | rex field=_raw "quoted-printable(?<body>.{2500})" | stats count by substr(body,1,2500)
- index=botsv3 sourcetype=stream:smtp "Fw: All your datas belong to us" | rex field=_raw "text/plain; charset=\\\\\"us-ascii\\\\\"(?<body>.{3000})" | stats count by substr(body,1,3000)
- index=botsv3 sourcetype=stream:smtp "Malware Alert Text.txt" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "To: (?<to_hdr>[^\\\\]+)" | rex field=_raw "Subject: (?<subj>[^\\\\]+)" | stats count by from_addr, to_hdr, subj
- index=botsv3 sourcetype=stream:smtp "MWHPR17MB124780ACE6F28E61609F84EABF2B0" | rex field=_raw "namp_(?<fwd>.{1500})" | stats count by substr(fwd,1,1500)
- index=botsv3 sourcetype=stream:smtp "Quarentined email" "morebeer" | stats count
- index=botsv3 sourcetype=stream:smtp "Quarentined email" | rex field=_raw "(?<pre>.{0,250})morebeer(?<post>.{0,250})" | stats count by pre, post
- index=botsv3 sourcetype=stream:smtp "Quarentined email" | rex field=_raw "beer(?<frag>.{0,200})" | stats count by substr(frag,1,200)
- index=botsv3 sourcetype=stream:smtp "Quarentined email" | rex field=_raw "Content-Transfer-Encoding: (?<cte>[^\\\\\r\n]+)" | stats count by cte
- index=botsv3 sourcetype=stream:smtp "Quarentined email" | rex field=_raw "morebeer(?<post>.{0,300})" | stats count by substr(post,1,300)
- index=botsv3 sourcetype=stream:smtp "stout" OR "morebeer" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "Subject: (?<subj>[^\\\\]+)" | stats count by from_addr, subj
- index=botsv3 sourcetype=stream:smtp "taedonggang" | stats count
- index=botsv3 sourcetype=stream:smtp "Wild Birthday Extravaganza" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "\"attach_filename\":\[(?<attaches>[^\]]*)\]" | stats count by from_addr, attaches
- index=botsv3 sourcetype=stream:smtp attach_filename | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "\"attach_filename\":\[(?<attaches>[^\]]*)\]" | stats count by from_addr, attaches
- index=botsv3 sourcetype=stream:smtp attach_filename | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "Subject: (?<subj>[^\\\\]+)" | rex field=_raw "\"attach_filename\":\[(?<attaches>[^\]]*)\]" | stats count by from_addr, attaches, subj
- index=botsv3 sourcetype=stream:smtp attach_filename=* | stats count by attach_filename, attach_type
- index=botsv3 sourcetype=stream:smtp hyunki1984 | rex field=_raw "\"attach_filename\":\[(?<attaches>[^\]]*)\]" | rex field=_raw "Subject: (?<subject>[^\\\\]+)" | stats count by subject, attaches
- index=botsv3 sourcetype=stream:smtp pwned.jpg | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "To: (?<to_hdr>[^\\\\]+)" | rex field=_raw "Subject: (?<subj>[^\\\\]+)" | rex field=_raw "Date: (?<date_hdr>[^\\\\]+)" | stats count by from_addr, to_hdr, subj, date_hdr
- index=botsv3 sourcetype=stream:smtp | mvexpand attach_filename | stats count by attach_filename, attach_type
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | stats count by from_addr
- index=botsv3 sourcetype=stream:stream:smtp "All your datas belong to us" | rex field=_raw "quoted-printable[\\\\r\\\\n]+(?<body>.{2200})" | stats count by substr(body,1,2200)
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "BRUCE BIRTHDAY" EventCode=11 | stats count by TargetFilename, Image
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "BRUCE BIRTHDAY" | stats count by EventCode
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "morebeer" OR "stout" | stats count by EventCode, TargetFilename
