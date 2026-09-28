# Q317 — SH <-> Senior conversation

### 22:17:15 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'o365:management:activity', 'symantec:ep:risk:file'] sources=['WinEventLog:Microsoft-Windows-Sysmon/Operational'] fields=['EventCode', 'TargetFilename', 'Image', 'ProcessGuid', 'CommandLine', 'host', 'User', 'CreationTime', 'SourceFileName', 'Computer_Name', 'file_name']
**Technique:** senior
**Reason:** The question is about an uploaded executable on a compromised endpoint, not a cloud control-plane action. Sysmon file-creation/process telemetry is the direct place to order executable arrivals on the endpoint, while O365/Symantec can help anchor the compromised account or corroborate file identity if needed.

Determine which endpoint belongs to the compromised domain admin account, then identify the first executable uploaded to that endpoint system and return its filename exactly as recorded. Start with FYODOR-L as the strongest candidate endpoint from prior case knowledge, but verify from host/file evidence whether the first uploaded executable on that compromised endpoint is visible in Sysmon or adjacent file telemetry.

### 22:20:29 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> 
_full: reports/s1_round_1.md_

### 22:20:41 - SH -> s1   [COMMAND]
**continue** — FYODOR-L remains the strongest endpoint candidate from prior case knowledge, and Sysmon EventCode 11 is the direct artifact for ordering executable arrivals on that host. The round failed only because it ended before returning the ordered rows.

On FYODOR-L, read the complete EventCode 11 file-creation set in time order and identify which created files are executables. Determine the earliest executable created on that endpoint, and if multiple hosts or account interpretations become plausible, say exactly what evidence would distinguish the compromised domain admin endpoint from rivals before naming a file.

### 22:25:27 - s1 -> SH   [REPORT - round 2 - FOUND]
> Chain: FYODOR-L (host of AzureAD\FyodorMalteskesko, the account SH names as the compromised domain admin) shows an obfuscated PowerShell downloader (PID 6360, -NoP -NonI -W Hidden -enc, parent reads payload from registry Run key HKCU:\Software\Microsoft\Windows Update) that writes C:\Windows\Temp\hd
_full: reports/s1_round_2.md_

### 22:25:36 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] The strongest current candidate is hdoor.exe, as the earliest executable created on FYODOR-L at 2018-08-20 18:42:49 +08 by the malicious PowerShell downloader.
[q2] What would settle the question is direct evidence that FYODOR-L is the compromised endpoint used by the domain admin account, or a rival endpoint showing an earlier uploaded executable for that same account.

**continue** — The executable-ordering work on FYODOR-L is useful and likely right, but the question binds to the compromised endpoint of the domain admin account, not merely the easiest host with tooling. Before answering, the case needs the endpoint-to-account linkage or a ruled-out rival endpoint.
**New scope:** sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'ms:aad:audit', 'ms:aad:signin', 'WinEventLog', 'WinHostMon'] sources=[] fields=['User', 'ComputerName', 'host', 'TargetFilename', 'ProcessId', 'actor.userPrincipalName', 'targets{}.userPrincipalName', 'userPrincipalName']

Establish whether FYODOR-L is the compromised endpoint of the domain admin account by using account-bearing endpoint telemetry already in scope or adjacent host evidence, and then confirm the earliest executable creation on that endpoint. If FYODOR-L is confirmed, show the complete ordered executable-creation result for that host and why hdoor.exe is first; if another endpoint tied to that account exists, compare its earliest uploaded executable instead.

