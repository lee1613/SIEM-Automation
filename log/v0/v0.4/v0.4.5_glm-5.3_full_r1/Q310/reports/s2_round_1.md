# s2 - Q310 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=o365:management:activity "Birthday" | stats count min(_time) as first max(_time) as last values(Workload) as workloads values(Operation) as operations values(UserId) as users by SourceFileName
- index=botsv3 sourcetype=o365:management:activity SourceFileName="BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count values(Operation) as ops min(_time) as first max(_time) as last values(UserId) as users values(ClientIP) as ips by _time Operation UserId
- index=botsv3 sourcetype=symantec:ep:risk:file OR sourcetype=symantec:ep:security:file | stats count min(_time) as first max(_time) as last values(ComputerName) as hosts values(Risk_Action) as actions values(Risk_Name) as risks by file_name
- index=botsv3 sourcetype=symantec:ep:risk:file OR sourcetype=symantec:ep:security:file file_name="Bruce Birthday Happy Hour Pics.lnk" | stats count values(_time) as time values(ComputerName) as host values(User_Name) as user values(Risk_Name) as risk values(Risk_Action) as action values(Risk_Event_Description) as desc values(sourcetype) as st
### What it means
Intention: The detection is on BGIST-L (user BruceGist) at the OneDrive sync path, event time 09:58:20 UTC — right after the 17:57:33 upload. Now read a raw message-trace event of the later wave to confirm the phishing email carried the anonymous link to this file.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
