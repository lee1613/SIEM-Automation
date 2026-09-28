# s1 - Q317 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=6_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | source=WinEventLog:Microsoft-Windows-Sysmon/Operational | fields=EventCode, TargetFilename (rex from _raw), Image, ProcessId, User, CommandLine

**Insight:** FOUND
**Candidate:** hdoor.exe   **Confidence:** 80

## Prior rounds
- Round 1: Discovered feeds; Sysmon Operational is the only file-creation telemetry (EventCode 11, 172 events). FYODOR-L confirmed present (4126 events).
- Round 1: TargetFilename is not an indexed field — values live only in _raw XML; rex extraction required.

## This round
### What I ran
- `host=FYODOR-L EventCode=11 | rex TargetFilename | stats min(_time) by TargetFilename` -> 18 distinct files, full set read; only 4 are .exe.
- Same query without host filter -> 39 .exe creations across all hosts, full set read; hdoor.exe is FYODOR-L's earliest .exe (epoch 1534761769 = 2018-08-20 18:42:49 +08).
- `EventCode=11 hdoor` -> created by powershell.exe PID 6360.
- `EventCode=1 ProcessId=6360` -> obfuscated `-enc` PowerShell downloader under AzureAD\FyodorMalteskesko; parent chain reads payload from a registry Run key.
- `get_raw_events "hdoor"` -> hdoor.exe (PID 10260) initiating TCP to 192.168.9.50 and 192.168.9.31 (sepm) on ports 21/22/445/443.

### What it means
The first executable to arrive on FYODOR-L is C:\Windows\Temp\hdoor.exe, written at 18:42:49 by an obfuscated PowerShell downloader running as AzureAD\FyodorMalteskesko — the arrival ("upload") act itself, not setup or aftermath. The file then executed and scanned internal hosts on ftp/ssh/smb/https ports, positively showing malicious tooling. Later .exe arrivals on the same host (iexeplorer.exe, powershell.exe in unziped\lsof-master at 18:51, DismHost.exe at 19:34) are all later than hdoor.exe.

## Ruled out
- iexeplorer.exe / powershell.exe (unziped\lsof-master) — created at 1534762061, ~5 min after hdoor.exe.
- DismHost.exe (FYODOR-L) — created at 1534764864, ~11 min after hdoor.exe; also a benign Windows servicing binary pattern seen on other hosts.
- Rival hosts' first .exe (ABUNGST-L DismHost.exe 1534756580, BGIST-L Dropbox suite, PCERF-L software_reporter_tool) — different hosts/accounts, not the domain-admin endpoint in scope.
- .lnk / .ps1 / .tmp files on FYODOR-L — not executables by extension; the question asks for an executable.

## Open items
- Domain-admin identity of FyodorMalteskesko not independently verified (tool budget exhausted); rests on SH's framing plus all malicious activity on FYODOR-L running as that account.
- EventCode 15 stream events (6 on FYODOR-L) not individually read; they are ADS markers, not new executables.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "XmlWinEventLog:Microsoft-Windows-Sysmon/Operational"}` (55 of 111 rows seen); `get_raw_events: {"keyword": "hdoor", "limit": 10, "sourcetype": "XmlWinEventLog:Microsoft-Windows-Sysmon/O…` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
