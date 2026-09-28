# s3 - Q329 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=12_
**Scope:** sourcetype=o365:management:activity (fields Operation, UserId, ObjectId, SourceFileName, Site_Url, SourceRelativeUrl, ClientIP); plus ms:o365:reporting:messagetrace, ess_content_importer, aws:s3:accesslogs, aws:cloudtrail as content routes.
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 5

## Prior rounds
- R1: Sysmon located both files on MKRAEUS-L — PDF downloaded via Chrome (hash only), PPTX named in one unread registry event; no content reached.
- R2: Read the PPTX registry event (opened from SharePoint in PowerPoint); swept stream:http/smb/smtp and all local FileCreate events — no bytes, no derivatives.
- R3 (this round): o365 cloud activity fully enumerated for both files — PPTX has 2 metadata-only records, PDF has none; all other cloud feeds empty.

## This round
### What I ran
- o365 "frothly_gabf_deck" -> 2 events (FileUploaded by mkraeusen@froth.ly; FileAccessed by app@sharepoint/ExportWorker); both raw-read.
- o365 UserId="mkraeusen@froth.ly" full enumeration -> exactly 1 event (the FileUploaded).
- o365 ListItemUniqueId pivot on the PPTX -> same 2 events only.
- o365 "ba_advertising_code_overview.pdf" / "ba_advertising*" / "gabf" -> 0 / 0 / same 2 events.
- ms:o365:reporting:messagetrace, ess_content_importer, aws:s3:accesslogs, aws:cloudtrail for "frothly_gabf_deck" -> 0 events each.

### What it means
NOT_FOUND: cloud activity is metadata-only. The PPTX's entire cloud footprint is one upload record (09:58:42 UTC, PowerPoint 2014, ClientIP 107.77.212.175) and one ExportWorker access (11:28:56 UTC) — no text, preview, or durable pointer to bytes. The PDF has no cloud records at all. Neither file's content is exposed by any tested feed, so the oversized-font word cannot be read from evidence in hand.

## Assumptions
- Coverage: content could appear via (a) o365 SharePoint/OneDrive records — searched exhaustively (filename, UserId, ListItemUniqueId, "gabf"), metadata-only; (b) Exchange/message-trace attachment names — searched, 0; (c) ess_content_importer — searched, 0; (d) AWS S3/CloudTrail object records — searched, 0; (e) osquery:results and Sysmon on other hosts — NOT SEARCHED (outside scope) - UNVERIFIED.
- Selection: the PPTX is the stronger candidate (only file with an upload record, matching the question's "uploaded" act; ExportWorker access hints at export) — but this is a lead, not evidence of the word - VERIFIED as upload act, UNVERIFIED as content holder.
- Premise: the oversized word is recoverable from telemetry — UNVERIFIED: no content-bearing artifact found in any tested feed.

## Ruled out
- o365:management:activity — 2 records for the PPTX, both metadata-only; 0 for the PDF.
- ms:o365:reporting:messagetrace, ess_content_importer, aws:s3:accesslogs, aws:cloudtrail — 0 events for the PPTX.
- stream:http/smb/smtp, WinHostMon, local PPTX copy on MKRAEUS-L — eliminated in R1-R2.

## Open questions for SH
- Should next round pivot to osquery:results and Sysmon on hosts other than MKRAEUS-L (e.g., where Taedonggang staged the upload), or to stream:http POST bodies around 10:30-11:30 UTC without a filename filter (the upload may have been renamed)?
- Is there any known artifact in the case holding actual file bytes for either document?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
