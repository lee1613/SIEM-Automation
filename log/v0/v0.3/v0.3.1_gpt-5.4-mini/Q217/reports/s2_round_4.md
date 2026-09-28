# s2 - Q217 - Round 4
_stamped by runner: rounds_remaining=1 novel_spl=3_
**Scope:** sourcetype=stream:http,stream:tcp,XmlWinEventLog:Microsoft-Windows-Sysmon/Operational,WinEventLog,osquery:results | source=none | fields=host,User,Image,CommandLine,TargetFilename,process_name,path,url,uri,file_name
**Insight:** NOT_FOUND
**Candidate:** BTUN-L   **Confidence:** 66

## Prior rounds
- Confirmed endpoint/host telemetry exists and can expose process/file/network context.
- Identified BSTOLL-L as a prior Bud-related lead, but did not recover the first attachment.
- Shifted the investigation to browser/network telemetry for the Craft Brewer Conference thread.
- Established BTUN-L as the strongest employee endpoint tied to Brewertalk thread access.
- No verified attachment filename/content or visualization type has yet been recovered.

## This round
### What I ran
- `index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BTUN-L (Image="*chrome.exe" OR Image="*OUTLOOK.EXE" OR Image="*EXCEL.EXE" OR Image="*WINWORD.EXE") | stats ...` -> 4 hits for AzureAD\BillyTun (Outlook x2, Chrome x1, Excel x1).
- `index=botsv3 sourcetype="stream:http" host=BTUN-L site="www.brewertalk.com" | stats ...` -> many Brewertalk page requests from BTUN-L, including /showthread.php, /forumdisplay.php, /task.php, and /index.php.
- `index=botsv3 sourcetype="stream:http" host=BTUN-L (uri_path="*.xls*" OR ... ) | stats ...` -> 1 irrelevant Symantec update ZIP, not the attachment.
### What it means
BTUN-L is clearly the recipient-side endpoint interacting with the Brewertalk thread, and BillyTun used Outlook/Chrome/Excel there. But the first attachment itself still has not been exposed in the available telemetry, so the visualization type remains unconfirmed.

## Ruled out
- Direct BTUN-L attachment filename recovery from current Sysmon/WinEventLog - not surfaced.
- Brewertalk static web assets as the first attachment - those were page resources, not user attachment evidence.

## Open questions for SH
- Is there an attachment cache or browser-history artifact family available beyond the current scope if I need to identify the file name/title?
- Can SH confirm whether the first attachment would be expected in Outlook cache, browser download history, or an Office document open event?