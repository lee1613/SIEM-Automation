# s2 - Q324 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=5_
**Scope:** WinEventLog | XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | stream:http — _raw, ComputerName, Message, CommandLine, TargetFilename, Image, form_data, uri_path, host
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 25

## Prior rounds
- R1: no phone/mobile/cell/carrier-named field exists in any of the 102 sourcetypes; code42:user, ms:aad:signin, o365:management:activity ruled out.
- R2: code42:api/computer/org, ms:aad:audit, Script:InstalledApps, WinHostMon — zero Bungstein artifacts; no carrier-branded app anywhere in the fleet.
- R3 (this round): ABUNGST-L's Windows free-text surfaces read — process telemetry, known attack tooling, .lnk downloads; no phone number or carrier.

## This round
### What I ran
- get_raw_events keyword=abungstein on WinEventLog, Sysmon, stream:http -> 0 events each (his email form appears nowhere in these feeds)
- get_raw_events WinEventLog keyword=ABUNGST-L -> 10 events: Security 4688/4689/4670 process telemetry, account AzureAD\AlBungstein
- WinEventLog "ABUNGST" | stats count by LogName, EventCode -> 36 groups, all returned: Security process events dominate (4689:596, 4688:586, 4673:561, 4957:536, 4670:345); 19 PowerShell 4104 scriptblocks
- PowerShell 4104 | stats count by EventCode, Message -> 24 rows, 12 returned and read: profile.ps1, $global:?, Get-Item hklm audit, MediaPlayer demo, iex bit.ly/e0Mw9w, obfuscated Empire-style AMSI-bypass loader, -enc base64 loader, HTML5 prototype (1 of 3) — the known BOTSv3 attack tooling; no phone or carrier string
- stream:http host=ABUNGST-L | stats count by uri_host -> 0 events — his endpoint generated no HTTP stream traffic at all
- Sysmon host=ABUNGST-L | stats count by EventCode -> 1,479 events (1:328, 3:1073, 11:14, 12:10, 13:40, 15:12, 5:2)
- Sysmon EventCode 11/15 | stats count by TargetFilename, Image -> 14 rows, all read: DismHost.exe, BRUCE BIRTHDAY HAPPY HOUR PICS .lnk download chain, __PSScriptPolicyTest .ps1, hosts.ac.tmp (Cisco AnyConnect) — no contact data

### What it means
NOT_FOUND: no carrier artifact on Bungstein's endpoint in the assigned surfaces. stream:http is fully ruled out for ABUNGST-L (zero traffic, so no form_data or carrier-site visit can exist). Sysmon file-creations read in full — no contact data. Two honest gaps remain open: 12 of 24 distinct PowerShell 4104 messages were not returned (most plausibly the "2 of 3"/"3 of 3" continuations of the HTML5 blob and duplicates, but unverified), and Sysmon's 328 process-creation command lines / 1,073 network events are counted but unread.

## Ruled out
- stream:http — 0 events for host=ABUNGST-L and 0 for abungstein
- Sysmon file-create/stream-create (EventCode 11/15) on ABUNGST-L — 14 rows read in full, no contact data
- WinEventLog Security/Application/System on ABUNGST-L — process/permission telemetry only
- PowerShell 4104 scriptblocks read (12) — benign profile plus known attack tooling, no phone/carrier

Next: Sysmon EventCode 1 command lines on ABUNGST-L, the 12 unread 4104 messages, bash_history, ess_content_importer, aws:cloudtrail, osquery:results.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p4 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_raw_events: {"keyword": "ABUNGST", "limit": 20, "sourcetype": "WinEventLog"}` (10 of 20 rows seen); `run_splunk_search: index=botsv3 sourcetype=WinEventLog "ABUNGST" LogName="microsoft-windows-powershell/operat…` (12 of 24 rows seen). A claim resting on them alone is UNVERIFIED._
