# s1 - Q202 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=3_
**Scope:** sourcetype=hardware, osquery:results, access_combined, apache_error, aws:elb:accesslogs | fields: host, cpu_type, columns.cpu_brand
**Insight:** FOUND
**Candidate:** E5-2676 v3   **Confidence:** 70

## Prior rounds
Round 1 (this round): identified the web tier and located the only CPU-model fields in the dataset.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; hardware, osquery:results flagged as host-inventory candidates
- search_keyword processor / cpu -> only CPU-model fields in the dataset are hardware.cpu_type and osquery:results columns.cpu_brand
- index=botsv3 sourcetype=hardware (get_sourcetype_fields) -> cpu_type "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz" on 3 gacrux hosts
- index=botsv3 sourcetype=osquery:results columns.cpu_brand=* | stats count by host, columns.cpu_brand -> identical string on 2 gacrux hosts (2 events)
- index=botsv3 (access_combined OR apache_error OR aws:elb:accesslogs) | stats count by sourcetype, host -> 4 gacrux instances + hoth emit Apache logs; ELB logs on splunk.froth.ly
- sample_events access_combined -> user-agent "ELB-HealthChecker/2.0" confirms the gacrux fleet serves behind the Frothly ELB

### What it means
The web servers are the gacrux EC2 fleet serving Apache behind the Frothly ELB. The host-inventory feed (sourcetype=hardware) records cpu_type "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz" on 3 of the 4, corroborated by osquery cpu_brand on 2. Per the question's example format (Intel Core i7-8650U -> i7-8650U), the processor number is E5-2676 v3.

## Ruled out
- code42:computer - cloud console feed for Windows laptops (MKRAEUS-L, BSTOLL-L, FYODOR-L); modelInfo=null, no CPU data, no web servers
- WinHostMon / Script:GetEndpointInfo - Windows endpoint feeds; no Windows host serves web traffic (web logs are Apache on Linux hosts; no IIS feed exists)
- dmesg/syslog CPU fields (nr_cpu_ids, CPUs, NR_CPUS) - core counts, not processor model

Caveats: gacrux.i-0920036c8ca91e501 (busiest web host) has no hardware/osquery CPU record - the other three agree on E5-2676 v3, consistent with a uniform EC2 fleet, but that one host is inferred. hoth also emits access_combined (240 events); its role and CPU are unverified and no feed covers it.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "code42:computer"}` (57 of 114 rows seen). A claim resting on them alone is UNVERIFIED._
