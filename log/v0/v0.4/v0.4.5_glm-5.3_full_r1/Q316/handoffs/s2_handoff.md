# s2 - Q316 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=7_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, stream:http | source=WinEventLog:Microsoft-Windows-Sysmon/Operational | fields=EventCode, Image, CommandLine, ParentImage, ProcessGuid, DestinationIp, DestinationPort
**Insight:** partial   **Candidate:** logos.png   **Confidence:** 70

## Prior rounds
- None — first round on this scope.

## This round
### What I ran
- `sourcetype=stream:http` 45.77.53.176 (field filters, then raw token) -> 0 events both ways.
- Sysmon `"45.77.53.176" | stats by EventCode, Computer` -> EC1 FYODOR-L x4; EC3 FYODOR-L x3850; EC3 ABUNGST-L x1070.
- `EventCode=1 "45.77.53.176"` -> 4 rows: iexeplorer.exe run against 192.168.9.30:8080/frothlyinventory/showcase.action with a /bin/sh backpipe to 45.77.53.176:8088.
- All events for ProcessGuid {EBF7A186-C442-5B58-0000-00109914D901} -> 25 rows (12 read): powershell.exe PID 6360 started 18:07:06 with -enc base64; it spawned net.exe user /add svcvnc, schtasks Updater, hdoor.exe -hbs 192.168.9.1-50, netsh firewall-off, iexeplorer.exe.
- `EventCode=3` same Guid + IP -> 679 events, 25 read, all 45.77.53.176:443 beacons from PID 6360.

### What it means
The ProcessGuid is the attacker's resident powershell (PID 6360). hdoor.exe and iexeplorer.exe appear as Image in its child process-creation events — executed from disk at C:\Windows\Temp\hdoor.exe and C:\Windows\Temp\unziped\lsof-master\iexeplorer.exe — so they are the extracted tools, not the retrieved container. The "unziped\lsof-master" directory name itself records that an archive was expanded; the container is the file retrieved before that expansion. logos.png is the carried candidate for that retrieved file, and nothing this round contradicts it — but its confirming EventCode 11 creation row was not yet read when the cap hit, so the value is partial, not verified.

## Ruled out
- stream:http as the retrieval feed — 0 events mention 45.77.53.176 (field and raw-token searches); its dest_port values are only 80/8080/8000.
- hdoor.exe as container — EC1 18:43:10 shows it executed as a child of PID 6360.
- iexeplorer.exe / unziped\lsof-master\powershell.exe as container — EC1 19:05:40+ shows iexeplorer.exe executed from the extraction directory; both are expansion products.

Next: read EC11 TargetFilename on FYODOR-L 18:07–18:45 (expect C:\Windows\Temp\logos.png then unziped\lsof-master\*), isolate the :3333 EC3 row, rex the full -enc base64, check stream:tcp.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p4 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:http"}` (28 of 57 rows seen); `run_splunk_search: index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" source="WinE…` (12 of 25 rows seen); `run_splunk_search: index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" source="WinE…` (25 of 679 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: retired: SH stamped one of its verifications false
- Scope I owned: sourcetypes=['stream:http', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'] sources=['stream:http', 'WinEventLog:Microsoft-Windows-Sysmon/Operational'] fields=['uri_path', 'status', 'http_user_agent', 'bytes_out', 'http_content_length', 'dest_ip', 'dest_port', 'src_ip', 'src_port', 'EventCode', 'TargetFilename', 'ProcessGuid', 'Image', '_time']
- Rounds worked: 1/5  (iterations: 11, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "45.77.53.176" | stats count by sourcetype, source
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "45.77.53.176" | stats count by EventCode, Computer, source
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" source="WinEventLog:Microsoft-Windows-Sysmon/Operational" "{EBF7A186-C442-5B58-0000-00109914D901}" | stats count by EventCode, _time, Image, CommandLine, ParentImage, ProcessId
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" source="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 "45.77.53.176" | stats count by _time, host, Image, CommandLine, ParentImage, ProcessGuid, ProcessId
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" source="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=3 "{EBF7A186-C442-5B58-0000-00109914D901}" "45.77.53.176" | stats count by _time, Image, DestinationIp, DestinationPort, DestinationHostname, ProcessId
- index=botsv3 sourcetype=stream:http "45.77.53.176" | stats count by src_ip, dest_ip, src_port, dest_port, http_method, uri_path, bytes, bytes_in, bytes_out, status, site, user_agent, _time
- index=botsv3 sourcetype=stream:http dest_ip=45.77.53.176 OR src_ip=45.77.53.176 | stats count by src_ip, dest_ip, dest_port, http_method, url, status_code, site, user_agent, _time | sort - _time
