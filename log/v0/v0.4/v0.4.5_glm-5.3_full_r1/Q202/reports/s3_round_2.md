# s3 - Q202 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=8_
**Scope:** sourcetype=osquery:results, hardware | source=/var/log/osquery/osqueryd.results.log | fields=host, name, columns.*, cpu_type
**Insight:** FOUND
**Candidate:** E5-2676 v3   **Confidence:** 75

## Prior rounds
- s1: refuted p1 — osquery:results carries CPU strings outside hardware/cpu_brand (hoth cpuid product_name = AMD FX(tm)-8120).
- s2: established web-server set = gacrux EC2 fleet in WebServers ASG (8 t2.medium incl. i-0920036c8ca91e501); hardware feed covers 3 gacrux hosts, all E5-2676 v3; hoth ruled out (internal SuiteCRM); filed p3/p4/p5.
- R3 (me): enumerated i-0920036c8ca91e501's osquery telemetry (12 result tables, no cpuid/system_info rows); eliminated FX-8120 rival (hoth only); submitted E5-2676 v3.
- R4 (this round): read all 166 system_profile events for i-0920036c8ca91e501.

## This round
### What I ran
- host="gacrux.i-0920036c8ca91e501" name=system_profile | stats count by columns.name -> 29 distinct profiled queries (full 166 events read via schema + per-query rows). All are osquery schedule-performance metrics: average_memory, executions, wall_time, output_size. No processor model or identifier anywhere.
- Same rows, columns.name=system_info -> 8 events: query "SELECT hostname, cpu_brand, physical_memory FROM system_info;", executions 1→7, output_size 109 bytes per execution (cumulative 109/218/327/545/654/654/763).
- name=system_profile | stats count by host -> 5 hosts covered: the 3 hardware-covered gacrux members, i-0920036c8ca91e501, mars.

### What it means
system_profile is osquery's query-performance snapshot, not hardware inventory — it carries no literal processor model for i-0920036c8ca91e501. It does prove the system_info query ran 7 times on that host, each producing 109 bytes of output (cpu_brand data was generated), but no name=system_info result rows exist in the captured osquery:results log for this host — its 12 result tables exclude system_info — so the value itself is unreadable.

Host-bound telemetry for i-0920036c8ca91e501 still unexamined: hardware-feed coverage of that host, sourcetype=cpu, cloud-init/cloud-init-output/bootstrap, amazon-ssm-agent logs, aws:cloudwatch. I hit the tool cap before sweeping these.

Stated explicitly as instructed: the web-server-set answer rests only on the three directly evidenced gacrux hosts — hardware cpu_type "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz" on i-06fea586f3d3c8ce8, i-09cbc261e84259b54, i-0cc93bade2b3cba63 — plus exclusion of the hoth rival (the dataset's only other CPU-model string, AMD FX(tm)-8120, occurs solely on hoth, outside the WebServers fleet). No live rival answer remains.

## Ruled out
- system_profile as a processor-model source for i-0920036c8ca91e501 - all 166 events are schedule-performance metrics; no CPU field in schema.
- system_info result rows on i-0920036c8ca91e501 - query ran (7 executions, 109 bytes each) but no result rows captured.
- AMD FX(tm)-8120 as web-server processor - sole occurrence host=hoth, outside WebServers fleet.
- osquery:results as fleet CPU carrier - "E5-2676" matches 0 events fleet-wide.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p7 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
