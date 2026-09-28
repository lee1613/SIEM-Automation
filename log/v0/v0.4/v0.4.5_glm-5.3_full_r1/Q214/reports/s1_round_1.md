# s1 - Q214 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=3_
**Scope:** sourcetype=symantec:ep:security:file, symantec:ep:risk:file | fields=Host_Name, signature, action, Event_Description, user, src, Intrusion_URL
**Insight:** FOUND
**Candidate:** BTUN-L   **Confidence:** 85

## Prior rounds
- None — first round on this question.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; eight symantec:ep:* feeds present.
- search_keyword "coin" / "miner" -> 0 matches (matches field names only, not values).
- get_sourcetype_fields symantec:ep:risk:file -> 91 field rows, every field count=1: a single field-extracted event, BGIST-L, Backdoor.PsEmpire, Requested action "Cleaned", Actual "Cleaned by deletion", Secondary "Quarantined" — a backdoor, not cryptocurrency.
- get_sourcetype_fields symantec:ep:security:file -> 63 field rows; Host_Name distinct_count=1 = BTUN-L (46 events); signatures "Web Attack: JSCoinminer Download 6" (SID 30356, 23) and "Download 8" (SID 30358, 23); action=blocked on all 46; Event_Description "attack blocked. Traffic has been blocked for this application"; user=BillyTun; src=54.67.127.227; Intrusion_URL=www.brewertalk.com pages; apps Edge/Chrome.

### What it means
BTUN-L's own records positively show the act the question names: SEP's host IPS blocked 46 JSCoinminer download attacks ("attack blocked. Traffic has been blocked", action=blocked) while BillyTun browsed the compromised brewertalk.com — successful prevention, i.e. defeat, of the cryptocurrency threat. The rival BSTOLL-L has no records in this feed (Host_Name distinct_count=1 = BTUN-L), and carried-forward findings put actual miner execution on BSTOLL-L — infection, not defeat. BGIST-L's risk event is a PowerShell Empire backdoor, unrelated to cryptocurrency.

## Ruled out
- BGIST-L (symantec:ep:risk:file) — only field-extracted risk event is Backdoor.PsEmpire cleaned/quarantined, not a coinminer.
- BSTOLL-L in symantec:ep:security:file — feed's only Host_Name value is BTUN-L; no coinminer-block records for BSTOLL-L.
- search_keyword coin/miner — field-name matching only, 0 hits; value evidence found via fieldsummary instead.

Gaps: risk-feed fieldsummary extracted fields from only one event; no direct host-filtered BSTOLL-L search; endpoint telemetry (WinEventLog/osquery/WinHostMon) not yet checked for miner-termination evidence.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
