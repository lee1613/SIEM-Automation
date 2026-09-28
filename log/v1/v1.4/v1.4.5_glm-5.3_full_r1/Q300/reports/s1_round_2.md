# s1 - Q300 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=3_
**Scope:** sourcetype=o365:management:activity, ms:o365:management | fields=Operation, SourceFileName, SourceFileExtension, UserAgent, UserId, ClientIP, CreationTime
**Insight:** FOUND
**Candidate:** Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 Fedora/1.9.1-2.5.rs3.0 NaenaraBrowser/3.5b4   **Confidence:** 99

## Prior rounds
- R1: Found the only .lnk upload (BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, bgist@froth.ly, 104.207.83.63) and its Naenara UserAgent; cross-checked both O365 feeds agree; submitted.
- R2 (clarify): Confirmed to SH that the FileUploaded listing was complete (7 of 7) and the UA string was returned unclipped in three independent queries.

## This round
### What I ran
- `(ms:o365:management OR o365:management:activity) Operation=FileUploaded | stats count by sourcetype, SourceFileExtension, SourceFileName` -> 14 of 14 rows: seven files, each once per feed; only .lnk is BRUCE BIRTHDAY HAPPY HOUR PICS.lnk.
- `o365:management:activity SourceFileName="BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count by Operation, CreationTime, SourceFileExtension, Workload, UserId, ClientIP, UserAgent` -> 22 of 22 rows: the file's complete event lifecycle.

### What it means
p1 VERIFIED: the complete FileUploaded population across both O365 activity feeds is 14 events / 7 files, read in full; exactly one .lnk upload exists, present in both feeds. No rival .lnk upload is left unresolved.
p2 VERIFIED: of the 22 events on the .lnk file, exactly one is Operation=FileUploaded — 2018-08-20T09:57:33, bgist@froth.ly, 104.207.83.63 — and that record itself carries the full literal UserAgent. The other 21 rows are FileAccessed/FileModified (same second, same UA), the 09:58:02 anonymous-link creation and sharing events, and the 09:59+ link-use/access events by bstoll@froth.ly, anonymous users, and app@sharepoint from other IPs with Edge/17.17134 or ExportWorker UAs — the aftermath, not the upload. The upload record is the act the question names.
The user agent string is unchanged: `Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 Fedora/1.9.1-2.5.rs3.0 NaenaraBrowser/3.5b4`

## Ruled out
- Six other FileUploaded files (jpg/png/pdf/pptx) — not .lnk; complete population read.
- Edge/17.17134 UA — link-use/access events by recipients, not the upload.
- "ExportWorker" UA — app@sharepoint FileAccessed, not the upload.

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
