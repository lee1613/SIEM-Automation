# s2 - Q324 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=1_
**Scope:** code42:api | code42:computer | code42:org | ms:aad:audit | Script:InstalledApps | WinHostMon — keyword reads of _raw for Bungstein / abungstein / ABUNGST
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 30

## Prior rounds
- R1: no phone/mobile/cell/carrier-named field exists in any of the 102 sourcetypes; code42:user, ms:aad:signin and o365:management:activity ruled out as carrier sources.
- R2 (this round): every remaining identity/profile and endpoint-inventory feed ruled out — zero Bungstein artifacts anywhere in the assigned scope.

## This round
### What I ran
- get_raw_events code42:api keyword=Bungstein -> 0 events; keyword=abungstein -> 0 events
- get_raw_events code42:computer keyword=Bungstein -> 0; keyword=abungstein -> 0
- get_raw_events code42:org keyword=Bungstein -> 0
- get_raw_events ms:aad:audit keyword=Bungstein -> 0; keyword=abungstein -> 0
- get_raw_events Script:InstalledApps keyword=ABUNGST -> 0
- get_raw_events WinHostMon keyword=ABUNGST -> 10 of 10 events, all Type=Process rows for Host="ABUNGST-L" (splunk forwarder, chrome, search hosts, audiodg) — no contact or carrier data
- Script:InstalledApps fleet-wide carrier-branded app search (Name=*Verizon* / *AT&T* / *T-Mobile* / *Sprint* / *Carrier* / *Mobile*) | stats count by Name, host -> 0 events

### What it means
NOT_FOUND: the assigned scope is exhausted. Bungstein appears in no Code42 feed and no ms:aad:audit event under either identifier form; his endpoint ABUNGST-L has no installed-apps inventory at all, so no carrier-branded app can exist on it; WinHostMon's 10 ABUNGST-L rows are process telemetry only, read in full. The carrier is not in identity/profile data or endpoint software inventory anywhere in botsv3. Limitation: I did not confirm the overall event counts of code42:api/computer/org or ms:aad:audit — if a feed is entirely empty its 0-result keyword search is uninformative about Bungstein specifically, though it still holds no carrier artifact.

## Ruled out
- code42:api, code42:computer, code42:org — 0 events mentioning Bungstein or abungstein
- ms:aad:audit — 0 events mentioning Bungstein or abungstein (retired senior's unsearched item d, now closed)
- Script:InstalledApps — no ABUNGST-L inventory; no carrier-branded app fleet-wide
- WinHostMon ABUNGST-L — 10 rows, all Type=Process, no contact data

Next: the only live route is free text in non-identity event bodies — WinEventLog / Sysmon command lines, bash_history, stream:http bodies, ess_content_importer, aws:cloudtrail — none yet searched, all outside this round's scope.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p3 - amend or settle that one. The text you sent was discarded: "Al Bungstein's cell carrier, if present anywhere in botsv3, is free text inside "
