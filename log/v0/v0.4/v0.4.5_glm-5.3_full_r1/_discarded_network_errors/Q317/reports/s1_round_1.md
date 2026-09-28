# s1 - Q317 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=2_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host="FYODOR-L" | stats count by EventCode
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host="FYODOR-L" EventCode=11 | table _time TargetFilename Image User | sort _time
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host="FYODOR-L" EventCode=11 | table _time TargetFilename Image User | sort _time
### What it means
Intention: List all EventCode 11 (file creation) events on FYODOR-L in time order — 21 events is small enough to read in full — to identify the first executable file created/uploaded on that endpoint.
