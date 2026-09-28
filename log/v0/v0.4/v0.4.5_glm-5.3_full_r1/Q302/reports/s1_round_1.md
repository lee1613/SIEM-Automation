# s1 - Q302 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=symantec:ep:security:file | stats count by signature, file_name, file_path
- index=botsv3 sourcetype=o365:management:activity (Workload=SharePoint OR Workload=OneDrive) SourceFileExtension="docm" OR SourceFileExtension="xlsm" OR SourceFileExtension="dotm" | stats count by SourceFileName, SourceFileExtension, UserId
- index=botsv3 "Brewing.xlsm" | stats count by sourcetype, source
- index=botsv3 sourcetype=o365:management:activity "Brewing.xlsm" | stats count by Operation, UserId, Site_Url
### What it means
Intention: The O365 activity feed doesn't have "Brewing.xlsm" as a string. Let me check the raw events from the O365 activity feed to see how the file is referenced, and also search other feeds for macro-enabled files.
