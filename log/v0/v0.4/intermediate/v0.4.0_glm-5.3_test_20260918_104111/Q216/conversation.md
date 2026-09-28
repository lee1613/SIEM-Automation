# Q216 — SH <-> Senior conversation

### 10:41:35 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'app', 'url', 'domain', 'bytes', 'packets', '_time']
**Technique:** hunter
**Reason:** The question explicitly names Cisco NVM flow logs, and this feed is present only on the source axis as cisconvmflowdata under sourcetype=syslog; a single tightly scoped senior can answer it without parallelization.

Using the Cisco NVM flow feed at source="cisconvmflowdata", identify the endpoint traffic that corresponds to Monero cryptocurrency mining and establish the start and end of that mining activity so the total duration in seconds can be calculated.

### 10:47:03 - s1 -> SH   [REPORT - round 1 - FOUND]
> Mining window: first flow start fss=1534759261 (Mon Aug 20 2018 10:01:01 UTC) to last flow end fes=1534766374 (11:59:34 UTC); duration = 1534766374-1534759261 = 7113 seconds. Chain: powershell.exe is the only anomalous process in the feed (4,835 events); 99.9% of its flows go to external IP 45.77.53
_full: reports/s1_round_1.md_

### 10:47:07 - SH -> (new)   [ANSWER]
**7113** (count) from s1

The report establishes mining traffic in Cisco NVM flow logs as powershell.exe flows to 45.77.53.176, notes the mining window from fss=1534759261 to fes=1534766374, and literally computes the duration as 7113 seconds while excluding the two non-mining Edge browsing flows.

### 10:47:07 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

