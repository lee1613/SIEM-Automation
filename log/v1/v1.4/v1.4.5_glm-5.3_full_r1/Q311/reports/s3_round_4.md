# s3 - Q311 - Round 4
_stamped by runner: rounds_remaining=1 novel_spl=8_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational Computer="BSTOLL-L.froth.ly" EventCode=1 "powershell -noP -sta -w 1 -enc" | rex field=CommandLine "powershell -noP -sta -w 1 -enc\s+(?<b64>\S+)" | eval decoded=replace(replace(b64," ",""),"\n","") | stats count by decoded
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational Computer="BSTOLL-L.froth.ly" EventCode=1 Image="C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" | stats count, values(_time) as times by ParentImage, ParentCommandLine
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Openational Computer="BSTOLL-L.froth.ly" EventCode=1 "powershell -noP -sta -w 1 -enc" | stats count, values(_time) as times by ParentImage
- index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational Computer="BSTOLL-L.froth.ly" EventCode=1 "powershell -noP -sta -w 1 -enc" | stats count, values(_time) as times by ParentImage
### What it means
Intention: Two powershell.exe -enc launches on BSTOLL-L: epoch 1534759188 (2018-08-20 09:06:28 UTC) and 1534764520 (2018-08-20 10:48:40 UTC). The 10:48:40 one is ~20 minutes after the 10:28:40 .lnk download. Let me verify the .lnk download times precisely to confirm adjacency.

Intention: Get exact times of the .lnk file creations on BSTOLL-L to confirm adjacency with the powershell launches.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_raw_events: {"keyword": "BRUCE BIRTHDAY", "limit": 10, "sourcetype": "XmlWinEventLog:Microsoft-Windows…` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
