# s2 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=9_
**Scope:** Sysmon EventCode=11/1 (host, TargetFilename, Image, CommandLine, User, ProcessGuid, CurrentDirectory) + code42:security file-sync
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1: no queries executed (empty reply).
- Round 2: enumerated code42:api/osquery/WinHostMon/Sysmon; ruled out three feeds as filename sources; read Sysmon file-creates on BTUN-L, BSTOLL-L, PCERF-L; found PCERF-L ~WRD000.jpg lead.
- Round 3 (this): completed Sysmon file-create coverage on all 8 hosts; tightened PCERF-L chain with raw events; discovered code42:security file-sync feed with real filenames; still no Splunk illustration artifact or visualization type.

## This round
### What I ran
- Sysmon EventCode=11 counts by host -> 172 events across 8 hosts; per-host reads: FYODOR-L (18 rows), MKRAEUS-L (8), JWORTOS-L (8), BGIST-L (50 of 54, remainder excluded by NOT-filter -> 0 new).
- get_raw_events keyword=M0UPC09M -> 7 events: OUTLOOK.EXE PID 5632 created the cache 10:24:46 UTC, saved pwned.jpg (10:24:46) and pwned (002).jpg (10:25:03), then ~WRD000.jpg (10:33:05) — a Word-style inline-image render from a later email.
- Sysmon EventCode=1 Image=*POWERPNT* -> MKRAEUS-L (MalloryKraeusen, 1) and PCERF-L (PeatCerf, 2); no file argument in CommandLine.
- get_source_types -> 102 sourcetypes; code42:security fields -> files{}.fileName/fullPath/fileEventType, processOwner BudStoll/MalloryKraeusen.
- code42:security | mvexpand files{}.fileName | stats by fileName,fullPath,fileEventType -> 111 rows, 50 returned.
### What it means
NOT_FOUND: complete Sysmon file-create coverage across all 8 employee hosts shows no Splunk export, dashboard image, or miner-illustration document, and no record states a visualization type. code42:security adds real filenames (frothly_html_memcached.tar.gz, frothly-servers.pem, ba_advertising_code_overview.pdf, frothly_gabf_deck-2018-mk.pptx, Edge backup files) but none is a Splunk illustration. The mvexpand pairing was misaligned (fileName and fullPath exploded independently), so those pairs are unreliable; 61 of 111 rows unread.

## Assumptions
- Coverage: Sysmon TargetFilename — all 8 hosts fully read this round — VERIFIED. Sysmon CommandLine for Office apps — POWERPNT/OUTLOOK/EXCEL carry no file argument — VERIFIED. code42:security files{}.fileName — 13 distinct values, ~12 seen, pairing broken, 61 rows unread — PARTIALLY VERIFIED. symantec:ep:* file feeds, o365:management:activity — not searched — UNVERIFIED.
- Selection: PCERF-L lead (Word inline image 10:33:05) and MKRAEUS-L lead (frothly_gabf_deck-2018-mk.pptx + POWERPNT) are the two behavioural candidates; neither is tied to Bud or to the miner topic yet — UNVERIFIED.
- Premise that the attachment's name or content reveals the visualization — no artifact recovered, so untestable — UNVERIFIED.

## Ruled out
- Sysmon file-creates on all 8 hosts (172 events) — no Splunk/miner illustration artifact; keyword search for splunk/miner/chart/dashboard/coin/monero -> 0.
- code42:api, osquery:results, WinHostMon — no filename capability (round 2).
- pwned.jpg / pwned (002).jpg — attacker taunt images, not a Splunk illustration.
- BA_Advertising_Code_Overview.pdf — advertising-code document, unrelated to coin miner.

## Open questions for SH
- Should the next round fix the code42:security fileName/fullPath pairing (rex over _raw) and read the 61 unread rows before pivoting to symantec:ep:* file feeds?
- Is frothly_gabf_deck-2018-mk.pptx worth O365 corroboration as a possible Bud attachment, or is it known to be Mallory's own GABF deck?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=11…` (50 of 54 rows seen); `run_splunk_search: index=botsv3 sourcetype=code42:security | mvexpand "files{}.fileName" | stats count by "fi…` (50 of 111 rows seen). A claim resting on them alone is UNVERIFIED._
