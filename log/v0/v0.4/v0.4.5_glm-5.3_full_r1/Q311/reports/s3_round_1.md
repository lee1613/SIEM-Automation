# s3 - Q311 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=3_
**Scope:** sourcetype=symantec:ep:risk:file, o365:management:activity, WinEventLog:Microsoft-Windows-PowerShell/Operational | fields: Application_Name, file_path, file_hash, Risk_Name, ObjectId, ComputerName, Message
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- (Round 1 — this report.)

## This round
### What I ran
- get_source_types -> 102 sourcetypes; identified symantec:ep:* family, o365:management:activity, WinEventLog sub-feeds.
- get_sourcetype_fields sourcetype=symantec:ep:risk:file -> 1 event total: Backdoor.PsEmpire on BGIST-L (BruceGist, 2018-08-20 09:58:20), file_path c:\users\brucegist\onedrive - frothly\birthday pictures\bruce birthday happy hour pics.lnk, SHA2 7A1367EF...3A405, 5732 bytes. Field list contains NO payload name — the detection names only the .lnk itself.
- get_sourcetype_fields sourcetype=o365:management:activity -> ObjectId confirms the OneDrive copy (BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, 24 events); no payload naming.
- search_keyword "lnk" -> 0 results (no lnk-named fields in the manifest).
- get_sources WinEventLog -> 6 feeds, incl. Microsoft-Windows-PowerShell/Operational (92 events).
- get_raw_events PowerShell/Operational (first 10) -> ABUNGST-L scriptblocks only in the sample read.
- run_splunk_search PowerShell/Operational | stats count by ComputerName -> ABUNGST-L=28, **BGIST-L=21**, FYODOR-L=43.

### What it means
NOT_FOUND: the Symantec risk feed — the named detection artifact — carries only the .lnk's own name, hash and path, with no field for an embedded executable. The OneDrive activity trail likewise names only the .lnk. The decisive unread evidence is the 21 BGIST-L PowerShell scriptblock events (EventCode 4104), which I confirmed exist but did not reach before the iteration cap; the .lnk's embedded command line and the payload it names should appear there. Next round reads those 21 events in full, then stream:http for the payload fetch, then the remaining symantec:ep:* feeds and the mail trace.

## Ruled out
- symantec:ep:risk:file as payload-naming evidence - its only event names the .lnk itself; no payload field exists in the feed.
- o365:management:activity ObjectId - OneDrive URLs only, no payload metadata.
- search_keyword "lnk" - no lnk-named fields exist anywhere in the dataset manifest.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "o365:management:activity"}` (31 of 125 rows seen); `get_raw_events: {"limit": 10, "source": "WinEventLog:Microsoft-Windows-PowerShell/Operational", "sourcetyp…` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
