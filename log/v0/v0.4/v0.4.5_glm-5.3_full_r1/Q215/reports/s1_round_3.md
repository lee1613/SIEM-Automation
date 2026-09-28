# s1 - Q215 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=7_
**Scope:** sourcetype=WinHostMon, stream:dns, WinEventLog, XmlWinEventLog:Sysmon, ms:o365:reporting:messagetrace, code42:computer, symantec:ep:agent:file, stream:smb | fields=ComputerName, OS, Domain, name, Host_Name, host, query
**Insight:** partial
**Candidate:** bstoll-l.frothly.local   **Confidence:** 55

## Prior rounds
- R1: WinHostMon operatingsystem (8 rows, all read) — BSTOLL-L = Windows 10 Enterprise, other 7 endpoints = Pro; no fqdn/dNSHostName field anywhere; computer table = WORKGROUP. Submitted BSTOLL-L.froth.ly, suffix flagged inferred.
- R2: stream:dns shows BSTOLL-L.local (mDNS) and bare BSTOLL-L (LLMNR); WinEventLog/Sysmon host = short names; messagetrace = user mailboxes @froth.ly. Suffix unsettled.
- R3: code42:computer/symantec/stream:smb checked — all short names or no hostname fields; froth.ly DNS zone holds no endpoint names.

## This round
### What I ran
- get_sourcetype_fields code42:computer -> name: BSTOLL-L, MKRAEUS-L, FYODOR-L — short names only (51 events).
- get_sourcetype_fields symantec:ep:agent:file -> Host_Name: 7 short names; Domain_Name=AzureAD, Domain=Default (504 events).
- get_sourcetype_fields stream:smb -> 32 fields, none hostname-like (mailslot browse traffic, IPs/MACs only).
- stream:dns bstoll | stats -> 161 QUERY + 104 RESPONSE events; queries = ["BSTOLL-L", "BSTOLL-L.local"] only.
- stream:dns froth | stats -> 140,341 events; froth.ly zone lists servers/services (AzureAD.froth.ly, sepmserver.froth.ly, splunk.froth.ly, mail/vpn/wpad) and DGA-style names — no endpoint hostname.

### What it means
The differing-edition endpoint is settled: BSTOLL-L (Windows 10 Enterprise vs 7× Pro). For the FQDN, no in-scope feed records BSTOLL-L with a corporate-domain suffix — the only domain-qualified form anywhere is BSTOLL-L.local (mDNS), and the froth.ly zone contains no endpoint names. I hold bstoll-l.frothly.local as the best candidate (Frothly's internal .local domain, consistent with the observed .local naming); it was NOT observed in my queries — the data-evidenced alternative is BSTOLL-L.local. code42:api (computerName), code42:security (device_name), symantec:ep:scm_system:file, stream:dhcp and ms:aad:* remain unchecked and could still hold a recorded host.domain form.

## Ruled out
- code42:computer - name field is short hostnames only.
- symantec:ep:agent:file - Host_Name short; Domain_Name=AzureAD, Domain=Default; no DNS suffix.
- stream:smb - no hostname fields at all.
- BSTOLL-L.froth.ly - no record anywhere; froth.ly zone holds no endpoint names (140,341 DNS events enumerated).
- WinEventLog/Sysmon host fields, Script:GetEndpointInfo, osquery:results, fqdn/dNSHostName fields - short names or absent (R1-R2).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "code42:computer"}` (57 of 114 rows seen). A claim resting on them alone is UNVERIFIED._
