# Q208 — SH <-> Senior conversation

### 12:48:38 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['PerfmonMk:Process', 'cpu', 'top', 'ps', 'osquery:results', 'WinHostMon'] sources=- fields=['process', 'Name', 'Percent_Processor_Time', 'pctCPU', 'host', '_time', 'CommandLine', 'Image', 'columns.*']
**Technique:** senior
**Reason:** The question is about endpoint process behavior and CPU saturation, so the answer should come from host process/performance telemetry. This scope includes Windows process performance counters plus adjacent CPU/process inventories that can reveal the suspicious mining process and the earliest moment it hit 100 percent utilization.

Identify the Frothly endpoint exhibiting coin-mining activity, then determine which process associated with that activity first reached 100 percent CPU processor utilization time on that endpoint, and return the exact process name as recorded.

### 12:58:29 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> 
_full: reports/s1_round_1.md_

### 12:58:29 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

### 12:58:29 - runner   [NOTE]
s1 api_failed — retired, spawn slot refunded

### 12:58:29 - runner   [NOTE]
s1 api_failed and no operator reachable — skipping; slot already refunded, decision request at C:\dev\SIEM-Automation\log\v1\v1.4/v1.4.5_glm-5.3_full_r1\decision_request.json

### 12:58:34 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['PerfmonMk:Process', 'cpu', 'top', 'ps', 'osquery:results', 'WinHostMon'] sources=- fields=['process', 'Process', 'Name', 'ID Process', 'PercentProcessorTime', 'percent_processor_time', 'cpu', 'host', 'dest']
**Technique:** senior
**Reason:** The prior senior was lost to transport failure before producing any findings. The answer still depends on endpoint process and CPU telemetry, especially process-performance counters that can show the earliest process to hit 100 percent utilization on the mined-on host.

Identify the Frothly endpoint exhibiting coin-mining activity, then determine which process tied to that activity first reached 100 percent CPU processor utilization time on that endpoint, and return the exact process name as recorded.

### 13:04:25 - s2 -> SH   [REPORT - round 1 - FOUND]
> Timeline (UTC, Aug 20 2018): feed spans 13:04:21-18:37:59 on BSTOLL-L only. 100% Processor_Time readers: MicrosoftEdgeCP#2 13:36:26 (1 sample); chrome#5 17:37:50, 2 more by 18:59:19 (3 total); chrome#4 17:38:30-18:04:11 (129 samples, sustained ~26 min = the mining); MsMpEng 18:04:31 (1 sample, Defen
_full: reports/s2_round_1.md_

### 13:04:33 - SH -> s2   [COMMAND]
SH's answers to your open questions:
[q1] Treat chrome#5 as the strongest rival because your own result says its first 100% sample is 40 seconds earlier than chrome#4. To answer soundly, you must establish which process is actually part of the coin-mining activity and then which qualifying 100% event comes first within that activity, rather than relying only on sustained duration.

