# Q214 — SH <-> Senior conversation

### 14:23:34 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['symantec:ep:security:file', 'symantec:ep:risk:file', 'symantec:ep:behavior:file', 'symantec:ep:agent:file', 'symantec:ep:agt_system:file', 'symantec:ep:packet:file', 'symantec:ep:traffic:file', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon'] sources=- fields=['Host_Name', 'Computer_Name', 'signature', 'CIDS_Signature_ID', 'action', 'Risk_Action', 'Image', 'EventCode', 'user', 'file_name', 'process', 'command_line']
**Technique:** senior
**Reason:** The question is about an endpoint that defeated the cryptocurrency threat, so the evidence is most likely in Symantec Endpoint Protection detections and remediation actions, with endpoint telemetry only as corroboration. Prior questions make BSTOLL-L and BTUN-L the key rival hosts: one actually mined, the other had SEP coin-miner detections.

Determine which single Frothly endpoint shows evidence of defeating the cryptocurrency threat. Test the carried-forward candidates BSTOLL-L and BTUN-L first, and establish what records indicate defeat of the threat such as SEP blocking, cleaning, quarantining, termination, or other successful prevention/remediation evidence. Return the short hostname of the only endpoint that fits.

### 14:26:35 - s1 -> SH   [REPORT - round 1 - FOUND]
> BTUN-L evidence detail: 46 SEP security events, event times 2018-08-18 20:51 through 2018-08-20 (indexed Aug 20), user BillyTun, local IP 192.168.3.130, remote 54.67.127.227:80 (brewertalk.com pages: /, index.php, forumdisplay.php?fid=7), blocked applications MICROSOFTEDGECP.EXE (38) and CHROME.EXE 
_full: reports/s1_round_1.md_

### 14:26:42 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] At present, the clearest defeat evidence is SEP blocking on BTUN-L: blocked JSCoinminer detections with attack-blocked descriptions. But you still need to confirm whether other feeds carry rival defeat evidence for the cryptocurrency threat on another endpoint.
[q2] BSTOLL-L remains the strongest rival host because prior questions showed actual Coinhive mining there; to rule it out for this question, test whether any security or endpoint feed records successful blocking, cleaning, or remediation of the cryptocurrency threat on BSTOLL-L rather than just execution.

**continue** — The senior found direct prevention evidence on BTUN-L in the correct SEP feed, but the question asks for the only endpoint showing defeat of the cryptocurrency threat, so rival remediation evidence on BSTOLL-L or in adjacent SEP feeds must be ruled out before answering.
**New scope:** sourcetypes=['symantec:ep:security:file', 'symantec:ep:risk:file', 'symantec:ep:behavior:file', 'symantec:ep:agent:file', 'symantec:ep:traffic:file', 'symantec:ep:packet:file', 'symantec:ep:agt_system:file', 'symantec:ep:scm_system:file'] sources=[] fields=['Host_Name', 'signature', 'action', 'Event_Description', 'user', 'src', 'Intrusion_URL', 'Risk name', 'Requested action', 'Actual action', 'Secondary action']

Settle both premises from endpoint-security evidence. First, verify coverage by checking whether cryptocurrency-threat defeat evidence appears anywhere outside symantec:ep:security:file for the relevant hosts, especially BSTOLL-L and BTUN-L, in SEP-related feeds that could record blocking, cleaning, quarantine, or related remediation. Second, verify selection by showing that BTUN-L has JSCoinminer detections with blocked/attack-blocked outcomes and that no other endpoint has equivalent cryptocurrency-threat defeat evidence. Then restate the short hostname literally if unchanged.

### 14:28:25 - s1 -> SH   [REPORT - round 2 - FOUND]
> Answer unchanged from round 1: BTUN-L. This round closed the SEP-scope gaps: (1) all 46 JSCoinminer detections are on BTUN-L with action=blocked (signature-level query, 2 rows, read in full); (2) literal "JSCoinminer" appears in no SEP feed other than symantec:ep:security:file; (3) the risk feed hol
_full: reports/s1_round_2.md_

### 14:28:35 - SH -> s1   [CLARIFY]
**suspect**
1. From the evidence you already hold, is there any endpoint other than BTUN-L with a SEP record showing cryptocurrency-threat prevention or remediation (blocked, cleaned, quarantined, or equivalent), or is BTUN-L the only one?
2. Does your held evidence already show that BSTOLL-L has no SEP defeat record for the cryptocurrency threat and only actual mining evidence from prior questions, with no unresolved rival host left inside SEP scope?
3. Does any conclusion you drew about symantec:ep:behavior:file depend on rows beyond the first 50 shown in the partial-results warning, or is your BTUN-L selection fully supported without relying on that truncated result?

### 14:28:40 - s1 -> SH   [CLARIFY REPLY]
1. **BTUN-L is the only one.** Inside SEP scope, the only cryptocurrency-threat records are the 46 "Web Attack: JSCoinminer Download 6/8" events in symantec:ep:security:file, and the signature-level query (`| stats count by Host_Name, action, signature`) returned exactly 2 rows, both Host_Name=BTUN-L, action=blocked. The risk feed holds exactly one event total (BGIST-L, Backdoor.PsEmpire, cleaned/quarantined — a backdoor, not crypto), and the behavior feed is entirely application-control AC-rule policy blocks. No other endpoint has a SEP record showing crypto-threat prevention or remediation.

2. **Yes, with one caveat.** The cross-feed search for "BSTOLL-L" across all 8 SEP sourcetypes returned 0 events, so BSTOLL-L has no SEP records of any kind — no blocking, cleaning, or quarantine — and prior questions put actual Coinhive mining there (infection, not defeat). No unresolved rival host remains inside SEP scope. The caveat: endpoint telemetry outside SEP (WinEventLog, osquery:results, WinHostMon, PerfmonMk:Process) was never checked for miner-termination or manual-remediation evidence on BSTOLL-L or any other host — that branch of coverage is still unsearched, though it is outsid

### 14:28:45 - SH -> s1   [ANSWER]
**BTUN-L** (hostname) from s1

s1 established that the only SEP cryptocurrency-threat records are 46 'Web Attack: JSCoinminer Download 6/8' events in symantec:ep:security:file, and the signature-level result returned exactly two rows, both Host_Name=BTUN-L with action=blocked. Clarification then established that no other endpoint has any SEP record of cryptocurrency-threat prevention or remediation, that BSTOLL-L has zero SEP records of any kind, and that the answer does not depend on the truncated behavior-feed listing.

**Premises it rests on:** p1, p2

### 14:28:45 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

