# s2 - Q326 - Round 5
_stamped by runner: rounds_remaining=0 novel_spl=8_
**Scope:** ms:o365:reporting:messagetrace, stream:smtp, o365:management:activity, ms:o365:management, code42:security; fields Subject, SenderAddress, RecipientAddress, content, Operation, ObjectId, SourceFileName, UserId, fileName, fullPath
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: O365 deck events are metadata-only (upload by mkraeusen 09:58:42Z; ExportWorker access from Azure IP 11:28:56Z); stream:smtp holds 0 mkraeusen events; keyword "advertising" 0 hits.
- R2: code42:security anchors Mallory's research artifact ba_advertising_code_overview.pdf (Chrome download+upload) and the deck's local copy; no in-scope feed carries their text.
- R3: stream:http on MKRAEUS-L has no .pdf transaction (download was HTTPS, no body); SMTP "enjoyed" only in Fyodor's personal beer email; "meant to be" 0; messagetrace has no advertising subjects.
- R4 (this): Mallory's mail and all O365 content-bearing operations enumerated in full — none touches her files; the one-word value never appeared in any output.

## This round
### What I ran
- messagetrace (Sender/Recipient mkraeusen) | stats count by Subject, SenderAddress -> 39 rows, all read: Craft Brewer Conference, Upcoming Tradeshow, Wild Birthday Extravaganza, site age verification, Splunk restart, kombucha, brewertalk, Groupon. No advertising thread, no slogan.
- ms:o365:management (mkraeusen OR advertising OR advert*) | stats count by Operation, UserId -> 11 rows: Mallory SearchQueryPerformed(1), SharingInheritanceBroken(3); Fyodor eDiscovery preview/export ops.
- get_raw_events SearchQueryPerformed -> EventData carries only <ClientType>; no query text.
- get_raw_events PreviewItemRendered -> Fyodor's eDiscovery preview of "SOX\SOX_Preview\Newsfeed" (Type=html) — not Mallory's research.
- o365:management:activity UserId=mkraeusen@froth.ly -> 1 event only: the deck FileUploaded.
- o365:management:activity | stats count by Operation -> 28 types; FilePreviewed 14, FileDownloaded 1, AnonymousLink* 12.
- FilePreviewed | stats by UserId, SourceFileName -> 8 rows: bgist (3 images), fyodor (3 of his own PDFs), ghoppy (2 of her own files). Zero Mallory files.
- FileDownloaded/AnonymousLinkCreated/Used -> 5 rows: fyodor archive.tar; bgist birthday .lnk. Zero Mallory files.

### What it means
NOT_FOUND. Every content-bearing operation type in the O365 feeds — FilePreviewed, FileDownloaded, AnonymousLinkCreated/Used, eDiscovery PreviewItemRendered/SearchPreviewed — was enumerated in full and none touches Mallory's files; her only O365 footprint is the deck upload. Her 39 messagetrace rows carry no advertising research. The only named advertising artifact remains ba_advertising_code_overview.pdf, and the dataset exposes only its metadata (fileName, fullPath, md5 2c897ddf03bce71c0536fe247121be20, 273201 bytes, application/pdf, download ~10:31Z, upload ~11:17Z via Chrome from 12.196.122.127). The one-word value is not readable from accessible artifacts, and I do not submit a guess.

