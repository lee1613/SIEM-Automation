# s1 - Q212 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=0_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran

### What it means
Intention: Settle premise p1/p2 by searching the five unexamined SEP feeds for any miner-related text, and simultaneously pull the earliest coin-miner events by Begin_Time to establish the event-order basis.


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['symantec:ep:risk:file', 'symantec:ep:security:file', 'symantec:ep:behavior:file', 'symantec:ep:traffic:file'] sources=[] fields=['signature_id', 'sig_id', 'rule_id', 'event_time', '_time', 'risk_name', 'virus', 'threat_name', 'computer_name', 'host', 'severity']
- Rounds worked: 3/3  (iterations: 12, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=symantec:ep:* "coinminer" OR "coin miner" OR "CoinMiner" | stats count by sourcetype, signature, signature_id, Host_Name, Computer_Name | sort - count
- index=botsv3 sourcetype=symantec:ep:security:file NOT CIDS_Signature_ID=* | stats count by signature, Host_Name, description | sort - count
- index=botsv3 sourcetype=symantec:ep:security:file | stats count by signature, signature_id, Host_Name | sort - count
- index=botsv3 sourcetype=symantec:ep:security:file | stats count, dc(signature_id) as distinct_sids, values(signature_id) as sids
