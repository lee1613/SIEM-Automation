# s3 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=2_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 (sourcetype=stream:http OR sourcetype=osquery:results OR sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" OR sourcetype=WinEventLog) | stats min(_time) AS earliest max(_time) AS latest count BY sourcetype
- index=botsv3 sourcetype=stream:http ("Splunk chart" OR "metrics store" OR "check it out" OR "allhands" OR "bstoll" OR "Bud Stoll") | stats count by site, uri_path
### What it means
Intention: Check the endpoint feeds (osquery, Sysmon, WinEventLog) for any trace of the thread identifiers (brewertalk, allhands, bstoll, Bud Stoll) — a temp file, cache object, or process command line tied to the thread would appear there.


## What I'd tell my replacement
- Retired because: This senior is done. It keeps returning to the same narrowed endpoint/browser lead without producing result-backed findings, and this round again reports intention rather than evidence. With no spawn slots left, further rounds here are unlikely to reach the two-word visualization value.
- Scope I owned: sourcetypes=['osquery:results', 'stream:http', 'stream:smb', 'stream:dns', 'WinEventLog', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'symantec:ep:packet:file', 'symantec:ep:traffic:file', 'access_combined'] sources=[] fields=['filename', 'path', 'command', 'url', 'uri', 'query', 'dest', 'src', 'process', 'image', 'file_name', 'ObjectName']
- Rounds worked: 4/8  (iterations: 25, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "image001.jpg" | stats count by sourcetype, source
- index=botsv3 (sourcetype=stream:http OR sourcetype=osquery:results OR sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" OR sourcetype=WinEventLog) | stats min(_time) AS earliest max(_time) AS latest count BY sourcetype
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "image00" | stats count by EventCode, ComputerName
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "image001.jpg" | stats count by EventCode, ComputerName
- index=botsv3 sourcetype=osquery:results "image00" | stats count by source, name
- index=botsv3 sourcetype=stream:http "brewertalk" | stats count by source, http_method, status
- index=botsv3 sourcetype=stream:http "brewertalk" | top limit=40 uri_path
- index=botsv3 sourcetype=stream:http "image00" | stats count by source, http_method, status
- index=botsv3 sourcetype=stream:http "image001.jpg" | stats count by source, http_method, status
- index=botsv3 sourcetype=stream:http "miner" | stats count by site, uri_path
- index=botsv3 sourcetype=stream:http "splunk" | stats count by site, uri_path
- index=botsv3 sourcetype=stream:http ("Splunk chart" OR "metrics store" OR "check it out" OR "allhands" OR "bstoll" OR "Bud Stoll") | stats count by site, uri_path
- index=botsv3 sourcetype=stream:http uri_path="/attachment.php" | stats count by url
- index=botsv3 sourcetype=WinEventLog "image00" | stats count by source, EventCode
- index=botsv3 sourcetype=WinEventLog "image001.jpg" | stats count by source, EventCode
