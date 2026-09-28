# s2 - Q329 - Round 2
_stamped by runner: rounds_remaining=4 novel_spl=2_
**Scope:** sourcetype=symantec:ep:packet:file, symantec:ep:behavior:file, symantec:ep:risk:file, symantec:ep:traffic:file, code42:api, code42:security, WinEventLog | fields=files{}.fileName, files{}.fullPath, Application hash, Risk name, Process Command Line
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- (R1) Mapped the four artifacts in bgist@froth.ly's OneDrive "Documents/Birthday Pictures" via o365 metadata; captured ListItemUniqueIds; eliminated stream:http and stream:smtp as byte carriers.
- (R2) Eliminated all seven scoped endpoint feeds as content-bearing sources; confirmed .lnk = Backdoor.PsEmpire (SHA256 7A1367EF...A405, 5732 bytes) cleaned by deletion on 5 endpoints; images never touched endpoint disk.

## This round
### What I ran
- get_sourcetype_fields symantec:ep:packet:file / code42:api / symantec:ep:traffic:file -> all network/API metadata; no filename or content fields.
- get_raw_events symantec:ep:risk:file keyword=BRUCE -> 1 event: Backdoor.PsEmpire detection on BGIST-L, hash 7A1367EFBA05B09E317909B040C3CDA972544212B4F9DB639237492351A3A405, 5732 bytes, "Cleaned by deletion".
- get_raw_events WinEventLog keyword=Birthday -> 10 events: AV cleanups of the .lnk on MKRAEUS-L/BTUN-L/PCERF-L/BGIST-L/FYODOR-L + 4688 browser_broker events giving the .lnk retrieval URL.
- run_splunk_search code42:security file inventory -> only tar.gz/pdf/pptx/desktop.ini; zero Birthday Pictures files.
- get_raw_events WinEventLog keyword=morebeer / search stout+"Birthday Pictures" -> 0 events.

### What it means
NOT_FOUND: endpoint-side evidence retains no file bytes. The .lnk was destroyed by AV deletion everywhere it landed; the three images never appear on any endpoint — they live only in OneDrive cloud. The rendered-content answer is not recoverable from this scope.

## Ruled out
- symantec:ep:packet:file / traffic:file - network-flow metadata only, no filename or content fields.
- symantec:ep:behavior:file - application-control policy events only.
- symantec:ep:risk:file - carries the .lnk detection (hash/size) but no bytes; no image events at all.
- code42:api / code42:security - API poll metadata; file inventory covers only BudStoll's OneDrive root and MalloryKraeusen's docs/downloads.
- WinEventLog - .lnk download/process events only; zero events for morebeer/stout/Birthday Pictures images.

## Open questions for SH
- Should the next worker take ess_content_importer (Exchange message-content import) and ms:o365:reporting:messagetrace for the email bodies that delivered these files?
- The 3-4 stream:smtp "Quarentined email" events (~2018-08-20 09:16 UTC) remain unread — is a body-level extraction of those in scope for the next round?
- Is the intended "larger-font word" recoverable from stream:tcp payloads in the upload window (2018-08-20 ~09:58 UTC, ClientIP 104.207.83.63)?

## What I'd tell my replacement
- Retired because: s2 exhausted the endpoint-recovery angle and established a durable negative: the image-named files are not recoverable from the scoped Symantec, Code42, or WinEventLog evidence, while the .lnk alone was retained as malware metadata. Further progress requires a different artifact class, so this senior should hand off rather than continue on a second weak round.
- Scope I owned: sourcetypes=['stream:http', 'aws:s3:accesslogs', 'code42:security', 'stream:smtp', 'access_combined'] sources=[] fields=['uri_path', 'form_data', 'http_content_length', 'status', 'site', 'url', 'object', 'key', 'filename', 'attachment', 'subject', 'src_ip', 'dest_ip']
- Rounds worked: 2/6  (iterations: 16, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=code42:security | stats count by files{}.fileName, files{}.fullPath, files{}.fileEventType, files{}.length
- index=botsv3 sourcetype=stream:smtp stout | stats count by src, dest, subject
- index=botsv3 sourcetype=WinEventLog (stout OR "Birthday Pictures") | stats count by ComputerName, EventCode
