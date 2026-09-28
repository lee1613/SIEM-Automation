# s1 - Q215 - Round 4
_stamped by runner: rounds_remaining=1 novel_spl=4_
**Scope:** sourcetype=WinEventLog (ComputerName field), WinHostMon (operatingsystem) | fields=ComputerName, OS
**Insight:** FOUND
**Candidate:** BSTOLL-L.froth.ly   **Confidence:** 95

## Prior rounds
- R1: WinHostMon operatingsystem (8 rows, all read) — BSTOLL-L = Windows 10 Enterprise, other 7 endpoints = Pro. Submitted BSTOLL-L.froth.ly with suffix inferred; no fqdn/dNSHostName field found.
- R2: stream:dns showed only BSTOLL-L.local (mDNS) and bare BSTOLL-L; WinEventLog queried with wrong field name (Computer, 0 rows); messagetrace = user mailboxes only.
- R3: code42:computer, symantec:ep:agent:file, stream:smb all short names or no hostnames; froth.ly DNS zone holds no endpoint names; p3 (BSTOLL-L.froth.ly) refuted on that evidence.
- R4: code42:api, code42:security, symantec:ep:scm_system:file, stream:dhcp checked — no FQDNs; then found the literal FQDN in WinEventLog ComputerName.

## This round
### What I ran
- get_sourcetype_fields code42:api / code42:security / symantec:ep:scm_system:file / stream:dhcp -> no endpoint FQDNs (code42:api = API metadata only; code42:security = deviceGuid/file paths; scm_system = SEPM server events; DHCP host_name = short names, domain_name = localdomain).
- Term search "frothly.local" across all in-scope feeds -> 0 events.
- Term search "frothly" across all in-scope feeds -> 7 sourcetypes matched, incl. WinEventLog (37) and Sysmon (29).
- get_raw_events WinEventLog keyword=frothly -> raw Security 4663/4688 events carry the literal line "ComputerName=BSTOLL-L.froth.ly".
- index=botsv3 sourcetype=WinEventLog | stats count by ComputerName -> 9 rows, all read: all 8 Frothly endpoints as <name>.froth.ly (BSTOLL-L.froth.ly = 24,427 events) plus SEPM.

### What it means
FOUND. The FQDN is literally recorded, not inferred: WinEventLog's ComputerName field names every Frothly Windows endpoint as hostname.froth.ly, and the differing-edition endpoint from the settled WinHostMon comparison — BSTOLL-L, the only Windows 10 Enterprise host among eight (others Pro) — appears as **BSTOLL-L.froth.ly** on 24,427 events. The 8 FQDNs map 1:1 to the 8 WinHostMon endpoints; SEPM is the Symantec server, outside the endpoint set. My round-2 miss was querying the field "Computer" (absent) instead of "ComputerName"; the round-3 refutation of the .froth.ly form rested on that gap and is superseded by the literal raw-event evidence.

## Ruled out
- code42:api - API call metadata only, no hostnames.
- code42:security - deviceGuid, file paths, processOwner; no endpoint hostname.
- symantec:ep:scm_system:file - SEPM server events only.
- stream:dhcp - host_name = short names; domain_name = localdomain.
- "frothly.local" as a suffix - 0 events across all in-scope feeds.
- BSTOLL-L.local - only the mDNS form in stream:dns; superseded by the literal FQDN in WinEventLog.
- SEPM as a comparison endpoint - Symantec server, absent from WinHostMon endpoint inventory.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_raw_events: {"keyword": "frothly", "limit": 10, "sourcetype": "WinEventLog"}` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
