# s3 - Q311 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "Birthday" | stats count by Computer, EventCode
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational Computer="BSTOLL-L.froth.ly" EventCode=11 "Birthday" | stats count by TargetFilename, Image
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational Computer="BSTOLL-L.froth.ly" EventCode=1 "Birthday" | stats count by CommandLine, ParentImage
- index=botsv3 sourcetype=stream:smtp "Birthday" | stats count by src_user, rcpt_to
### What it means
Intention: No SMTP trail. Let me read BSTOLL-L's EventCode 15 (file stream hash) events mentioning Birthday — these hash the .lnk's alternate streams, and the Zone.Identifier content may reveal the download URL or payload name.

Intention: Read BSTOLL-L's file-stream-hash events for the Birthday .lnk.