### 22:27:38 - s1 -> SH   [REPORT - round 3 - FOUND]
> Answer: hdoor.exe (C:\Windows\Temp\hdoor.exe), the first executable created on FYODOR-L, the compromised endpoint of the privileged account AzureAD\FyodorMalteskesko. Chain: (1) endpoint selection — FYODOR-L is the only host in WinEventLog:Security with account/group-management events (4720 account 
_full: reports/s1_round_3.md_

### 22:27:45 - SH -> s1   [CLARIFY]
SH's answers to your open questions:
[q3] What would fully settle the wording is a literal role/group artifact naming the compromised account as domain admin, but the held evidence already shows FYODOR-L is the only endpoint where AzureAD\FyodorMalteskesko performs high-privilege account-management actions (create/enable/reset/add-to-group) during compromise. Clarify whether any rival endpoint or rival privileged account remains in the held results.

**suspect**
1. From the evidence you already hold, is FYODOR-L the only endpoint in the checked security/sysmon results where AzureAD\FyodorMalteskesko performs privileged account-management actions during the compromise, with no rival endpoint tied to that same account left unresolved?
2. From the evidence you already hold, does any completed result literally identify another executable created on FYODOR-L earlier than hdoor.exe, or is the ordered executable set on that host complete with hdoor.exe first?
3. Does your candidate hdoor.exe depend at all on the partial 50-of-61 Security EventCode inventory, or is the endpoint/account linkage and executable ordering supported by complete targeted results already read?

### 22:27:59 - s1 -> SH   [CLARIFY REPLY]
**1. Yes — FYODOR-L is the only such endpoint, and no rival tied to that account is unresolved.** The targeted queries were complete, not partial: `EventCode=4728` returned exactly 1 event (FYODOR-L, 18:08:17, subject AzureAD\FyodorMalteskesko adding FYODOR-L\svcvnc to a global group), and the `4720 OR 4722 OR 4724 OR 4732 OR 4738` query returned 6 of 6 rows, all on FYODOR-L (18:08:17–18:08:35). Both 4732 events in the dataset are accounted for on FYODOR-L. No other host in WinEventLog:Security has any account-management event, so no rival endpoint for this account exists on that axis. The one thing I did not enumerate is every host where FyodorMalteskesko appears as a process User in Sysmon generally — but that is not the account-management axis the question asks about.

**2. No earlier executable exists in any completed result; the ordered set is complete with hdoor.exe first.** The FYODOR-L EventCode 11 query returned 18 of 18 rows (complete, all read): the only executables are hdoor.exe (1534761769), iexepler.exe and unziped\lsof-master\powershell.exe (both 1534762061), and DismHost.exe (1534764864). The all-host .exe query (39 of 39, complete) shows the same FYODOR-L ordering.

### 22:28:06 - runner   [NOTE]
TURN REJECTED:
- [F2] ANSWER is blocked: 6 load-bearing premise(s) it rests on are still UNVERIFIED - COMMAND s1 to settle them, or RETIRE it if it is circling the same lead and SPAWN an alternative senior on a different area, constrained to where it may have overlooked: p1 "Executable uploads to the compromised endpoint appear as Sysmon EventCode 11 (Fi" | p2 "FYODOR-L is the compromised endpoint of the privileged (domain admin) account: i" | p3 "hdoor.exe is the first executable created on FYODOR-L: its creation time (epoch " | p4 "Coverage: On the compromised endpoint of the privileged account in this dataset," | p5 "Selection: The first executable uploaded to that endpoint is hdoor.exe, because " | p6 "The question's 'uploaded' act is satisfied here by host-side arrival on the endp" → re-read F2.

### 22:28:14 - SH -> s1   [COMMAND]
**continue** — The entity and candidate are already isolated: FYODOR-L is the only held endpoint with FyodorMalteskesko's privileged account-management activity, and hdoor.exe is the earliest executable creation there. What blocks submission is ledger state, so the next round should do nothing except settle the existing premises from exact Security and Sysmon output.
**New scope:** sourcetypes=[] sources=[] fields=['EventCode', 'TargetFilename', 'Image', 'ProcessId', 'User', 'ComputerName', '_time', 'CommandLine']

Settle premises p1 through p6 directly from exact word-for-word output. For p1 and p4, quote the complete FYODOR-L Sysmon EventCode 11 rows that show file-creation evidence for executables on that endpoint and the complete all-host executable-creation comparison if you use it to rule out rival endpoint/file readings. For p2, quote the complete WinEventLog:Security rows showing AzureAD\FyodorMalteskesko's privileged account-management activity on FYODOR-L (the 4728 event and the 4720/4722/4724/4732/4738 set) and enough host context to show no rival endpoint for that account exists in the held results. For p3 and p5, quote the ordered FYODOR-L executable-creation rows showing hdoor.exe at epoch 1534761769 before iexeplorer.exe, unziped\lsof-master\powershell.exe, and DismHost.exe. For p6, quote the file-creation row and any paired process row needed to show why the question's 'uploaded' act is being read here as endpoint file arrival/creation rather than a separate mail or web upload action. Then restate the executable name literally if unchanged.

### 22:29:28 - s1 -> SH   [REPORT - round 4 - FOUND]
> Executable name unchanged: hdoor.exe (C:\Windows\Temp\hdoor.exe), first executable created on FYODOR-L at epoch 1534761769 (2018-08-20 18:42:49 +08) by obfuscated PowerShell downloader PID 6360 running as AzureAD\FyodorMalteskesko. All six premises settled this round with complete, fully-read result
_full: reports/s1_round_4.md_

### 22:29:37 - SH -> s1   [RETIRE]
s1 identified a stable candidate and closed the EventCode 15 corner, but after four rounds it is still narrating premise settlement instead of returning the exact quoted Security and Sysmon rows needed to verify p1–p6. Another round on the same senior is likely to circle the same proof gap.

### 22:29:37 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 22:29:37 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['WinEventLog', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'] sources=['WinEventLog:Security', 'WinEventLog:Microsoft-Windows-Sysmon/Operational'] fields=['EventCode', 'ComputerName', 'SubjectUserName', 'MemberName', 'TargetFilename', 'Image', 'ProcessId', 'User', 'CommandLine', '_time']
**Technique:** senior
**Reason:** A competing suspicion is that the answer can be made runner-acceptable by rebuilding the chain from Security-first evidence, using complete Windows Security rows to bind the compromised privileged account to the endpoint before moving to ordered Sysmon executable arrivals. This differs from s1’s stalled Sysmon-first narration and uses the same feed family through a different field-first direction.

Independently determine which executable was first uploaded to the compromised endpoint of the privileged account. First prove which endpoint belongs to the compromised privileged account from Windows Security account-management events, then enumerate executable file creations on that same endpoint in Sysmon and return the earliest executable filename exactly as recorded.

### 22:37:41 - s2 -> SH   [REPORT - round 1 - NOT_FOUND]
> 
_full: reports/s2_round_1.md_

### 22:37:41 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

### 22:37:41 - runner   [NOTE]
s2 api_failed — retired, spawn slot refunded

### 22:37:41 - runner   [NOTE]
s2 api_failed and no operator reachable — skipping; slot already refunded, decision request at C:\dev\SIEM-Automation\log\v1\v1.4/v1.4.5_glm-5.3_full_r1\decision_request.json

### 22:37:47 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['WinEventLog', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'] sources=['WinEventLog:Security', 'WinEventLog:Microsoft-Windows-Sysmon/Operational'] fields=['EventCode', 'ComputerName', 'TargetFilename', 'Image', 'ProcessId', 'User', 'CommandLine', '_time']
**Technique:** senior
**Reason:** The retired senior was lost to transport failure, not disproved on scope. The unresolved blocker is still exact proof for endpoint selection and first executable ordering, and the Security-first path remains the best way to settle it.

Independently determine which executable was first uploaded to the compromised endpoint of the privileged account. First prove which endpoint belongs to the compromised privileged account from Windows Security account-management events, then enumerate executable file creations on that same endpoint in Sysmon and return the earliest executable filename exactly as recorded.

### 22:45:51 - s3 -> SH   [REPORT - round 1 - NOT_FOUND]
> 
_full: reports/s3_round_1.md_

### 22:45:51 - s3 -> SH   [HANDOFF]
_full: handoffs/s3_handoff.md_

### 22:45:51 - runner   [NOTE]
s3 api_failed — retired, spawn slot refunded

### 22:45:51 - runner   [NOTE]
s3 api_failed again with no operator reachable — pausing; resume with --run-name

