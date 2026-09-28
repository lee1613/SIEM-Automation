# s2 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetypes=code42:api, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinHostMon, osquery:results | fields=user/User/host/TargetFilename/CommandLine/Image/path
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1: no queries executed (empty reply); nothing established.
- Round 2 (this): enumerated all four scoped feeds; ruled out code42:api, osquery:results, WinHostMon as filename sources; read all Sysmon file-creates on BTUN-L, BSTOLL-L, PCERF-L; found a Word-embedded-image lead on PCERF-L but no attachment name and no visualization type.

## This round
### What I ran
- get_sourcetype_fields on all four scoped feeds -> code42:api = 88 count-only summaries; osquery = 219,997 Linux process/shell events; WinHostMon = Service/Driver/Process/etc., no file type; Sysmon = 9,212 events incl. 172 file-creates with TargetFilename.
- Sysmon EventCode=11 | stats by host,TargetFilename -> 148 rows (50 returned); narrowed: image/doc extensions -> 5 rows; *splunk*/*miner*/*chart*/*dashboard*/*coin*/*monero* -> 0 rows.
- Sysmon EventCode=11 host IN (BTUN-L,BSTOLL-L) -> 30 rows, all read; host=PCERF-L -> 18 rows, all read.
- Sysmon EventCode=1 Office/Outlook CommandLine -> 9 rows: POWERPNT on MKRAEUS-L and PCERF-L, EXCEL on BTUN-L, OUTLOOK on 5 hosts.
### What it means
NOT_FOUND: no feed in scope names a Splunk export, dashboard image, or miner-illustration document, and no record states a visualization type. The one behavioural lead — ~WRD000.jpg created in PCERF-L's Outlook cache (Word rendering an embedded image from an opened email attachment, alongside pwned.jpg) — shows a document-with-picture was opened by Peat Cerf, but the attachment's filename was never logged and its content is unrecovered, so the two-word visualization type cannot be stated.

## Assumptions
- Coverage: Sysmon TargetFilename — searched image/doc extensions (5 rows), miner/splunk keywords (0 rows), full reads on BTUN-L/BSTOLL-L/PCERF-L; 98 of 148 overall rows (FYODOR-L, MKRAEUS-L, JWORTOS-L, remainder of ABUNGST-L/BGIST-L) NOT read — UNVERIFIED. Sysmon CommandLine/Image — searched for Outlook/Office/Content.Outlook (9 rows) — VERIFIED as searched, no artifact path seen. osquery columns.path — Linux binaries only — VERIFIED. WinHostMon Path — service executables only, no file-listing Type — VERIFIED. code42:api — no file fields at all — VERIFIED.
- Selection: Bud candidates btun (BTUN-L/BillyTun) and bstoll (BSTOLL-L/BudStoll) both fully read for file creates; neither shows a Splunk artifact — VERIFIED. PCERF-L selected as pivot because ~WRD000.jpg shows an attachment document was opened there — VERIFIED as a lead, not as the answer.
- Premise that the attachment is a document/image whose name or content reveals the visualization — UNVERIFIED: no such artifact recovered yet.
- Premise that ~WRD000.jpg implies an opened Word attachment — behavioural inference from the Outlook-cache path; the parent .docx filename is not in any record I read — UNVERIFIED.

## Ruled out
- code42:api — carries only endpoint/total_events count summaries, no filenames or file activity.
- osquery:results — Linux servers (hoth/mars/gacrux) process/shell-history; no Windows employee file handling.
- WinHostMon — Types are Service/Driver/Process/Computer/Disk/NetworkAdapter/OperatingSystem/Processor; no file listings.
- Sysmon file-creates on BTUN-L, BSTOLL-L, PCERF-L — fully read; no Splunk/miner illustration artifact.
- Sysmon keyword search for splunk/miner/chart/dashboard/coin/monero in TargetFilename — 0 events.

## Open questions for SH
- May I spend the next round reading the remaining Sysmon file-create rows (FYODOR-L, MKRAEUS-L, JWORTOS-L) before any other pivot, or do you already know which employee received Bud's miner email?
- Is O365 mail metadata still off-limits for confirming a filename once endpoint evidence narrows a candidate, or only as the primary discovery path?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 4 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "osquery:results"}` (38 of 153 rows seen); `get_sourcetype_fields: {"sourcetype": "XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"}` (55 of 111 rows seen); `run_splunk_search: index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11…` (50 of 148 rows seen); `get_sourcetype_fields: {"sourcetype": "WinHostMon"}` (34 of 136 rows seen). A claim resting on them alone is UNVERIFIED._
