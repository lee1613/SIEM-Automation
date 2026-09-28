# s4 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=code42:security, o365:management:activity, stream:smtp | fields=files{}.fileName, files{}.fileEventType, processOwner, Operation, SourceFileName, ClientIP, UserAgent
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: literal "taedonggang"/"taedong" absent in o365:management:activity and stream:smtp; O365 FileUploaded = 7 Frothly-user uploads to own OneDrive; code42 UPLOAD events existed but were unenumerated.

## This round
### What I ran
- code42 UPLOAD `stats by fileName, fullPath, ...` -> cross-join artifact (1475 rows) — multivalue fields must be paired with mvzip first.
- `get_raw_events` on UPLOAD and "ba_advertising" -> true pairings: BudStoll uploaded frothly_html_memcached.tar.gz from desktop (md5 differs from his downloaded copy); MalloryKraeusen uploaded ba_advertising_code_overview.pdf (273201 B, md5 2c897ddf03bce71c0536fe247121be20) from her downloads via Chrome, 2018-08-20T11:17:06Z.
- `mvzip(fileName, fileEventType)` positional pairing -> the complete UPLOAD set: ba_advertising_code_overview.pdf (MalloryKraeusen), frothly_gabf_deck-2018-mk.pptx (MalloryKraeusen), frothly_html_memcached.tar.gz (BudStoll). 3 rows, read in full.
- stream:smtp for those filenames -> 0 events (SMTP is not the carrier).
- o365 mkraeusen by ClientIP/UserAgent -> FileUploaded from 107.77.212.175, UA "Microsoft Office PowerPoint 2014" (unremarkable).
- o365 remaining file ops -> fyodor FileSyncUploadedFull blargh.tgz, FileDownloaded archive.tar; FilePreviewed = beer docs only.
- stream:smtp `rex filename=` -> 7 attachment names: Employee New Hire Dates.xlsx, Malware Alert Text.txt, pwned.jpg, image001/002.jpg, 1534778082419.png, 1532632113419.png (base64-encoded name).
- from/to lookup for those emails -> 0 (phrase-OR filter fails on this feed; rex-based filter needed).

### What it means
NOT_FOUND: the upload inventory across my scope is now complete, but none of these feeds carries document content, so the oversized-font word is unrecoverable from scope as it stands. Strongest lead: ba_advertising_code_overview.pdf — uploaded from MalloryKraeusen's downloads via Chrome with no O365 counterpart, i.e. to an external destination; attribution unverified. The word itself needs content-bearing records (stream:http POST/response bodies, or the SMTP emails' full bodies), which I have not yet been able to read.

## Ruled out
- code42 stats cross-join pairing — artifact of multivalue fields; mvzip is the correct method.
- stream:smtp as carrier of the code42-uploaded files — 0 events for those filenames.
- frothly_gabf_deck-2018-mk.pptx as exfil — matches mkraeusen's own OneDrive FileUploaded (internal sync).
- frothly_html_memcached.tar.gz as attacker exfil — BudStoll's own download-then-modified-reupload; no attacker attribution.
- O365 FilePreviewed/FileModified as content sources — beer documents only, no attacker files.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: "The complete uploaded-file inventory across the three in-scope feeds is: code42:"
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "ba_advertising_code_overview.pdf is the strongest Taedonggang-upload candidate: "

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=code42:security files{}.fileEventType=UPLOAD | stats count by file…` (25 of 1475 rows seen); `get_sourcetype_fields: {"sourcetype": "stream:smtp"}` (47 of 94 rows seen). A claim resting on them alone is UNVERIFIED._
