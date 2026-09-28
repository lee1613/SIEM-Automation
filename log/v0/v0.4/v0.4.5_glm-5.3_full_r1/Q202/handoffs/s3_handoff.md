# s3 - Q202 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=7_
**Scope:** sourcetype=hardware, osquery:results, cpu, cloud-init, cloud-init-output, bootstrap, amazon-ssm-agent-too_small, aws:cloudwatch | fields=host, cpu_type, columns.*, message, _raw
**Insight:** FOUND
**Candidate:** E5-2676 v3   **Confidence:** 78

## Prior rounds
- s1: refuted p1 — osquery:results carries CPU strings beyond hardware/cpu_brand (hoth cpuid product_name = AMD FX(tm)-8120).
- s2: established web-server set = gacrux WebServers ASG fleet (8 t2.medium incl. i-0920036c8ca91e501); hardware feed covers 3 gacrux hosts, all E5-2676 v3; hoth ruled out; filed p3/p4/p5.
- R3: enumerated i-0920036c8ca91e501's osquery tables (no cpuid/system_info rows); eliminated FX-8120 rival (hoth only); submitted E5-2676 v3.
- R4: read all 166 system_profile events — osquery performance metrics, no CPU model; system_info query ran 7× on the host (109 bytes/exec) but no result rows captured.
- R5 (this round): swept every remaining host-bound feed for i-0920036c8ca91e501 — none carries a processor string.

## This round
### What I ran
- sourcetype=hardware host="gacrux.i-0920036c8ca91e501" -> 0 events.
- sourcetype=cpu | stats count by host -> hoth only (1192); sampled raw "all 2.00 0.00 4.00 0.00 94.00" — utilization percentages.
- sourcetype=cloud-init OR cloud-init-output OR bootstrap | stats count by sourcetype, host -> 7 rows: cloud-init/cloud-init-output cover only the 3 hardware-covered gacrux hosts; bootstrap hoth only.
- amazon-ssm-agent-too_small "i-0920036c8ca91e501" -> 725 events on the host; + "Xeon" OR "processor" OR "cpu" -> 0.
- aws:cloudwatch "i-0920036c8ca91e501" + "Xeon" OR "processor" OR "cpu_brand" -> 0.

### What it means
Feed by feed for i-0920036c8ca91e501: hardware — lacks coverage of the host; cpu — cannot contain a processor model (utilization only) and lacks gacrux coverage; cloud-init / cloud-init-output — lack coverage of the host; bootstrap — hoth only; amazon-ssm-agent — 725 events, no processor model; aws:cloudwatch — 411 events, no processor model; osquery:results (prior rounds) — no cpuid/system_info rows, system_profile is performance metrics, system_info query ran 7× with 109 bytes/exec output but rows never captured.

Stated explicitly: the only directly evidenced processor number on the verified web-server set is the hardware-feed value on the three confirmed gacrux web hosts — "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz" on i-06fea586f3d3c8ce8, i-09cbc261e84259b54, i-0cc93bade2b3cba63 — processor number **E5-2676 v3**. The exact unresolved premise preventing a fully sound set-wide answer is p5: i-0920036c8ca91e501's own CPU has no direct evidence — its system_info output (7 executions, 109 bytes each) was never captured as result rows, and no other host-bound feed for that host carries a processor string; the t2.medium instance-type corroboration remains inference, not direct evidence. No live rival processor string exists in the dataset outside hoth's AMD FX(tm)-8120, which is outside the web-server set.

## Ruled out
- hardware feed for i-0920036c8ca91e501 - 0 events, no coverage.
- sourcetype=cpu - utilization percentages only, hoth-only coverage.
- cloud-init/cloud-init-output for i-0920036c8ca91e501 - no coverage (3 other gacrux hosts only); bootstrap - hoth only.
- amazon-ssm-agent-too_small (725 events, 0 CPU matches); aws:cloudwatch (411 events, 0 CPU matches).
- system_profile - performance metrics, no CPU field; system_info rows on the host - never captured.
- AMD FX(tm)-8120 - hoth only, outside the WebServers fleet; osquery:results fleet-wide - "E5-2676" matches 0 events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p6 - amend or settle that one. The text you sent was discarded: "The host-bound telemetry sweep for i-0920036c8ca91e501 is exhausted with no proc"


## What I'd tell my replacement
- Retired because: retired: SH stamped one of its verifications false
- Scope I owned: sourcetypes=['cpu', 'top', 'ps', 'osquery:results', 'aws:description'] sources=[] fields=['host', 'processor', '_raw', 'columns.cpu_brand', 'columns.feature', 'columns.value', 'id', 'instance_type', 'image_id']
- Rounds worked: 3/5  (iterations: 33, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "E5-2676" | stats count by sourcetype, host, source
- index=botsv3 sourcetype=amazon-ssm-agent-too_small "i-0920036c8ca91e501" | stats count by host
- index=botsv3 sourcetype=amazon-ssm-agent-too_small host="gacrux.i-0920036c8ca91e501" "Xeon" OR "processor" OR "cpu" | stats count
- index=botsv3 sourcetype=aws:cloudwatch "i-0920036c8ca91e501" "Xeon" OR "processor" OR "cpu_brand" | stats count
- index=botsv3 sourcetype=cloud-init OR sourcetype=cloud-init-output OR sourcetype=bootstrap | stats count by sourcetype, host
- index=botsv3 sourcetype=cpu | stats count by host
- index=botsv3 sourcetype=cpu | stats count by pctCPU, CPU
- index=botsv3 sourcetype=hardware "E5-2676" | stats count by host, cpu_type
- index=botsv3 sourcetype=hardware host="gacrux.i-0920036c8ca91e501" | stats count by host, cpu_type
- index=botsv3 sourcetype=osquery:results "E5-2676" | stats count by host, columns.feature, columns.value
- index=botsv3 sourcetype=osquery:results "FX(tm)-8120" | stats count by host, columns.feature, columns.value
- index=botsv3 sourcetype=osquery:results "FX-8120" | stats count by host, columns.feature, columns.value
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" "system_profile" | stats count by columns.feature, columns.value
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" name=system_profile columns.name=system_info | stats count by columns.query, columns.output_size, columns.executions, columns.last_executed
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" name=system_profile | stats count
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" name=system_profile | stats count by columns.feature, columns.value
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" name=system_profile | stats count by columns.name
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" | stats count by name
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" | stats count by name, columns.feature, columns.value | search name=system_profile
- index=botsv3 sourcetype=osquery:results host=gacrux.i-0920036c8ca91e501 name=system_profile | stats count by columns.feature, columns.value
- index=botsv3 sourcetype=osquery:results name=system_profile | stats count by host
