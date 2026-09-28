# s1 - Q210 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 (sourcetype=WinHostMon OR sourcetype=PerfmonMk:Process OR sourcetype="osquery:results" OR sourcetype=ps) (xmrig* OR minerd OR cpuminer OR cgminer OR stratum OR cryptonight) | stats count by sourcetype, host
### What it means
Intention: Search for Monero mining indicators across all Windows endpoint telemetry (Sysmon, WinHostMon, PerfmonMk) — process names, command lines, and hashes commonly associated with Monero miners.
