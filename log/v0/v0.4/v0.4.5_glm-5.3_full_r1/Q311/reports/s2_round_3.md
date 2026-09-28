# s2 - Q311 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 host="BGIST-L" earliest="08/20/2018:09:50:00" latest="08/20/2018:10:10:00" | stats count by _time, Image, CommandLine, ParentImage | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 | stats count by host, ComputerName | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysvmon/Operational" EventCode=1 | stats count by host, ComputerName | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 | stats count by host | head 50
### What it means
Intention: The host field works. Now search Sysmon process-creation events on BGIST-L around the Symantec detection time (2018-08-20 09:58:20) with correct time syntax.
