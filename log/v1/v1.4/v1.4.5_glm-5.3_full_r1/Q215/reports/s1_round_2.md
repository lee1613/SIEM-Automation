# s1 - Q215 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=8_
**Scope:** sourcetype=WinHostMon (operatingsystem, computer), stream:dns, WinEventLog, XmlWinEventLog:Sysmon, ms:o365:reporting:messagetrace | fields=ComputerName, OS, Domain, host, query, name, SenderAddress
**Insight:** partial
**Candidate:** BSTOLL-L.froth.ly   **Confidence:** 55

## Prior rounds
- R1: WinHostMon operatingsystem (8 rows, all read) — BSTOLL-L = Windows 10 Enterprise, other 7 endpoints = Windows 10 Pro; no fqdn/dNSHostName field anywhere; computer table = WORKGROUP. Submitted BSTOLL-L.froth.ly with the suffix flagged as inferred.

## This round
### What I ran
- sample_events stream:dns keyword=bstoll (5 events) -> BSTOLL-L appears as "BSTOLL-L.local" (mDNS, udp/5353, src 192.168.247.131) and bare "BSTOLL-L" (LLMNR, udp/5355).
- WinEventLog | stats count by Computer -> 0 rows (field absent); | stats count by host -> 9 rows, all short hostnames (BSTOLL-L 24427) plus SEPM.
- Sysmon | stats count by Hostname -> 0 rows; | stats count by host -> 8 short hostnames.
- messagetrace bstoll* | stats count by SenderAddress -> 15 rows; bstoll@froth.ly (89 events) is the user's mailbox, not an endpoint name.
- stream:dns SPL enumerations (BSTOLL*, *bstoll*) -> 0 rows (leading-wildcard/tool quirk); the keyword search is the only working view of that feed.

### What it means
The differing-edition endpoint is settled: BSTOLL-L, the only Windows 10 Enterprise host among eight. For the FQDN, the only domain-qualified form of this endpoint's name observed anywhere in scope is **BSTOLL-L.local**, from mDNS. froth.ly is evidenced as Frothly's mail domain (bstoll@froth.ly and eight other @froth.ly users) but no artifact shows the endpoint as BSTOLL-L.froth.ly. I hold BSTOLL-L.froth.ly as the candidate on the conventional hostname+corporate-domain construction; BSTOLL-L.local is the strictly data-evidenced alternative, and the suffix choice between them is not yet settled by any record I could reach. code42:computer, symantec:ep:agent:file, stream:smb and ms:aad:* — the feeds most likely to record a host.domain form — were outside this round's scope.

## Ruled out
- WinEventLog Computer field - absent (0 rows); host field carries short names only.
- Sysmon Hostname field - absent; host = short names.
- ms:o365:reporting:messagetrace - carries user email addresses (@froth.ly), not endpoint hostnames.
- Script:GetEndpointInfo - 3 hosts, short names, no OS edition (R1).
- osquery:results - Linux hosts only (R1).
- fqdn / dNSHostName fields - absent from the dataset (R1).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
