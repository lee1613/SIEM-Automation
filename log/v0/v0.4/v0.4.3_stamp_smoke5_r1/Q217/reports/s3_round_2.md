# s3 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=2_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=osquery:results "image00" | stats count by source, name
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "image00" | stats count by EventCode, ComputerName
### What it means
Intention: Check Windows event logs for the attachment filenames — Outlook saving or opening the attachment would leave traces in WinEventLog.
