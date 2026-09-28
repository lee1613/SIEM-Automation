# s2 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Scope:** code42:security (files{}.fileName/fullPath/fileEventType, processOwner) + symantec:ep:* file feeds + Sysmon PCERF-L window
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1: no queries executed (empty reply).
- Round 2: ruled out code42:api/osquery/WinHostMon as filename sources; read Sysmon file-creates on BTUN-L, BSTOLL-L, PCERF-L; found PCERF-L ~WRD000.jpg lead.
- Round 3: completed Sysmon file-create coverage on all 8 hosts (172 events); found code42:security feed; mvexpand pairing was misaligned.
- Round 4 (this): repaired code42:security extraction, exhausted it and all six symantec:ep:* feeds; no Splunk illustration artifact anywhere in endpoint/file-sync scope.

## This round
### What I ran
- get_raw_events code42:security -> confirmed files is an array of complete objects; mvzip+rex extraction -> 12 true file-event triples, all read.
- Raw reads for the 3 names missing from mvzip -> frothly-servers.pem (RULE_MATCH, BudStoll keys), OneDrive dir + desktop.ini (SCAN, BudStoll) — all 13 code42:security filenames now accounted for.
- get_sourcetype_fields / stats on all symantec:ep:* feeds -> risk:file = 1 event (Bruce Birthday Happy Hour Pics.lnk/Backdoor.PsEmpire); agent:file = client-log chatter; behavior:file = Splunk forwarder/cmd paths only; security:file = browser EXEs; packet:file = empty.
- Sysmon PCERF-L EventCode=1, UtcTime 10:20–10:40 -> 11 process creates, no Office application.
- Index-wide visualization-term search rejected (no sourcetype filter) — not run.
### What it means
NOT_FOUND: the endpoint/file-sync scope is exhausted. No feed in it names a Splunk export, dashboard image, or miner-illustration document, and no record states a visualization type. The two-word answer cannot be derived from anything I verified.

## Assumptions
- Coverage: code42:security — all 13 distinct filenames read with correct pairing — VERIFIED. symantec:ep:risk:file/agent:file/behavior:file/security:file/packet:file — all enumerated, no user-document filenames — VERIFIED. Sysmon file-creates — all 8 hosts fully read (rounds 2–3) — VERIFIED. o365:management:activity, stream:smtp, code42:computer/org/user, WinEventLog Application — not searched — UNVERIFIED.
- Selection: Bud candidates btun and bstoll both checked in file-sync (code42 shows only BudStoll); neither shows a Splunk artifact — VERIFIED. frothly_gabf_deck-2018-mk.pptx is MalloryKraeusen's upload, not tied to Bud or the miner issue — VERIFIED as untied.
- Premise that the attachment's content reveals the visualization — untestable; no artifact recovered — UNVERIFIED.

## Ruled out
- code42:security (all 13 filenames: frothly_html_memcached.tar.gz/.txt, frothly-servers.pem, OneDrive/desktop.ini, edb*.log, schema.txt, spartan.*, ba_advertising_code_overview.pdf, frothly_gabf_deck-2018-mk.pptx) — none is a Splunk illustration or Bud email attachment.
- symantec:ep:risk:file (1 event, birthday .lnk malware), agent:file (log chatter), behavior:file (system paths), security:file (browser EXEs), packet:file (empty).
- Sysmon file-creates on all 8 hosts; code42:api; osquery:results; WinHostMon (rounds 2–3).
- pwned.jpg / pwned (002).jpg — attacker taunt images, not Splunk illustrations.

## Open questions for SH
- May the next round use o365:management:activity (never explored by either senior) to identify the mail Peat Cerf previewed at 10:33:05 UTC on Aug 20, given endpoint evidence fixed host/user/time?
- Should the per-sourcetype visualization-term sweep (the rejected query) be run across o365:management:activity and stream:smtp first, before any further endpoint pivot?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
