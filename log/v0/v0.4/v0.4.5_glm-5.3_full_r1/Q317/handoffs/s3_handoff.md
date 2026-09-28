# s3 - Q317 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=4_
**Scope:** sourcetype=symantec:ep:risk:file | sourcetype=symantec:ep:security:file | sourcetype=osquery:results | sourcetype=stream:smb | sourcetype=stream:http | fields: file_name, Computer_Name, Host_Name, host, src_ip, dest_ip, service, command, bytes, _time
**Insight:** FOUND
**Candidate:** hdoor.exe   **Confidence:** 92

## Prior rounds
- R1 (s1): Sysmon EventCode=11 *.exe searched dataset-wide — 39 events on 8 hosts, all read; FYODOR-L flagged for C:\Windows\Temp attacker artifacts; BSTOLL-L ruled out (Windows Update artifact only).
- R2 (me): fyodor@froth.ly established as the domain admin (only ms:aad:audit actor assigning the "Company Administrator" role); identity tied to FYODOR-L alone (Sysmon EventCode=1, 107 events; WinEventLog, 2,543 events); earliest executable on FYODOR-L = C:\Windows\Temp\hdoor.exe at 2018-08-20 18:42:49, written by powershell.exe. Submitted hdoor.exe.
- R3 (this round): closed the residual coverage gap — no unsearched feed records an earlier executable on FYODOR-L.

## This round
### What I ran
- get_sourcetype_fields symantec:ep:risk:file -> 1 event dataset-wide: "Bruce Birthday Happy Hour Pics.lnk" on BGIST-L (Backdoor.PsEmpire) — a .lnk, not an executable, not FYODOR-L.
- get_sourcetype_fields symantec:ep:security:file -> 46 events, all on BTUN-L: JSCoinminer web-attack blocks naming browser processes — no FYODOR-L records, no uploaded files.
- `sourcetype=osquery:results | stats count by host` -> 8 rows, all read: BSTOLL-L, MKRAEUS-L, gacrux.*, hoth, mars.* — no FYODOR-L records at all.
- `sourcetype=stream:smb | stats count by host` -> 8 hosts including FYODOR-L (10 events).
- `sourcetype=stream:smb host=FYODOR-L | stats count by _time, src_ip, dest_ip, service, command, bytes` -> 10 rows, all read: every one a periodic NetBIOS browse broadcast (192.168.70.186 -> 192.168.70.255, \MAILSLOT\BROWSE, 209 bytes) — no filename field, no file transfer.
- `sourcetype=stream:http host=FYODOR-L | stats count by uri, src_ip, dest_ip` -> 0 events.

### What it means
FOUND, unchanged. Every feed named in the open coverage premise p1 has now been searched, and none records an executable arriving on FYODOR-L before 2018-08-20 18:42:49. Symantec's two file feeds carry nothing on FYODOR-L (one holds a single .lnk on BGIST-L; the other 46 browser-process web-attack blocks on BTUN-L). osquery:results has zero FYODOR-L records. FYODOR-L's ten stream:smb events are filename-less NetBIOS browse broadcasts, and stream:http has zero FYODOR-L events. Sysmon EventCode=11 is therefore the only feed recording executable file creation on FYODOR-L, and its complete 4-row listing was read in full in round 2: the earliest executable is C:\Windows\Temp\hdoor.exe at 18:42:49, written by powershell.exe, which then ran under the fyodor account scanning internal hosts. The answer stands: hdoor.exe.

## Ruled out
- symantec:ep:risk:file as a source of an earlier FYODOR-L executable — its only event is a .lnk on BGIST-L.
- symantec:ep:security:file — all 46 events on BTUN-L; browser-process web-attack blocks, no file uploads.
- osquery:results — no FYODOR-L records at all (8 hosts listed, none is FYODOR-L).
- stream:smb — FYODOR-L's 10 events are \MAILSLOT\BROWSE broadcasts with no filename field.
- stream:http — zero FYODOR-L events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: end of question (turns)
- Scope I owned: sourcetypes=['ms:aad:audit', 'o365:management:activity', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'] sources=['/tenantdomains/froth.ly', 'WinEventLog:Microsoft-Windows-Sysmon/Operational'] fields=['activity', 'actor.userPrincipalName', 'targets{}.userPrincipalName', 'Operation', 'UserId', '_time', 'TargetFilename', 'Image', 'host']
- Rounds worked: 2/5  (iterations: 22, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=ms:aad:audit "Add member to role" | stats count by _time, actor.userPrincipalName, targets{}.userPrincipalName, targets{}.modifiedProperties{}.newValue
- index=botsv3 sourcetype=ms:aad:audit | stats count by actor.userPrincipalName, activity, targets{}.userPrincipalName, targets{}.name
- index=botsv3 sourcetype=osquery:results | stats count by host
- index=botsv3 sourcetype=stream:http host=FYODOR-L | stats count by uri, src_ip, dest_ip
- index=botsv3 sourcetype=stream:smb host=FYODOR-L | stats count by _time, src_ip, dest_ip, service, command, bytes
- index=botsv3 sourcetype=stream:smb | stats count by host
- index=botsv3 sourcetype=WinEventLog fyodor | stats count by host
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational EventCode=1 user="*fyodor*" | stats count by host, user
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational host=FYODOR-L EventCode=11 hdoor | stats count by _time, TargetFilename, Image, ProcessGuid
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational host=FYODOR-L EventCode=11 TargetFilename="*.exe" | stats count by _time, TargetFilename, process_name, Image, ParentImage
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational host=FYODOR-L EventCode=11 TargetFilename="*.exe" | stats min(_time) as first_time, count by TargetFilename | sort first_time | convert ctime(first_time)
