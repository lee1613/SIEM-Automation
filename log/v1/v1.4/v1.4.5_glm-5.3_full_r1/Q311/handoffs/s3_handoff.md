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


## What I'd tell my replacement
- Retired because: Three rounds in this broad direction produced no executable value and repeatedly ended at intended next steps. The only live lead left in the held evidence is the narrower BSTOLL-L Sysmon file-stream/hash path around the Birthday .lnk.
- Scope I owned: sourcetypes=['symantec:ep:risk:file', 'o365:management:activity', 'stream:smtp', 'ms:o365:reporting:messagetrace'] sources=[] fields=['file_name', 'file_path', 'Risk_Name', 'SourceFileName', 'Operation', 'UserId', 'Subject', 'Attachment*', 'content', '_raw']
- Rounds worked: 3/5  (iterations: 30, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "Bruce Birthday Happy Hour Pics" | stats count by sourcetype, source
- index=botsv3 sourcetype=stream:http src_ip=192.168.105.214 earliest=1534760000 latest=1534763000 | stats count by uri, status
- index=botsv3 sourcetype=stream:smtp "Birthday" | stats count by src_user, rcpt_to
- index=botsv3 sourcetype=WinEventLog source="WinEventLog:Microsoft-Windows-PowerShell/Host" ComputerName="BGIST-L.froth.ly" | stats count by EventCode
- index=botsv3 sourcetype=WinEventLog source="WinEventLog:Microsoft-Windows-PowerShell/Operational" ComputerName="BGIST-L.froth.ly" EventCode=40961 OR EventCode=40962 OR EventCode=53504 | rex field=_raw "Message=(?<msg>[^\r\n]{0,200})" | stats count by EventCode, msg
- index=botsv3 sourcetype=WinEventLog source="WinEventLog:Microsoft-Windows-PowerShell/Operational" ComputerName="BGIST-L.froth.ly" EventCode=4104 | rex field=_raw "(?i)(?<exe_token>[A-Za-z0-9_\-\.]{1,60}\.(exe|bat|cmd|ps1|vbs|dll|hta|jpe?g|png|zip|txt|lnk))" | stats count by exe_token
- index=botsv3 sourcetype=WinEventLog source="WinEventLog:Microsoft-Windows-PowerShell/Operational" ComputerName="BGIST-L.froth.ly" EventCode=4104 | rex field=_raw "(?i)(?<url_token>https?://[^\s\"'<>]{4,120})" | stats count by url_token
- index=botsv3 sourcetype=WinEventLog source="WinEventLog:Microsoft-Windows-PowerShell/Operational" ComputerName="BGIST-L.froth.ly" | rex field=_raw "Host Application = (?<host_app>[^\r\n]+)" | stats count by host_app
- index=botsv3 sourcetype=WinEventLog source="WinEventLog:Microsoft-Windows-PowerShell/Operational" ComputerName="BGIST-L.froth.ly" | stats count, min(_time) as first_time, max(_time) as last_time by EventCode
- index=botsv3 sourcetype=WinEventLog source="WinEventLog:Microsoft-Windows-PowerShell/Operational" | stats count by ComputerName
- index=botsv3 sourcetype=WinEventLog source="WinEventLog:Microsoft-Windows-PowerShell/Operational" | stats count by source
- index=botsv3 sourcetype=WinEventLog source="WinEventWLog:Microsoft-Windows-PowerShell/Operational" ComputerName="BGIST-L.froth.ly" | stats count
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational "Birthday" | stats count by Computer, EventCode
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational Computer="BSTOLL-L.froth.ly" EventCode=1 "Birthday" | stats count by CommandLine, ParentImage
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational Computer="BSTOLL-L.froth.ly" EventCode=11 "Birthday" | stats count by TargetFilename, Image
