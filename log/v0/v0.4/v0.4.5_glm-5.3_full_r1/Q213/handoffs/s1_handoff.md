# s1 - Q213 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="symantec:ep:packet:file" "JSCoinminer" | stats count by signature, host, user
### What it means
Intention: Complete the coverage check on the traffic feed for the exact token JSCoinminer.


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['symantec:ep:security:file', 'symantec:ep:risk:file', 'symantec:ep:behavior:file', 'symantec:ep:security:file'] sources=[] fields=['signature', 'CIDS_Signature_ID', 'Host_Name', 'Begin_Time', '_time', 'severity', 'risk_name', 'virus', 'threat']
- Rounds worked: 3/3  (iterations: 22, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "coinminer" | stats count by sourcetype, source, signature, host
- index=botsv3 sourcetype="symantec:ep:*" "coinminer" | stats count by sourcetype, signature, host, user, dest
- index=botsv3 sourcetype="symantec:ep:agent:file" "coinminer" | stats count by signature, host, user, dest
- index=botsv3 sourcetype="symantec:ep:agent:file" "JSCoinminer" | stats count by signature, host, user
- index=botsv3 sourcetype="symantec:ep:agt_system:file" "JSCoinminer" | stats count by signature, host, user
- index=botsv3 sourcetype="symantec:ep:behavior:file" "coinminer" | stats count by signature, host, user, dest
- index=botsv3 sourcetype="symantec:ep:behavior:file" "JSCoinminer" | stats count by signature, host, user
- index=botsv3 sourcetype="symantec:ep:packet:file" "JSCoinminer" | stats count by signature, host, user
- index=botsv3 sourcetype="symantec:ep:risk:file" | stats count by Signature, ComputerName, Risk_Action, Severity | sort -count
- index=botsv3 sourcetype="symantec:ep:scm_system:file" "JSCoinminer" | stats count by signature, host,-proper
- index=botsv3 sourcetype="symantec:ep:security:file" "coinminer" | stats count by signature, host, user, dest
- index=botsv3 sourcetype="symantec:ep:security:file" "JSCoinminer" | stats count by host, user, signature
- index=botsv3 sourcetype="symantec:ep:security:file" "JSCoinminer" | stats count by signature, Computer_Name, Host_Name, dest, user, file_name, action
- index=botsv3 sourcetype="synantec:ep:behavior:file" "JSCoinminer" | stats count by signature, host, user
- index=bthreats sourcetype="symantec:ep:behavior:file" "coinminer" | stats count by signature, host, user, dest
