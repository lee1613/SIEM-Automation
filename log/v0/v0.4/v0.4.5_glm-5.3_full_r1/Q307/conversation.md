# Q307 — SH <-> Senior conversation

### 19:26:08 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinHostMon', 'symantec:ep:risk:file', 'symantec:ep:security:file', 'osquery:results', 'stream:tcp', 'stream:ip'] sources=- fields=['ComputerName', 'TargetFilename', 'Image', 'CommandLine', 'Hashes', 'process', 'file_name', 'MD5', 'dest_ip', 'dest_port', 'src_ip']
**Technique:** senior
**Reason:** The asked value is a file hash tied to a downloaded file on one endpoint, so the direct evidence is most likely in endpoint file/process telemetry that records filenames and hashes. Network telemetry is needed only to confirm which downloaded file was actually used for the later scanning activity.

Identify the file that was downloaded to Fyodor's endpoint and subsequently used to scan Frothly's network, then determine and return that file's MD5 value exactly as recorded in the data.

### 19:28:13 - s1 -> SH   [REPORT - round 1 - FOUND]
> MD5 recorded in the Sysmon Hashes field as MD5=586EF56F4D8963DD546163AC31C865D7 (uppercase, exactly as recorded); SHA256=99925199059EE049F7AEDA8904C2F5BDFBA86671FD7A5989BD60B72F26EF737C. File: C:\Windows\Temp\hdoor.exe, parent process powershell.exe, executed 2018-08-20T18:43:10+08:00. The download 
_full: reports/s1_round_1.md_

### 19:28:22 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] The strongest current candidate is hdoor.exe because its FYODOR-L process-create command line sweeps 192.168.9.1-192.168.9.50, which fits network scanning, and that same row carries MD5 586EF56F4D8963DD546163AC31C865D7. What remains to settle is the selection against iexeplorer.exe and the 'downloaded to Fyodor's endpoint' linkage from endpoint artifacts.

**continue** — This round found a plausible scanner file and its MD5 in the right endpoint feed, but the answer still rests on an unverified selection premise. One more round should directly settle which FYODOR-L file was used to scan the network and confirm the endpoint-download linkage from Sysmon file/process evidence.
**New scope:** sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'] sources=['WinEventLog:Microsoft-Windows-Sysmon/Operational'] fields=['EventCode', 'Image', 'CommandLine', 'Hashes', 'TargetFilename', 'ParentImage', 'DestinationIp', 'host']

On FYODOR-L in Sysmon, settle the selection directly. Provide exact output for the file-create and process-create records for hdoor.exe and iexeplorer.exe, then establish which one fits 'downloaded to Fyodor's endpoint system and used to scan Frothly's network' by comparing their execution behavior: IP-range sweep versus single-host exploitation. Also show the exact Hashes value on the selected file's execution or creation record and restate the MD5 literally if unchanged.

### 19:31:11 - s1 -> SH   [REPORT - round 2 - FOUND]
> MD5 unchanged from round 1: 586EF56F4D8963DD546163AC31C865D7 (uppercase, exactly as recorded in the Sysmon Hashes field; SHA256=99925199059EE049F7AEDA8904C2F5BDFBA86671FD7A5989BD60B72F26EF737C). Full chain on FYODOR-L: powershell.exe PID 6360 (encoded downloader) created C:\Windows\Temp\hdoor.exe at
_full: reports/s1_round_2.md_

### 19:31:17 - SH -> s1   [COMMAND]
**continue** — The right endpoint feed and rival set are now identified, and the only blocker is ledger verification of the file-selection step. One more round should quote the exact Sysmon rows that distinguish hdoor.exe as the scanner and carry its MD5.

Settle premise p2 with exact word-for-word output from FYODOR-L Sysmon only. Quote the EventCode=11 file-create rows for hdoor.exe and iexeplorer.exe showing both were dropped by the same powershell.exe process, then quote the EventCode=1 hdoor.exe execution row with the full IP-range sweep command line and Hashes field, and the contrasting iexeplorer.exe execution result showing it hit exactly one target host. Use those quoted rows to establish why hdoor.exe, not iexeplorer.exe, is the downloaded file used to scan Frothly's network, then restate the MD5 literally if unchanged.

### 19:32:04 - s1 -> SH   [REPORT - round 3 - FOUND]
> MD5 unchanged across all three rounds: 586EF56F4D8963DD546163AC31C865D7 (uppercase, exactly as recorded in the Sysmon Hashes field; SHA256=99925199059EE049F7AEDA8904C2F5BDFBA86671FD7A5989BD60B72F26EF737C). Selection chain on FYODOR-L: powershell.exe PID 6360 (encoded downloader) created both C:\Wind
_full: reports/s1_round_3.md_

### 19:32:10 - SH -> s1   [ANSWER]
**586EF56F4D8963DD546163AC31C865D7** (md5) from s1

FYODOR-L Sysmon directly records hdoor.exe being created on the endpoint and then executed once with command line `"C:\windows\temp\hdoor.exe" -hbs 192.168.9.1-192.168.9.50 /b /m /n`, which is the only held record that fits 'used to scan Frothly's network'. That same execution row carries `Hashes=MD5=586EF56F4D8963DD546163AC31C865D7`. The answer still rests on one load-bearing UNVERIFIED selection premise (hdoor.exe versus iexeplorer.exe) because the senior did not provide runner-acceptable quote text for p2 before budget expired; no senior rounds or slots remain, so I am answering on that single unverified premise and stating the limitation explicitly.

**Premises it rests on:** p1, p2

### 19:32:10 - runner   [NOTE]
answered with UNVERIFIED premises in the ledger — allowed (nothing left to try), but dangerous ground: p2 hdoor.exe is the file used to scan Frothly's network, not iexeplorer.exe: hdoor.exe's only execution sweeps an IP range (192.168.9.1-192.168.9.50 /b /m /n), which is the act of scanning; iexeplorer.exe's executions all target the single already-known host 192.168.9.30:8080 with post-exploitation commands (whoami, id, cat /etc/passwd, useradd), which is exploitation, not scanning.

### 19:32:10 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

