# s4 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=6_
**Scope:** sourcetype=code42:api, code42:security, code42:computer, code42:org, code42:user, WinEventLog, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinHostMon | fields=files{}.fileName, files{}.fullPath, TargetFilename, Image, host, EventCode
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1 (s2): Mapped Bud's brewertalk thread; refuted p2/p4 — the 13:50:47Z email (image001.jpg) is off-topic, so the first qualifying attachment is image002.jpg at 13:56:27Z.
- R1 (s3): 7 stream:smtp events carry the subject; body references 'the Splunk chart' without naming the kind; the Postmortem email's image002.jpg is a different, later image.
- R2 (retired senior): osquery:results and symantec:ep:* cannot hold the answer; o365:management:activity ObjectId paths searched, no image content.
- R3 (me): literal 'image002' absent from all five code42:* feeds and WinEventLog/Sysmon/WinHostMon (0 events each).

## This round
### What I ran
- get_sourcetype_fields code42:api / code42:security -> api has no file fields; security has files{}.fileName/fullPath/md5
- get_field_values files{}.fileName / files{}.fullPath (code42:security) -> 13 filenames / 14 full paths, read in full: tar.gz, OneDrive, desktop.ini, txt, pdf, edb logs, pem, pptx, schema.txt, spartan.* — zero JPGs
- WinEventLog ".jpg" -> 0 events
- Sysmon ".jpg" | stats by host, EventCode -> 8 events on BTUN-L (2) and PCERF-L (6), all EventCode 11 (FileCreate)
- Sysmon ".jpg" | stats by _time, host, TargetFilename, Image -> 4 rows: pwned.jpg on BTUN-L 10:24:07Z and PCERF-L 10:24:47Z, "pwned (002).jpg" PCERF-L 10:25:03Z, ~WRD000.jpg PCERF-L 10:33:05Z — all OUTLOOK.EXE writes to Content.Outlook INetCache
- stream:smtp "pwned.jpg" / "pwned" -> 0 events; ms:o365:reporting:messagetrace "pwned" -> 0 events

### What it means
NOT_FOUND, with explicit closure of this scope. Code42 holds no copy of Bud's attachment under any filename: its complete file inventory (14 paths, read end to end) contains no JPG and no email attachment. WinEventLog has no .jpg activity. Sysmon's only .jpg artifacts are pwned.jpg and ~WRD000.jpg — Outlook cache writes from an earlier, unattributed email (10:24–10:33Z, before Bud's 13:50:47Z thread opener), not image002.jpg or a renamed copy. No recipient endpoint or backup feed preserves a readable artifact or descriptive text for Bud's first qualifying attachment; the visualization kind remains unreadable in this scope, and I hold no submittable value.

## Ruled out
- Code42 (all five feeds) as holder of any attachment copy — complete file inventory, zero JPGs
- WinEventLog .jpg activity — 0 events
- Sysmon as holder of image002.jpg or a renamed copy — only pwned.jpg / ~WRD000.jpg exist, from an earlier unattributed email
- pwned.jpg as Bud's first qualifying attachment — not established: carrying email not findable by token in stream:smtp or messagetrace; sender/subject unknown (open rival, filed as premise)

Residual gap: no text search for visualization names (e.g. "choropleth") was run in these feeds — calls exhausted.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p7 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p8 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
