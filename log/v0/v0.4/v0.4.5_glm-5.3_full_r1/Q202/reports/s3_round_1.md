# s3 - Q202 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Scope:** sourcetype=hardware, osquery:results | source=/var/log/osquery/osqueryd.results.log | fields=cpu_type, columns.feature, columns.value, name, host
**Insight:** FOUND
**Candidate:** E5-2676 v3   **Confidence:** 75

## Prior rounds
- s1: refuted p1 — osquery:results carries a CPU string outside hardware/cpu_brand: columns.feature=product_name, "AMD FX(tm)-8120 Eight-Core Processor".
- s2: established web-server set = gacrux EC2 fleet in WebServers ASG (8 t2.medium incl. i-0920036c8ca91e501); hardware feed covers 3 gacrux hosts, all E5-2676 v3; hoth ruled out (internal SuiteCRM); filed p3/p4/p5.
- R3 (this round): mapped i-0920036c8ca91e501's telemetry, eliminated the FX-8120 rival, enumerated its osquery tables.

## This round
### What I ran
- get_sources keyword=i-0920036c8ca91e501 -> host-bound telemetry is osquery:results (47,098 events); also aws:cloudwatch (411), aws:description ec2_instances, cloudtrail, ssm-agent logs.
- index=botsv3 sourcetype=osquery:results "E5-2676" | stats count by host, columns.feature, columns.value -> 0 events.
- index=botsv3 sourcetype=hardware "E5-2676" | stats count by host, cpu_type -> 3 events: gacrux.i-06fea586f3d3c8ce8, i-09cbc261e84259b54, i-0cc93bade2b3cba63, all cpu_type="Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz".
- index=botsv3 sourcetype=osquery:results "FX(tm)-8120" | stats count by host, columns.feature, columns.value -> 1 event: host=hoth, product_name="AMD FX(tm)-8120 Eight-Core Processor".
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" | stats count by name -> 12 tables (proc_events 46,319; system_profile 166; mounts, shell_history, kernel_modules, etc.). No cpuid, no system_info.

### What it means
Three members of the gacrux WebServers fleet directly record cpu_type "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz" in the hardware feed — processor number E5-2676 v3, evidenced on web servers' own records, not via the retired same-CPU inference. The only other CPU-model string in the dataset, AMD FX(tm)-8120, belongs to hoth (internal SuiteCRM, not a web server), so no live rival remains. On i-0920036c8ca91e501 specifically: no cpuid or system_info osquery table ever ran there, and no E5-2676 string exists anywhere in osquery:results; its 166 system_profile events are the one unexamined artifact that could directly confirm on that host — the cap hit before I read them.

## Ruled out
- AMD FX(tm)-8120 as the web-server processor - sole occurrence is host=hoth, outside the WebServers fleet.
- osquery:results as carrier of the fleet CPU string - "E5-2676" matches 0 events fleet-wide.
- cpuid/system_info osquery tables on i-0920036c8ca91e501 - absent from its 12-table osquery schedule.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
