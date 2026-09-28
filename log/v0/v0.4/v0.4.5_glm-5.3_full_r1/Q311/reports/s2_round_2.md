# s2 - Q311 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "Bruce" | stats count by ComputerName, EventCode, Image | head 50
- index=botsv3 sourcetype="symantec:ep:risk:file" "Bruce Birthday Happy Hour Pics.lnk" | stats count by host, Risk_Name, file_name, file_path | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 (ComputerName="BGIST-L" OR host="BGIST-L") earliest="2018-08-20 09:50:00" latest="2018-08-20 10:10:00" | stats count by _time, Image, CommandLine, ParentImage | head 50
- index=botsv3 sourcetime="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 (ComputerName="BGIST-L" OR host="BGIST-L") earliest=1534763400 latest=1534764600 | stats count by _time, Image, CommandLine, ParentImage | head 50
### What it means
Intention: Retry the Sysmon process-creation search on BGHost-L around the detection time using correct Splunk time syntax.
