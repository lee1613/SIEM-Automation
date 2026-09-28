# s2 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=11_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="osquery:results" "192.168.8.117" | stats count by host, source
- index=botsv3 sourcetype="stream:http" "192.168.9.25" | stats count min(_time) as first, max(_time) as last by uri_path, src
- index=botsv3 sourcetype="stream:http" ".png" | stats count by uri_path, src, dest
- index=botsv3 sourcetype="bash_history" ("png" OR "scrot" OR "screenshot" OR "import " OR "gnome-screenshot" OR "spectacle") | stats count by host, source
### What it means

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="stream:http" ".png" | stats count by uri_path, src, dest` (50 of 764 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: Retiring for wrong-question drift and non-usable reporting. The last round reported no results and searched generic IP/.png/screenshot terms without tying them to Bud Stoll, the candidate attachment names, or the 'first attachment' requirement.
- Scope I owned: sourcetypes=['osquery:results', 'code42:api', 'code42:computer', 'code42:security', 'code42:user', 'symantec:ep:agent:file', 'symantec:ep:packet:file', 'symantec:ep:traffic:file', 'symantec:ep:behavior:file', 'WinHostMon', 'stream:http'] sources=[] fields=['filename', 'path', 'process', 'uri', 'url', 'object', 'file_name', 'CommandLine']
- Rounds worked: 2/8  (iterations: 25, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "1534778082419.png" | stats count by sourcetype, source
- index=botsv3 sourcetype IN ("bash_history","config_file","linux_audit") "1534778082419.png" | stats count by sourcetype, source
- index=botsv3 sourcetype IN ("stream:http","stream:smb","stream:smtp") "1534778082419.png" | stats count by sourcetype, source
- index=botsv3 sourcetype IN ("symantec:ep:security:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:scm_system:file","symantec:ep:agt_system:file") "1534778082419.png" | stats count by sourcetype, source
- index=botsv3 sourcetype IN ("XmlWinEventLog:Microsoft-Windows-Sysmon/Operational","WinHostMon","osquery:results","symantec:ep:agent:file","symantec:ep:risk:file","symantec:ep:security:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:scm_system:file","symantec:ep:agt_system:file","WinEventLog","bash_history","config_file","linux_audit","stream:http","stream:smb","code42:api","code42:computer","code42:org","code42:security","code42:user","aws:s3:accesslogs") ("choropleth" OR "single value" OR "filler gauge" OR "radial gauge" OR "marker gauge" OR "cluster map" OR "bubble chart" OR "punchcard" OR "sankey") | stats count by sourcetype, source, host
- index=botsv3 sourcetype IN ("XmlWinEventLog:Microsoft-Windows-Sysmon/Operational","WinHostMon","osquery:results","symantec:ep:agent:file","symantec:ep:risk:file","symantec:ep:security:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:scm_system:file","symantec:ep:agt_system:file","WinEventLog","bash_history","config_file","linux_audit","stream:http","stream:smb","code42:api","code42:computer","code42:org","code42:security","code42:user","aws:s3:accesslogs") ("image002.jpg" OR "Malware Alert Text.txt" OR "winmail.dat" OR "1534778082419.png") | stats count by sourcetype, source, host
- index=botsv3 sourcetype IN ("XmlWinEventLog:Microsoft-Windows-Sysmon/Operational","WinHostMon","osquery:results","symantec:ep:agent:file","symantec:ep:risk:file","symctec:ep:security:file","symantec:ep:security:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:scm_system:file","symantec:ep:agt_system:file","WinEventLog","bash_history","config_file","linux_audit","stream:http","stream:smb","code42:api","code42:computer","code42:org","code42:security","code42:user","aws:s3:accesslogs") ("choropleth" OR "single value" OR "filler gauge" OR "radial gauge" OR "marker gauge" OR "cluster map" OR "bubble chart" OR "punchcard" OR "sankey") | stats count by sourcetype, source, host
- index=botsv3 sourcetype="bash_history" ("png" OR "scrot" OR "screenshot" OR "import " OR "gnome-screenshot" OR "spectacle") | stats count by host, source
- index=botsv3 sourcetype="osquery:results" "1534778082419.png" | stats count by source, host
- index=botsv3 sourcetype="osquery:results" "192.168.8.117" | stats count by host, source
- index=botsv3 sourcetype="stream:http" ".png" | stats count by uri_path, src, dest
- index=botsv3 sourcetype="stream:http" "192.168.9.25" | stats count by uri_path, src, dest
- index=botsv3 sourcetype="stream:http" "192.168.9.25" | stats count min(_time) as first, max(_time) as last by uri_path, src
- index=botsv3 sourcetype="stream:http" dest="192.168.9.25" | stats count by uri_path, src, user
- index=botsv3 sourcetype="stream:http" dest_port=8000 OR src_port=8000 | stats count by dest, dest_port, uri_path
- index=botsv3 sourcetype="symantec:ep:agent:file" "1534778082419.png" | stats count by source, host
- index=botsv3 sourcetype="symantec:ep:risk:file" "1534778082419.png" | stats count by source, host
- index=botsv3 sourcetype="WinEventLog" "1534778082419.png" | stats count by source, host
- index=botsv3 sourcetype="WinHostMon" "1534778082419.png" | stats count by source, host
- index=botsv3 sourcetype="WinHostMon" "1534778082419.png" | stats count by sourcetype, source
- index=botsv3 sourcetype="WinHostMon" "192.168.8.117" | stats count by host, source
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "1534778082419.png" | stats count by Computer, EventCode
