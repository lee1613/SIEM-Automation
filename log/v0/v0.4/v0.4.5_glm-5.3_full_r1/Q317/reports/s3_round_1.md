# s3 - Q317 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=7_
**Scope:** sourcetype=ms:aad:audit | sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | sourcetype=WinEventLog | fields: actor.userPrincipalName, activity, targets{}.modifiedProperties{}.newValue, user, host, TargetFilename, Image
**Insight:** FOUND
**Candidate:** hdoor.exe   **Confidence:** 88

## Prior rounds
- R1 (s1): Sysmon EventCode=11 *.exe searched dataset-wide — 39 events on 8 hosts, all read; FYODOR-L flagged for attacker artifacts in C:\Windows\Temp; BSTOLL-L ruled out (only a Windows Update artifact). Admin-identity-to-host link untested; Symantec/stream/osquery feeds unsearched.

## This round
### What I ran
- `sourcetype=ms:aad:audit | stats count by actor.userPrincipalName, activity, targets{}.userPrincipalName` -> 15 rows, all read: fyodor@froth.ly performs role admin, password resets, account disables; bstoll@froth.ly only group membership.
- `ms:aad:audit "Add member to role"` -> 4 rows: fyodor assigned "Company Administrator"/"TenantAdmins" to klagerfield@froth.ly.
- `Sysmon EventCode=1 user="*fyodor*" | stats count by host, user` -> 1 row: FYODOR-L, AzureAD\FyodorMalteskesko, 107 events.
- `Sysmon host=FYODOR-L EventCode=11 TargetFilename="*.exe" | stats min(_time) by TargetFilename` -> 4 rows, all read: hdoor.exe 18:42:49; iexeplorer.exe and powershell.exe 18:47:41; DismHost.exe 19:34:24.
- `Sysmon host=FYODOR-L EventCode=11 hdoor` -> 1 row: hdoor.exe created by powershell.exe at 18:42:49.
- get_raw_events hdoor.exe -> EventCode=3 rows: hdoor.exe running as FyodorMalteskesko, scanning 192.168.9.50 (ftp/ssh/445) and sepm (443/445).
- `WinEventLog fyodor | stats count by host` -> 1 row: FYODOR-L only (2,543 events).

### What it means
FOUND. Identity: fyodor@froth.ly is the only ms:aad:audit actor performing directory-role administration — assigning the "Company Administrator" role — an admin-only act, establishing the domain admin identity from Microsoft admin-activity records. Endpoint: the fyodor identity (AzureAD\FyodorMalteskesko) appears on exactly one host, FYODOR-L, in both Sysmon process events and WinEventLog, tying the admin to that endpoint. First executable: the complete Sysmon EventCode=11 *.exe listing on FYODOR-L (4 rows, every row read) shows the earliest executable creation is C:\Windows\Temp\hdoor.exe at 2018-08-20 18:42:49, written by powershell.exe (a download/drop); hdoor.exe then ran under the fyodor account scanning internal hosts — the compromise act. Answer: hdoor.exe.

## Ruled out
- BSTOLL-L as the admin's endpoint — bstoll@froth.ly shows only group-membership activity in ms:aad:audit (no role administration), and the fyodor identity appears on no host but FYODOR-L.
- iexepler.exe, lsof-master powershell.exe, DismHost.exe as "first" — all created after hdoor.exe in the complete 4-row listing.
- Not yet checked (residual gap): symantec:ep:*:file, stream:http/stream:smb, osquery:results file tables for an earlier executable on FYODOR-L.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
