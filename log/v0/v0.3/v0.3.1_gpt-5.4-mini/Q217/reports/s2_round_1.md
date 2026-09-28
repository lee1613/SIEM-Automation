# s2 - Q217 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=2_
**Scope:** sourcetype=WinEventLog | source=WinEventLog:Security,WinEventLog:Application,WinEventLog:System | fields=EventCode,TaskCategory,Image,CommandLine,host,User,TargetFilename
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 22

## Prior rounds
- Identified endpoint telemetry feeds present in BOTSv3; Windows event logs and Sysmon are available.
- Confirmed WinEventLog contains Security/Application/System with process-creation and filtering-platform events.
- Confirmed Sysmon telemetry exists with EventCode 1/3/11 and fields suitable for process/file/network activity.
- Found BudStoll on BSTOLL-L launching Chrome, which is a plausible recipient-side context for the attachment.
- No file-creation evidence was recovered from BSTOLL-L Sysmon EventCode=11 in the query run.

## This round
### What I ran
- `index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 Image IN (...) | stats count by host, User, Image, CommandLine | sort - count` -> 5 relevant results for BSTOLL-L Chrome under AzureAD\BudStoll, plus unrelated FYODOR-L malicious activity.
- `index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11 host=BSTOLL-L | stats count by TargetFilename, Image, User | sort - count` -> 0 results.
### What it means
The only credible recipient-side lead is BudStoll on BSTOLL-L using Chrome, but I did not recover attachment filename, save/open evidence, or the visualization type. The zero EventCode=11 hits mean this exact file-creation path did not confirm the attachment in the queried scope.

## Ruled out
- FYODOR-L process telemetry - unrelated malicious execution, not Bud's attachment trail.
- Sysmon file-create on BSTOLL-L - no hits for the queried form.

## Open questions for SH
- Which endpoint-side artifact family should I prioritize next for BudStoll/BSTOLL-L: browser download history, document-open telemetry, or alternate host telemetry?
- Is there a known recipient host beyond BSTOLL-L associated with Bud's message thread?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
