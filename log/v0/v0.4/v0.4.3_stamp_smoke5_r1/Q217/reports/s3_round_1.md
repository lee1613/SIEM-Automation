# s3 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 "image001.jpg" | stats count by sourcetype, source
- index=botsv3 sourcetype=stream:http "image001.jpg" | stats count by source, http_method, status
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "image001.jpg" | stats count by EventCode, ComputerName
- index=botsv3 sourcetype=WinEventLog "image001.jpg" | stats count by source, EventCode
### What it means
Intention: Check the osquery results feed for file events naming the attachment — osquery monitors file changes on endpoints and could show a saved copy of image001.jpg.
