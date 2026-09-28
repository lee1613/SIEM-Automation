# s1 - Q213 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=7_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="synantec:ep:behavior:file" "JSCoinminer" | stats count by signature, host, user
- index=botsv3 sourcetype="symantec:ep:behavior:file" "JSCoinminer" | stats count by signature, host, user
- index=botsv3 sourcetype="symantec:ep:agt_system:file" "JSCoinminer" | stats count by signature, host, user
- index=botsv3 sourcetype="symantec:ep:scm_system:file" "JSCoinminer" | stats count by signature, host,-proper
### What it means
Intention: Continue the coverage check on the packet feed.
