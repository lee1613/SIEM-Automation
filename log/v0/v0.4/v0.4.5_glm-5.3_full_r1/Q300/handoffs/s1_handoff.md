# s1 - Q300 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=4_
**Scope:** sourcetype=o365:management:activity, ms:o365:management | fields=Operation, SourceFileName, SourceFileExtension, CreationTime, UserId, ClientIP, UserAgent
**Insight:** FOUND
**Candidate:** Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 Fedora/1.9.1-2.5.rs3.0 NaenaraBrowser/3.5b4   **Confidence:** 99

## Prior rounds
- R1: Found the only .lnk upload (BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, bgist@froth.ly, 104.207.83.63) and its Naenara UserAgent; both O365 feeds agree; submitted.
- R2 (clarify): Confirmed to SH the FileUploaded listing was complete (7 of 7) and the UA string was returned unclipped in three independent queries.
- R3: Filed premise verdicts for p1/p2; quotes were re-filed this round word-for-word without ellipses.

## This round
### What I ran
- `(ms:o365:management OR o365:management:activity) Operation=FileUploaded | stats dc(sourcetype) as feeds, values(SourceFileName) as file_names by SourceFileExtension` -> 5 of 5 rows: jpg, lnk, pdf, png, pptx; lnk group = BRUCE BIRTHDAY HAPPY HOUR PICS.lnk only, feeds=2.
- `Operation=FileUploaded SourceFileExtension=lnk | stats count by Operation, CreationTime, SourceFileName, SourceFileExtension, UserId, ClientIP, UserAgent` -> 1 of 1 row: the exact upload record with the full UserAgent (count 2 = same record mirrored in both feeds).
- `o365:management:activity SourceFileName="BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count by Operation, CreationTime, UserId, ClientIP, UserAgent` -> 22 of 22 rows: the file's complete lifecycle; exactly one FileUploaded row.

### What it means
p1 VERIFIED: the complete FileUploaded population across both O365 activity feeds is five extensions / seven files, each in both feeds; the only .lnk is BRUCE BIRTHDAY HAPPY HOUR PICS.lnk. No rival .lnk upload exists.
p2 VERIFIED: the single FileUploaded record for the .lnk (2018-08-20T09:57:33, bgist@froth.ly, 104.207.83.63) itself carries the full literal UserAgent. The other 21 lifecycle rows are access, modification, sharing, and anonymous-link-use events — the setup and aftermath, not the upload — with Edge/17.17134 or ExportWorker UAs.
User agent string, unchanged and literal: `Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 Fedora/1.9.1-2.5.rs3.0 NaenaraBrowser/3.5b4`

## Ruled out
- Six other uploaded files (jpg/png/pdf/pptx) — not .lnk; complete population read.
- Edge/17.17134 UA — link-use/access events by recipients, not the upload.
- "ExportWorker" UA — app@sharepoint FileAccessed, not the upload.

## What I'd tell my replacement
- Retired because: end of question (turns)
- Scope I owned: sourcetypes=['o365:management:activity', 'ms:o365:management'] sources=[] fields=['Operation', 'Workload', 'UserAgent', 'UserId', 'SourceFileName', 'ObjectId', 'ClientIP', 'RecordType']
- Rounds worked: 3/3  (iterations: 19, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 (sourcetype=ms:o365:management OR sourcetype=o365:management:activity) Operation=FileUploaded SourceFileExtension=lnk | stats count by Operation, CreationTime, SourceFileName, SourceFileExtension, UserId, ClientIP, UserAgent
- index=botsv3 (sourcetype=ms:o365:management OR sourcetype=o365:management:activity) Operation=FileUploaded SourceFileExtension=lnk | stats count by sourcetype, SourceFileName, UserAgent
- index=botsv3 (sourcetype=ms:o365:management OR sourcetype=o365:management:activity) Operation=FileUploaded | stats count by sourcetype, SourceFileExtension, SourceFileName
- index=botsv3 (sourcetype=ms:o365:management OR sourcetype=o365:management:activity) Operation=FileUploaded | stats count by sourcetype, SourceFileName, SourceFileExtension, CreationTime, UserId, ClientIP, UserAgent
- index=botsv3 (sourcetype=ms:o365:management OR sourcetype=o365:management:activity) Operation=FileUploaded | stats dc(sourcetype) as feeds, values(SourceFileName) as file_names by SourceFileExtension
- index=botsv3 sourcetype=o365:management:activity Operation=FileUploaded ObjectId="*BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count by UserAgent, UserId, ClientIP, CreationTime
- index=botsv3 sourcetype=o365:management:activity Operation=FileUploaded SourceFileName="BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count by UserAgent
- index=botsv3 sourcetype=o365:management:activity Operation=FileUploaded | stats count by ObjectId, UserId, ClientIP
- index=botsv3 sourcetype=o365:management:activity SourceFileName="BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" Operation=FileUploaded | table CreationTime, Operation, SourceFileName, SourceFileExtension, Workload, UserId, ClientIP, UserAgent
- index=botsv3 sourcetype=o365:management:activity SourceFileName="BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count by Operation, CreationTime, SourceFileExtension, Workload, UserId, ClientIP, UserAgent
- index=botsv3 sourcetype=o365:management:activity SourceFileName="BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count by Operation, CreationTime, UserId, ClientIP, UserAgent
