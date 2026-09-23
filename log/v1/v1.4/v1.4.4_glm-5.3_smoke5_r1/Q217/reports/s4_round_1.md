# s4 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=7_
**Scope:** sourcetype=code42:api, code42:security, code42:computer, code42:org, code42:user, WinEventLog, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinHostMon | fields=source, sourcetype, count
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1 (s2): Mapped Bud's brewertalk thread in stream:smtp; refuted p2/p4 — the earlier 13:50:47Z email (flow 2a2e1c18, image001.jpg) is off-topic ("Yeah. It looks like we have some issues - I haven't figured it out yet"), so the first qualifying illustrative email is the 13:56:27Z one with image002.jpg.
- R1 (s3): Counted 7 stream:smtp events with subject 'RE: Improved brewertalk.com - check it out!'; body text references 'the Splunk chart' but was not fully read; Postmortem email's image002.jpg is a different, later image (p6).
- R2 (retired senior): Proved osquery:results and symantec:ep:* cannot hold the answer; o365:management:activity ObjectId paths searched, no image content.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; confirmed all five code42:* feeds plus WinEventLog, WinHostMon, Sysmon exist
- sourcetype=code42:api "image002" | stats count by source -> 0 events
- sourcetype=code42:security "image002" | stats count by source -> 0 events
- sourcetype=code42:computer OR code42:org OR code42:user "image002" | stats count by sourcetype -> 0 events
- sourcetype=WinEventLog "image002" | stats count by source -> 0 events
- sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "image002" | stats count by source -> 0 events
- sourcetype=WinHostMon "image002" | stats count by source -> 0 events

### What it means
NOT_FOUND. SH's competing suspicion is eliminated: neither Code42 backup data (all five feeds) nor Windows host telemetry (WinEventLog, Sysmon, WinHostMon) holds any event mentioning image002 — no saved copy, path, filename, or derived artifact. The artifact therefore exists in scope only as the base64 JPEG in stream:smtp attach_content{} (unrenderable here) and is referenced by body prose ("the Splunk chart") that does not name the visualization kind. The two-word kind remains unreadable in this scope, and I hold no value that can be submitted as-is.

Caveat: the negatives match the literal token "image002" only; a renamed saved copy (Outlook save-as, downloaded .jpg under another name) would evade them and is not yet excluded.

## Ruled out
- code42:api / code42:security / code42:computer / code42:org / code42:user — 0 events mentioning "image002"
- WinEventLog / XmlWinEventLog:Microsoft-Windows-Sysmon/Operational / WinHostMon — 0 events mentioning "image002"
- osquery:*, symantec:ep:* — retired senior, carried forward
- o365:management:activity ObjectId paths — prior senior, carried forward

Next-round leads: (1) index-wide text search for visualization names ("choropleth", "gauge", "single value", "trellis") in stream:smtp bodies and other text feeds; (2) get_raw_events on the full 13:56:27Z email body; (3) "*.jpg" path search in Code42/Windows feeds per recipient host to catch renamed copies.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
