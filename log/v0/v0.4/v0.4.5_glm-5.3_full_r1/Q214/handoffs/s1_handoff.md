# s1 - Q214 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=9_
**Scope:** sourcetypes=symantec:ep:security:file, symantec:ep:risk:file, symantec:ep:behavior:file, symantec:ep:agent:file, symantec:ep:traffic:file, symantec:ep:packet:file, symantec:ep:agt_system:file, symantec:ep:scm_system:file | fields=Host_Name, signature, action, Event_Description, Risk name, Actual/Requested/Secondary action
**Insight:** FOUND
**Candidate:** BTUN-L   **Confidence:** 90

## Prior rounds
- R1: fieldsummary of symantec:ep:security:file found 46 "Web Attack: JSCoinminer Download 6/8" events, action=blocked, Host_Name distinct_count=1 (BTUN-L); risk feed's only field-extracted event was BGIST-L Backdoor.PsEmpire. Submitted BTUN-L at confidence 85.

## This round
### What I ran
- signature="Web Attack: JSCoinminer Download 6/8" | stats count by Host_Name, action, signature -> 2 rows, both BTUN-L, action=blocked, 23+23=46.
- "JSCoinminer" across all 8 SEP sourcetypes | stats count by sourcetype -> 1 row: symantec:ep:security:file, 46. Zero in the other seven feeds.
- Risk feed | stats count by "Computer name","Risk name","Actual action","Requested action","Secondary action" -> exactly 1 row: BGIST-L, Backdoor.PsEmpire, Cleaned by deletion/Quarantined.
- Behavior feed fieldsummary + signature listing -> 2192 events, 5 hosts (JWORTOS-L, BTUN-L, MKRAEUS-L, BGIST-L, PCERF-L), all application-control AC-rule blocks (Block scripts, Security/Sharing tabs, system files, hosts file) — nothing crypto.
- "BSTOLL-L" across all 8 SEP feeds | stats count by sourcetype -> 0 events.

### What it means
BTUN-L's own records positively show the act the question names: 46 JSCoinminer download attacks blocked by SEP host IPS (action=blocked, "attack blocked. Traffic has been blocked"), user BillyTun browsing brewertalk.com. Exclusivity is now verified inside the SEP scope: the JSCoinminer signature exists only in the security feed and only on BTUN-L; the risk feed's single event is a non-crypto backdoor on BGIST-L; the behavior feed is policy noise; and the rival BSTOLL-L has zero records in any SEP feed, so it cannot show SEP blocking/cleaning/quarantining of the cryptocurrency threat — consistent with prior findings that the miner actually executed there (infection, not defeat). Both carried-forward premises are settled VERIFIED.

## Ruled out
- BSTOLL-L — 0 events across all 8 SEP feeds; no SEP prevention/remediation records exist for it.
- BGIST-L — only SEP risk event is Backdoor.PsEmpire (cleaned/quarantined), not cryptocurrency.
- symantec:ep:behavior:file as crypto-defeat evidence — all 2192 events are AC-rule policy blocks, no coinminer.
- Other SEP feeds (agent, agt_system, packet, scm_system, traffic) — no "JSCoinminer" token, no host/action fields carrying remediation.

Gap: endpoint telemetry (WinEventLog/osquery/WinHostMon/PerfmonMk:Process) outside this round's SEP scope remains unchecked for miner-termination evidence on other hosts.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="symantec:ep:behavior:file" | stats count by signature, Host_Name` (50 of 61 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['symantec:ep:security:file', 'symantec:ep:risk:file', 'symantec:ep:behavior:file', 'symantec:ep:agent:file', 'symantec:ep:agt_system:file', 'symantec:ep:packet:file', 'symantec:ep:traffic:file', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon'] sources=[] fields=['Host_Name', 'Computer_Name', 'signature', 'CIDS_Signature_ID', 'action', 'Risk_Action', 'Image', 'EventCode', 'user', 'file_name', 'process', 'command_line']
- Rounds worked: 2/3  (iterations: 22, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 (coinminer OR "coin miner" OR monero OR xmrig OR cryptonight OR minerd) | stats count by sourcetype
- index=botsv3 sourcetype IN ("symantec:ep:behavior:file","symantec:ep:agent:file","symantec:ep:agt_system:file","symantec:ep:scm_system:file","symantec:ep:traffic:file","symantec:ep:packet:file") | stats count by sourcetype, Host_Name, Computer_Name
- index=botsv3 sourcetype IN ("symantec:ep:risk:file","symantec:ep:agent:file","symantec:ep:agt_system:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:scm_system:file","symantec:ep:security:file","symantec:ep:traffic:file") "BSTOLL-L" | stats count by sourcetype
- index=botsv3 sourcetype IN ("symantec:ep:risk:file","symantec:ep:agent:file","symantec:ep:agt_system:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:scm_system:file","symantec:ep:security:file","symantec:ep:traffic:file") "JSCoinminer" | stats count by sourcetype
- index=botsv3 sourcetype IN ("symantec:ep:risk:file","symantec:ep:agent:file","symantec:ep:agt_system:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:scm_system:file","symantec:ep:security:file","symantec:ep:traffic:file") "JSCoinminer" | stats count by sourcetype, Host_Name, Computer_Name, action
- index=botsv3 sourcetype IN ("symantec:ep:risk:file","symantec:ep:agent:file","symantec:ep:agt_system:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:scm_system:file","symantec:ep:security:file","symantec:ep:traffic:file") (coin OR miner OR monero OR cryptocurrency OR xmrig) | stats count by sourcetype
- index=botsv3 sourcetype="symantec:ep:*" (coin OR miner OR monero OR cryptocurrency OR xmrig) | stats count by sourcetype
- index=botsv3 sourcetype="symantec:ep:behavior:file" | stats count by signature, Host_Name
- index=botsv3 sourcetype="symantec:ep:risk:file" | stats count by "Computer name", "Risk name", "Actual action", "Requested action", "Secondary action"
- index=botsv3 sourcetype="symantec:ep:risk:file" | stats count by Computer_Name, Risk_Name, Actual_Action, Requested_Action, Secondary_Action
- index=botsv3 sourcetype="symantec:ep:security:file" "JSCoinminer" | stats count
- index=botsv3 sourcetype="symantec:ep:security:file" signature="Web Attack: JSCoinminer Download 6" OR signature="Web Attack: JSCoinminer Download 8" | stats count by Host_Name, action, signature
