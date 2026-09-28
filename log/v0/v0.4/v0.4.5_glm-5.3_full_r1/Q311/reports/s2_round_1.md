# s2 - Q311 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "Bruce Birthday Happy Hour Pics.lnk" | stats count by ComputerName, EventCode, Image, CommandLine | head 50
- index=botsv3 "Bruce Birthday Happy Hour Pics.lnk" | stats count by sourcetype, source | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "Happy Hour" | stats count by ComputerName, EventCode, Image, CommandLine | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Executed" "Happy Hour" | stats count by ComputerName, EventCode, Image, CommandLine | head 50
### What it means
Intention: Search Sysmon for the .lnk filename with a looser match (partial name) to see if the file appears in any Sysmon event on any host.
