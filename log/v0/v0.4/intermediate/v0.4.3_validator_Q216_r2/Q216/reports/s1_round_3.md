# s1 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=1_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields sa, da, dp, fss, fes, pn, ppn, liuid, ibc, obc
**Insight:** FOUND   **Candidate:** 112   **Confidence:** 90

## Prior rounds
- R1: Confirmed feed; ruled out process-name and keyword axes; found the only dp=3333 flow; hand-computed 112.
- R2: Full pool-IP sweep (4 groups) and complete 22-value dp enumeration; duration computed in SPL (112); 443 traffic ruled out as C2 by behavior (avg 0.9s, 2.4KB in).
- R3: Answered SH's clarification on quotes and partial results from held outputs; no new searches.
- R4 (this round): one consolidated complete query settling both open premises (p1 coverage, p5 measurement).

## This round
### What I ran
- `da=45.77.53.176 | eval duration=fes-fss | stats count min(fss) as first max(fes) as last sum(duration) as total_duration_seconds by sa, dp | sort dp` -> complete, 4 of 4 rows:
  - `{"sa": "192.168.105.214", "dp": "80", "count": "2", "first": "1534758533", "last": "1534758752", "total_duration_seconds": "219"}`
  - `{"sa": "192.168.24.128", "dp": "443", "count": "1015", "first": "1534759261", "last": "1534766363", "total_duration_seconds": "1266"}`
  - `{"sa": "192.168.70.186", "dp": "443", "count": "3814", "first": "1534759304", "last": "1534766374", "total_duration_seconds": "3452"}`
  - `{"sa": "192.168.70.186", "dp": "3333", "count": "1", "first": "1534762025", "last": "1534762137", "total_duration_seconds": "112"}`

### What it means
**Coverage (p1):** this complete output is every flow to the pool IP across all source IPs and all destination ports — only one group touches a mining-pool port (3333, count=1). With the complete 22-value dp enumeration (no 14444/45700/5555/7777/4444 anywhere) and round-1's full results (all 60 pn values, no miner; "monero" 0 events), every representation p1 names is searched: process name, literal token, pool port, pool IP on any port.

**Measurement (p5):** the question's duration is the qualifying mining flow's recorded start/end span in Cisco NVM — `eval duration=fes-fss` on the dp=3333 flow gives **112** — not download or beacon traffic. The same output shows what is excluded and why: the 443 groups are 3,814 and 1,015 sub-second beacons (avg 0.9s/flow, ~2.4KB in, 628B out — C2), and the 80 group is Edge browsing by a different user. The 3333 flow's own records show the act: 5,782,875 bytes inbound over 112s by powershell.exe (parent powershell.exe) under FyodorMaltesko.

## Ruled out
- 45.77.53.176:443 (3,814 + 1,015 flows) - sub-second sub-KB C2 beacons, not mining.
- 45.77.53.176:80 (2 flows) - Edge browsing, BruceGist.
- Other mining ports (14444, 45700, 5555, 7777, 4444) - absent from the complete 22-value dp enumeration.
- dp=8080 - internal 192.168.8.x -> 192.168.9.30 staging, not a pool.