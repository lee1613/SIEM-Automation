# s1 - Q215 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=1_
**Scope:** sourcetype=WinHostMon | source=operatingsystem, computer | fields=ComputerName, OS, Domain, Name
**Insight:** FOUND
**Candidate:** BSTOLL-L.froth.ly   **Confidence:** 60

## Prior rounds
- None — first round.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; WinHostMon, Script:GetEndpointInfo, osquery:results shortlisted as inventory feeds.
- get_sources sourcetype=WinHostMon -> 8 sources; operatingsystem (204 events) and computer (204) are the inventory tables.
- get_sourcetype_fields WinHostMon/operatingsystem -> OS field holds exactly two editions: "Microsoft Windows 10 Pro" (174 events) and "Microsoft Windows 10 Enterprise" (30 events); ComputerName has 8 distinct values.
- index=botsv3 sourcetype=WinHostMon source=operatingsystem | stats count by ComputerName, OS -> 8 rows, all read: ABUNGST-L, BGIST-L, BTUN-L, FYODOR-L, JWORTOS-L, MKRAEUS-L, PCERF-L = Windows 10 Pro; BSTOLL-L = Windows 10 Enterprise (30 events).
- get_sourcetype_fields WinHostMon/computer -> Domain=WORKGROUP on all 8 hosts; no DNS-suffix/FQDN field.
- get_sourcetype_fields Script:GetEndpointInfo -> 3 hosts only (ABUNGST-L, BTUN-L, FYODOR-L), short hostnames, no OS edition.
- get_sourcetype_fields osquery:results -> Linux hosts only (hoth, mars, gacrux).
- search_keyword "fqdn" -> 0 results; search_keyword "dNSHostName" -> 0 results.

### What it means
The edition comparison is settled: BSTOLL-L is the only Frothly Windows endpoint running Windows 10 Enterprise; the other seven run Windows 10 Pro. The FQDN is not directly recorded anywhere I reached — no fqdn or dNSHostName field exists, and WinHostMon's computer table reports WORKGROUP for every host. I constructed the FQDN as BSTOLL-L.froth.ly from the Frothly corporate domain. The hostname half is fully verified; the ".froth.ly" suffix is inferred and unverified — it needs confirmation from stream:dns, stream:smtp HELO names, or O365 message headers, which I did not reach this round. If the expected form is the bare hostname, the answer is BSTOLL-L.

## Ruled out
- Script:GetEndpointInfo - 3 hosts only, no OS edition field, short hostnames.
- osquery:results - Linux endpoints only (hoth, mars, gacrux).
- WinHostMon source=computer - Domain=WORKGROUP for all hosts; carries no FQDN/DNS suffix.
- fqdn / dNSHostName fields - absent from the dataset (keyword searches returned 0 events).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "osquery:results"}` (38 of 153 rows seen). A claim resting on them alone is UNVERIFIED._