**continue** — This round found the correct measurement feed and surfaced the key selection problem. The case now needs the mining activity itself established on BSTOLL-L and then mapped to the 100% CPU events so 'first' is answered against the activity, not merely against any process spike on the host.
**New scope:** sourcetypes=['PerfmonMk:Process', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinEventLog', 'WinHostMon', 'Script:GetEndpointInfo'] sources=[] fields=['%_Processor_Time', 'process_cpu_used_percent', 'process_name', 'instance', 'Image', 'ParentImage', 'CommandLine', 'Destination', 'User', 'ProcessGuid', 'host', '_time']

Establish the coin-mining activity on BSTOLL-L from endpoint evidence already adjacent to this scope, then compare chrome#4 and chrome#5 against that activity. Determine which process instances are actually part of the mining behavior, when that activity begins, and which associated process first reaches 100 percent CPU processor utilization time. If both are involved, state which one reaches 100 first by timestamp; if only one is tied to mining, show what rules the other out. Also provide exact result output to support the existing coverage and selection premises.

### 13:06:08 - s2 -> SH   [REPORT - round 2 - NOT_FOUND]
> 
_full: reports/s2_round_2.md_

### 13:06:15 - SH -> s2   [COMMAND]
**retry** — The current scope is still relevant, but the approach drifted into speculative keyword hunts that did not establish coin-mining activity or resolve the chrome#4 versus chrome#5 rival. The final round must use BSTOLL-L host evidence to tie the suspicious activity to concrete process instances and earliest 100% timestamps.
**New scope:** sourcetypes=['PerfmonMk:Process', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'ps', 'process', 'WinHostMon'] sources=[] fields=['%_Processor_Time', 'process_name', 'instance', '_time', 'Image', 'ProcessId', 'ParentProcessId', 'CommandLine', 'process', 'host']

On BSTOLL-L, enumerate the actual processes and process instances present around 17:37:00–18:05:00 in host telemetry adjacent to PerfmonMk:Process, and determine whether chrome#4 and chrome#5 map to one executable/process lineage or to distinct instances. Then establish, from the recorded CPU telemetry itself, which candidate process instance first reaches 100 percent CPU during the suspicious high-CPU window. If no separate mining identifier exists in the available evidence, say explicitly that the answer is constrained to the earliest 100% qualifying process in the high-CPU activity window and report which instance that is.

### 13:35:15 - s2 -> SH   [REPORT - round 3 - NOT_FOUND]
> 
_full: reports/s2_round_3.md_

### 13:35:23 - SH -> s2   [ANSWER]
**chrome#5** (process_name) from s2

s2's final report states literally that PID 3400 was recorded as "chrome#5" when it first hit 100% at 17:37:50, and later as "chrome#4" for the sustained run. That makes chrome#5 the earliest recorded process name to reach 100 percent CPU in the suspicious high-CPU activity window on BSTOLL-L. The answer rests on unverified premises about mining attribution and full coverage of rivals, but no rounds or senior slots remain, so I am answering on that stated limitation.

**Premises it rests on:** p1, p2, p3, p4

### 13:35:23 - runner   [NOTE]
answered on an unverified premise (R4 = FAIL) — allowed, but dangerous ground: s2's final report states literally that PID 3400 was recorded as "chrome#5" when it first hit 100% at 17:37:50, and later as "chrome#4" for the sustained run. That makes chrome#5 the earliest recorded process name to reach 100 percent CPU in the suspicious high-CPU activity window on BSTOLL-L. The answer rests on unverified premises about mining attribution and full coverage of rivals, but no rounds or senior slots remain, so I am answering on that stated limitation.

### 13:35:23 - runner   [NOTE]
answered with UNVERIFIED premises in the ledger — allowed (nothing left to try), but dangerous ground: p1 Per-process CPU utilization on the mined Frothly endpoint is recorded only in sourcetype=PerfmonMk:Process (host BSTOLL-L, fields %_Processor_Time / process_cpu_used_percent / process_name); that feed covers a single host and the whole Aug 20 2018 window, and no other sourcetype (WinHostMon, osquery:results) was searched for CPU counters.; p2 chrome#4 is the coin-mining process on BSTOLL-L and the first process to reach 100% processor time from that activity, because it alone shows sustained 100% Processor_Time (129 consecutive samples over ~26 minutes, 17:38:30-18:04:11Z) - the signature of a miner pegging a core - while MicrosoftEdgeCP#2 and MsMpEng show single transient spikes and chrome#5 shows 3 sporadic spikes that are not mining behavior.; p3 Coverage: on BSTOLL-L, per-process 100 percent CPU utilization relevant to this question is measured in PerfmonMk:Process process-instance telemetry, and the held evidence narrowed the suspicious high-CPU window to the competing browser instances chrome#5 and chrome#4 on PID 3400.; p4 Selection: the first process name to reach 100 percent CPU from the suspicious activity recorded on BSTOLL-L is chrome#5, because s2's final report states PID 3400 was recorded as chrome#5 when it first hit 100% at 17:37:50 and only later as chrome#4 for the sustained run.

### 13:35:23 - s2 -> SH   [HANDOFF]
_full: handoffs/s2_handoff.md_

