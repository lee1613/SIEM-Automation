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
