# s2 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype IN (symantec:ep:agent:file,symantec:ep:behavior:file,symantec:ep:packet:file,symantec:ep:risk:file,symantec:ep:security:file) "taedonggang" | stats count by sourcetype
### What it means
Intention: Symantec feeds are empty for the term; check osquery:results and WinHostMon for "taedonggang" as a file path or process name.
