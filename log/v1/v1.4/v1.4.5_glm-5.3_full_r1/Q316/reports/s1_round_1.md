# s1 - Q316 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=7_
**Scope:** sourcetype=stream:http | sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | fields=uri_path, url, bytes_out, src_ip, dest_ip, dest_port, EventCode, TargetFilename, host
**Insight:** FOUND
**Candidate:** logos.png   **Confidence:** 85

## Prior rounds
- Round 1 (this round): located the retrieval event and the tool-creation events; no prior rounds.

## This round
### What I ran
- `index=botsv3 sourcetype="stream:http" "45.77.53.176"` -> 1 retrieval: GET /images/logos.png from 45.77.53.176:3333, status 200, 5,542,140 bytes out, src 192.168.70.186, 18:47:16+08:00.
- `... Sysmon EventCode=3 dest_ip=45.77.53.176 dest_port=3333` -> 1 event: host=FYODOR-L, src_ip=192.168.70.186, 18:47:06.
- `... Sysmon host=FYODOR-L EventCode=11` -> 18 events (all returned): C:\Windows\Temp\hdoor.exe; C:\Windows\Temp\unziped\lsof-master\iexeplorer.exe; C:\Windows\Temp\unziped\lsof-master\powershell.exe; remainder benign (Edge .lnk downloads, PSScriptPolicyTest .ps1 temps, hosts.ac.tmp, Tasks\Updater, DismHost.exe).
- Time-bounded EventCode=11 query (18:40–20:00) -> 0 rows; timezone offset between stream:http's +08:00 rendering and Sysmon's stored times, so timestamps were not directly comparable.

### What it means
FOUND. The retrieval socket 45.77.53.176:3333 delivered exactly one file: logos.png, 5.5 MB — a size no genuine logo image needs. Immediately downstream on the same host, Sysmon records the attack tools appearing inside C:\Windows\Temp\unziped\lsof-master\ (iexeplorer.exe, powershell.exe) plus C:\Windows\Temp\hdoor.exe. The directory name "unziped" is itself evidence of archive extraction: those executables are the extracted contents, not the container. Since logos.png is the only file retrieved on that path, it is the file inferred to contain the attack tools — a PNG-named archive. The dropped executables fail the container test because they are the artifacts the container produced.

## Ruled out
- hdoor.exe, iexeplorer.exe, powershell.exe - dropped executables created in C:\Windows\Temp and C:\Windows\Temp\unziped\; they are the contents, not the container.
- Edge downloads (BRUCE BIRTHDAY HAPPY HOUR PICS .lnk/.partial) - benign user browsing artifacts, unrelated to the 45.77.53.176 retrieval.
- Any .zip file - no archive filename appears anywhere in FYODOR-L's 18 EventCode=11 records; the archive arrived under the logos.png name.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "45.77.53.17…` (50 of 3669 rows seen). A claim resting on them alone is UNVERIFIED._
