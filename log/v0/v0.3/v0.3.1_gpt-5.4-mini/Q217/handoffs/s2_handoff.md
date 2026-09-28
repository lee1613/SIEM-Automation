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

## What I'd tell my replacement
- Retired because: This senior narrowed the strongest endpoint lead to BTUN-L and established BillyTun used Outlook/Chrome/Excel while accessing the Brewertalk thread, but after multiple rounds it still could not recover the first attachment, filename, or visualization type. Handoff: carry forward candidate thread `Craft Brewer Conference`, Bud address `btun@froth.ly`, and endpoint lead BTUN-L / AzureAD\BillyTun as the most likely place where recipient-side attachment handling occurred.
- Scope I owned: sourcetypes=['WinEventLog', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon', 'osquery:results', 'stream:http', 'access_combined'] sources=[] fields=['user', 'dest', 'file_name', 'process', 'CommandLine', 'Image', 'TargetFilename', 'ObjectName', 'url', 'uri_path', 'Subject', 'attachment', 'filename']
- Rounds worked: 4/5  (iterations: 29, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype IN ("stream:http","XmlWinEventLog:Microsoft-Windows-Sysmon/Operational") host=BTUN-L (uri_path="*download*" OR uri_path="*attachment*" OR uri_path="*task.php*" OR uri_path="*showthread.php*" OR Image="*chrome.exe" OR CommandLine="*chrome.exe*") | stats count by sourcetype, host, dest, site, uri_path, url, Image, CommandLine, User, http_user_agent, file_name | sort - count
- index=botsv3 sourcetype IN ("XmlWinEventLog:Microsoft-Windows-Sysmon/Operational","WinEventLog","osquery:results") host=BTUN-L User="AzureAD\\BillyTun" (TargetFilename=* OR CommandLine=* OR Image=* ) | stats count by sourcetype, host, User, Image, CommandLine, TargetFilename, process_name, path, file_name | sort - count
- index=botsv3 sourcetype IN ("XmlWinEventLog:Microsoft-Windows-Sysmon/Operational","WinEventLog","osquery:results","stream:http") "Craft Brewer Conference" | stats count by sourcetype, source, host, User, Image, CommandLine, TargetFilename, process_name, path, url, uri, file_name | sort - count
- index=botsv3 sourcetype="osquery:results" host=BSTOLL-L (columns.path=*download* OR columns.path=*Downloads* OR columns.path=*Document* OR columns.path=*Chrome* OR columns.path=*Office*) | stats count by host, user, columns.path, columns.name, columns.type | sort - count
- index=botsv3 sourcetype="osquery:results" host=BSTOLL-L (columns.path=download* OR columns.path=Downloads* OR columns.path=Document* OR columns.path=Chrome* OR columns.path=Office*) | stats count by host, user, columns.path, columns.name, columns.type | sort - count
- index=botsv3 sourcetype="stream:http" host=BSTOLL-L (site="www.brewertalk.com" OR uri_path="*suitecrm*" OR uri_path="*attachment*" OR uri_path="*download*" OR uri_path="*upload*" OR uri_path="*file*") | stats count by host, dest, site, uri_path, url, http_user_agent | sort - count
- index=botsv3 sourcetype="stream:http" host=BSTOLL-L site="www.brewertalk.com" (uri_path="/showthread.php" OR uri_path="/task.php" OR uri_path="/forumdisplay.php") | stats count by host, dest, site, uri_path, url, http_user_agent, bytes_in, bytes_out | sort - count
- index=botsv3 sourcetype="stream:http" host=BTUN-L (uri_path="*.xls*" OR uri_path="*.xlsx" OR uri_path="*.zip" OR uri_path="*.doc*" OR uri_path="*.pdf" OR uri_path="*.ppt*" OR uri_path="*.csv") | stats count by host, dest, site, uri_path, url, http_user_agent | sort - count
- index=botsv3 sourcetype="stream:http" host=BTUN-L site="www.brewertalk.com" | stats count by host, dest, uri_path, url, http_user_agent | sort - count
- index=botsv3 sourcetype="stream:http" site="www.brewertalk.com" (uri_path="/showthread.php" OR uri_path="/task.php" OR uri_path="/forumdisplay.php") | stats count by host, dest, uri_path, http_user_agent | sort - count
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 Image IN ("C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe","C:\\Program Files\\Mozilla Firefox\\firefox.exe","C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE","C:\\Program Files (x86)\\Microsoft Office\\Office16\\WINWORD.EXE","C:\\Program Files\\Microsoft Office\\Office16\\EXCEL.EXE","C:\\Windows\\Temp\\unziped\\lsof-master\\iexeplorer.exe") | stats count by host, User, Image, CommandLine | sort - count
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11 host=BSTOLL-L | stats count by TargetFilename, Image, User | sort - count
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BTUN-L (Image="*chrome.exe" OR Image="*OUTLOOK.EXE" OR Image="*EXCEL.EXE" OR Image="*WINWORD.EXE") | stats count by host, User, Image, CommandLine | sort - count
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BTUN-L (Image="*chrome.exe" OR Image="*winword.exe" OR Image="*excel.exe" OR Image="*acrord32.exe" OR Image="*outlook.exe" OR Image="*notepad.exe") | stats count by host, User, Image, CommandLine | sort - count