## Ruled out
- messagetrace as a slogan source - 39 Mallory-linked rows read in full; no advertising thread or one-word summary.
- ms:o365:management previews - Fyodor's eDiscovery previewed a Newsfeed item; SearchQueryPerformed carries no query text.
- o365:management:activity FilePreviewed/FileDownloaded/AnonymousLink - all belong to bgist, fyodor, ghoppy; zero Mallory file events beyond the upload.
- stream:smtp - "enjoyed" only in Fyodor's personal happyvalleybeer.com email; "meant to be" 0 hits; 0 mkraeusen events.
- stream:http on MKRAEUS-L - no .pdf transaction; the 10:31Z download was HTTPS, so no body is captured.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=ms:o365:management | stats count by source` (50 of 142 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: s2 has exhausted its rounds after testing the remaining in-dataset content paths. It established the named research artifact and the absence of readable text in the searched surfaces, but did not produce a literal answer value or a senior-quoted wall sufficient for a not-answerable submission.
- Scope I owned: sourcetypes=['stream:http', 'stream:smtp', 'o365:management:activity', 'ms:o365:reporting:messagetrace', 'access_combined', 'code42:api', 'code42:computer', 'code42:org', 'code42:user'] sources=[] fields=['_raw', 'content', 'content_body', 'uri_path', 'uri', 'site', 'ObjectId', 'SourceFileName', 'UserId', 'Subject', 'attach_filename']
- Rounds worked: 5/5  (iterations: 54, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv0 sourcetype=code42:security ba_advertising_code_overview.pdf | stats count
- index=botsv3 "Frothly_GABF_Deck" | stats count by sourcetype, source
- index=botsv3 sourcetype=code42:api | stats count by endpoint, total_events
- index=botsv3 sourcetype=code42:security "ba_advertising_code_overview" | stats count by processOwner, fileName, fileEventType
- index=botsv3 sourcetype=code42:security (mkraeusen OR kraeusen OR GABF OR pptx) | stats count by processOwner, fileName, fileEventType
- index=botsv3 sourcetype=code42:security ba_advertising_code_overview.pdf | stats count by processOwner
- index=botsv3 sourcetype=code42:security | stats count
- index=botsv3 sourcetype=code42:security | stats count by processOwner
- index=botsv3 sourcetype=code42:security | stats count by processOwner, fileName
- index=botsv3 sourcetype=ms:o365:management (mkraeusen OR advertising OR advert*) | stats count by Operation, UserId
- index=botsv3 sourcetype=ms:o365:management | stats count by source
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace (advertising OR advert*) | stats count by subject, sender
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace (SenderAddress=mkraeusen@froth.ly OR RecipientAddress=mkraeusen@froth.ly) | stats count by Subject, SenderAddress
- index=botsv3 sourcetype=o365:management:activity "ba_advertising_code_overview" | stats count by Operation, UserId, SourceFileName
- index=botsv3 sourcetype=o365:management:activity "Frothly_GABF_Deck" | stats count by Operation, Workload
- index=botsv3 sourcetype=o365:management:activity (Operation=FileDownloaded OR Operation=AnonymousLinkCreated OR Operation=AnonymousLinkUsed) | stats count by Operation, UserId, SourceFileName
- index=botsv3 sourcetype=o365:management:activity Operation=FilePreviewed | stats count by UserId, SourceFileName, SiteUrl
- index=botsv3 sourcetype=o365:management:activity UserId=mkraeusen@froth.ly | stats count by Operation, SourceFileName
- index=botsv3 sourcetype=o365:management:activity UserId=mkraeusen@froth.ly | stats count by Operation, SourceFileName, ObjectId
- index=botsv3 sourcetype=o365:management:activity | stats count by Operation
- index=botsv3 sourcetype=osquery:results host=MKRAEUS-L (ba_advertising OR gabf OR pptx OR pdf) | stats count by source, name
- index=botsv3 sourcetype=osquery:results host=MKRAEUS-L | stats count by name, columns.path
- index=botsv3 sourcetype=osquery:results host=MKRAEUS-L | stats count by source
- index=botsv3 sourcetype=stream:http ba_advertising | stats count by host, uri_path
- index=botsv3 sourcetype=stream:http host=MKRAEUS-L earliest=08/20/2018:10:00:00 latest=08/20/2018:10:40:00 | stats count by uri_path
- index=botsv3 sourcetype=stream:http host=MKRAEUS-L http_user_agent="Mozilla/5.0*" | stats count by _time, uri_path, dest_ip
- index=botsv3 sourcetype=stream:http host=MKRAEUS-L | stats count by http_user_agent
- index=botsv3 sourcetype=stream:smtp "meant to be" | stats count by subject
- index=botsv3 sourcetype=stream:smtp enjoyed | rex field=_raw "(?<context>.{300}enjoyed.{300})" | stats count by context
- index=botsv3 sourcetype=stream:smtp enjoyed | stats count by subject
- index=botsv3 sourcetype=stream:smtp mkraeusen | stats count by attach_filename, attach_type
- index=botsv3 sourcetype=stream:smtp mkraeusen | stats count by src_user, attachments{}.filename
- index=botsv3 sourcetype=WinHostMon host=MKRAEUS-L "ba_advertising" | stats count by source, Name, CommandLine
- index=botsv3 sourcetype=WinHostMon host=MKRAEUS-L advertising | stats count by source, Name
- index=botsv3 sourcetype=WinHostMon host=MKRAEUS-L | stats count by source
