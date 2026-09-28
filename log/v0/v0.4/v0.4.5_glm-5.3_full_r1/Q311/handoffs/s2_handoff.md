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


## What I'd tell my replacement
- Retired because: Three rounds in the correct host-evidence area produced no executable candidate or usable result, only repeated setup attempts and malformed/broad searches. The answer is not going to be reached by continuing this senior in the same Sysmon approach.
- Scope I owned: sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'symantec:ep:risk:file', 'o365:management:activity'] sources=['WinEventLog:Microsoft-Windows-Sysmon/Operational'] fields=['Image', 'TargetFilename', 'CommandLine', 'Hashes', 'ParentImage', 'User', 'file_name', 'file_path', 'Risk_Name', 'SourceFileName', 'UserId', 'ClientIP']
- Rounds worked: 3/5  (iterations: 18, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "Bruce Birthday Happy Hour Pics.lnk" | stats count by sourcetype, source | head 50
- index=botsv3 sourcetime="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 (ComputerName="BGIST-L" OR host="BGIST-L") earliest=1534763400 latest=1534764600 | stats count by _time, Image, CommandLine, ParentImage | head 50
- index=botsv3 sourcetype="symantec:ep:risk:file" "Bruce Birthday Happy Hour Pics.lnk" | stats count by host, Risk_Name, file_name, file_path | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Executed" "Happy Hour" | stats count by ComputerName, EventCode, Image, CommandLine | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "Bruce Birthday Happy Hour Pics.lnk" | stats count by ComputerName, EventCode, Image, CommandLine | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "Bruce" | stats count by ComputerName, EventCode, Image | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "Happy Hour" | stats count by ComputerName, EventCode, Image, CommandLine | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 (ComputerName="BGIST-L" OR host="BGIST-L") earliest="2018-08-20 09:50:00" latest="2018-08-20 10:10:00" | stats count by _time, Image, CommandLine, ParentImage | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 host="BGIST-L" earliest="08/20/2018:09:50:00" latest="08/20/2018:10:10:00" | stats count by _time, Image, CommandLine, ParentImage | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 | stats count by host | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 | stats count by host, ComputerName | head 50
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysvmon/Operational" EventCode=1 | stats count by host, ComputerName | head 50
