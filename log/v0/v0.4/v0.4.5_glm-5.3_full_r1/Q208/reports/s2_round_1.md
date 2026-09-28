# s2 - Q208 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=6_
**Scope:** sourcetype=PerfmonMk:Process (host=BSTOLL-L) | fields=%_Processor_Time, process_cpu_used_percent, process_name, instance, _time; corroborated with XmlWinEventLog:Microsoft-Windows-Sysmon/Operational
**Insight:** FOUND
**Candidate:** chrome#4   **Confidence:** 65

## Prior rounds
- None. Prior senior was lost to transport failure before producing findings; this is round 1.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; PerfmonMk:Process identified as the per-process Windows performance-counter feed.
- get_sourcetype_fields PerfmonMk:Process -> %_Processor_Time, process_cpu_used_percent, process_name/instance; single host BSTOLL-L; 139,828 events.
- `index=botsv3 sourcetype="PerfmonMk:Process" "%_Processor_Time"=100 | stats count min(_time) max(_time) by process_name instance | sort first_time` -> 4 processes: MicrosoftEdgeCP#2 (1 sample, 13:36:26Z), chrome#5 (3, first 17:37:50Z), chrome#4 (129, first 17:38:30Z, last 18:04:11Z), MsMpEng (1, 18:04:31Z).
- `| stats min(_time) max(_time) dc(process_name) by host` -> feed covers only BSTOLL-L, 13:04-18:37Z Aug 20 2018.
- avg/max CPU by process_name -> TiWorker avg 74.8/max 99.55 (never 100); chrome#4 avg 22.9/max 100 over 641 samples.
- Sysmon EventCode=1 on BSTOLL-L by Image -> chrome.exe first created 14:29:32Z from explorer.exe; 50 of 68 rows read (truncated).

### What it means
BSTOLL-L is the only endpoint with per-process CPU telemetry and is the mined host. chrome#4 is the only process whose 100% readings exhibit mining behavior: 129 consecutive samples at 100% Processor_Time spanning ~26 minutes (17:38:30-18:04:11Z) - a miner pegging a core. The other three 100% readers are transient: MicrosoftEdgeCP#2 (one sample, 4h before the mining window), MsMpEng (one sample at 18:04:31Z, immediately after chrome#4's run ended - Defender responding), chrome#5 (3 samples scattered over 81 min - browser-like, not sustained). chrome#4 is therefore the first process to reach 100% processor time from the mining activity, recorded as "chrome#4".

## Ruled out
- MicrosoftEdgeCP#2 - single 100% sample at 13:36:26Z, ~4h before mining; transient browser spike.
- MsMpEng - single 100% at 18:04:31Z, Defender scan as the miner run ended.
- chrome#5 - 3 sporadic 100% samples (17:37:50-18:59:19Z), not sustained; CAVEAT: its first spike is 40s before chrome#4's, so it is the rival if "first" is read strictly temporally.
- TiWorker - avg 74.8%, max 99.55%, never reached 100.
- Other endpoints - PerfmonMk:Process carries BSTOLL-L only.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_field_values: {"field": "process_name", "sourcetype": "PerfmonMk:Process", "top_n": 20}` (20 of 277 rows seen); `run_splunk_search: index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BSTOLL-…` (50 of 68 rows seen). A claim resting on them alone is UNVERIFIED._
