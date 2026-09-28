# s1 - Q317 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=6_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinEventLog:Security | fields=EventCode, TargetFilename (rex from _raw), Image, ProcessId, User, ComputerName

**Insight:** partial — candidate held
**Candidate:** hdoor.exe   **Confidence:** 85

## Prior rounds
- Round 1: Sysmon EventCode 11 on FYODOR-L read in full (18 files, 4 executables); hdoor.exe earliest (18:42:49 +08), written by obfuscated PowerShell downloader PID 6360 as AzureAD\FyodorMalteskesko; hdoor.exe then ran, scanning internal hosts on 21/22/445/443.
- Round 1: full 39-row .exe list across all hosts read — no earlier .exe on FYODOR-L; rivals' .exe sets are benign installs.

## This round
### What I ran
- get_sources WinEventLog -> 6 feeds; Security = 46,469 events.
- `"Domain Admins"` in Security -> 0 hits; EventCode IN (4728,4732,...) -> 0 (extraction quirk), but count-by-EventCode showed 4728=1, 4732=2, 4720=1, 4722/4724/4738=1 each.
- `EventCode=4728 | stats by _time host` -> FYODOR-L, 18:08:17; raw read: subject AzureAD\FyodorMalteskesko added FYODOR-L\svcvnc to a security-enabled global group.
- `EventCode=4720 OR 4722 OR 4724 OR 4732 OR 4738` -> all 6 events on FYODOR-L at 18:08:17–18:08:35 (svcvnc created, enabled, password reset, group-added).

### What it means
FYODOR-L is the only endpoint where the compromised account performs privileged security-group management — creating local account svcvnc and adding it to groups — the domain-admin-style compromise acts; no other host has any such event. Combined with round 1: the complete ordered executable set on FYODOR-L is hdoor.exe (18:42:49) < iexepler.exe and unziped\lsof-master\powershell.exe (18:51:01) < DismHost.exe (19:34:24). hdoor.exe is first, written by the obfuscated -enc PowerShell downloader whose parent pulls its payload from a registry Run key — the upload/arrival act itself, followed by execution and internal scanning.

## Ruled out
- iexepler.exe / lsof-master\powershell.exe — created 18:51:01, ~5 min after hdoor.exe.
- DismHost.exe — 19:34:24, ~52 min after; benign Windows servicing binary.
- Rival endpoints (ABUNGST-L, BGIST-L, PCERF-L) — no group-management events; their .exe sets are Dropbox/Chrome/Dism installs under other accounts.
- Non-.exe files on FYODOR-L (.lnk, .ps1, .tmp, hosts.ac.tmp) — not executables.
- Literal "Domain Admins" group string in Security logs — 0 hits; attribution rests on privileged group-management acts plus SH's case knowledge.

## Open item
- One residual: no group-membership record literally titles FyodorMalteskesko "Domain Admin" (string absent from Security logs); asked SH whether AAD role records should close that or the FYODOR-L evidence suffices.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=WinEventLog source="WinEventLog:Security" | stats count by EventCo…` (50 of 61 rows seen). A claim resting on them alone is UNVERIFIED._
