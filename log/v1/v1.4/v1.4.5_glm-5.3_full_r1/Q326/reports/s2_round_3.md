# s2 - Q326 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=10_
**Scope:** code42:api, code42:computer, code42:security, WinHostMon (host=MKRAEUS-L), osquery:results (host=MKRAEUS-L), ess_content_importer; fields _raw, processOwner, fileName, fullPath, fileEventType, md5, columns.path, source, name
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: O365 deck events are metadata-only (FileUploaded by mkraeusen@froth.ly 09:58:42Z; FileAccessed by app@sharepoint "ExportWorker"/"Protection Center" from Azure IP 104.209.132.239 11:28:56Z); stream:smtp holds 0 mkraeusen events; keyword "advertising" 0 hits.
- R2 (this): code42:security anchors Mallory's advertising research artifact ba_advertising_code_overview.pdf; no in-scope feed carries its text; no external lookup performed.

## This round
### What I ran
- get_sourcetype_fields code42:api -> wrapper feed; endpoint field only.
- get_raw_events code42:security -> file telemetry structure: processOwner + files[]{fileName, fullPath, md5, length, mimeType, fileEventType}.
- code42:security | stats count by processOwner -> BudStoll 13, MalloryKraeusen 4.
- get_raw_events code42:security keyword=MalloryKraeusen -> 4 events: ba_advertising_code_overview.pdf DOWNLOAD then UPLOAD via chrome.exe; frothly_gabf_deck-2018-mk.pptx UPLOAD; Edge backup files.
- code42:security "ba_advertising_code_overview" (quoted) -> 0; bare token ba_advertising_code_overview.pdf -> 4 events, all MalloryKraeusen (dataset anchor; quoted phrases fail on JSON-escaped paths).
- o365:management:activity "ba_advertising_code_overview" -> 0 events.
- osquery:results host=MKRAEUS-L -> 2 sources (158 + 210 events); (ba_advertising OR gabf OR pptx OR pdf) -> 0; content is scheduled_tasks + one UAC registry key only.
- WinHostMon host=MKRAEUS-L "ba_advertising" -> 0; "advertising" -> 0 (8 sources, 16,926 events total).
- code42:api | stats count by endpoint, total_events -> wrapper counts only. code42:computer -> device inventory (BSTOLL-L, FYODOR-L). ess_content_importer -> 2 Splunkd error events.

### What it means
NOT_FOUND. The artifact that IS Mallory's advertising research is now named in dataset output: ba_advertising_code_overview.pdf, downloaded by Chrome under processOwner MalloryKraeusen to c:\users\mallorykraeusen\downloads\ (md5 2c897ddf03bce71c0536fe247121be20, 273201 bytes, application/pdf, detection 2018-08-20 ~10:31Z) and uploaded ~11:17Z from deviceRemoteAddress 12.196.122.127. But the file's content is not readable in any in-scope feed: code42:security records only file metadata, and every other scoped feed is negative. The one-word answer does not appear literally in any evidence I hold, so per the critic's ruling I report the artifact and its absence of text rather than a guessed value. No web_lookup was executed; this round is dataset-only.

## Ruled out
- code42:security as a content source - metadata only (fileName/fullPath/md5/length/mimeType); no document text field exists.
- code42:computer - device inventory only; code42:api - wrapper counts only.
- ess_content_importer - 2 Splunkd daemon error events, no content.
- osquery:results on MKRAEUS-L - scheduled tasks + UAC registry key; no file inventory naming the PDF or deck.
- WinHostMon on MKRAEUS-L - zero hits for "advertising"/"ba_advertising" across all 8 sources.
- o365:management:activity for the PDF - 0 events (only the deck has O365 events, both metadata-only).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
