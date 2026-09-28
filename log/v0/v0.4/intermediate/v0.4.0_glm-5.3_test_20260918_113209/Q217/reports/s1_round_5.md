# s1 - Q217 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=9_
**Scope:** sourcetype=osquery:results, symantec:ep:agent/traffic/packet/behavior:file, code42:security, code42:user, o365:management:activity, stream:http, stream:smb | fields=filename, path, ObjectId, dest, src, user, url, _raw
**Insight:** NOT_FOUND
**Candidate:** none (visualization type unknown; attachment = pwned.jpg, established)   **Confidence:** 20

## Prior rounds
- R1: Mapped 102 sourcetypes; Bud=btun@froth.ly; 13 outbound subjects; messagetrace has no attachment fields.
- R2: "RE: Splunk service needs a restart" (09:47:48Z) proven attachment-free; Bud's MIME attachments: pwned.jpg (10:24:29Z), Employee New Hire Dates.xlsx (11:11:17Z).
- R3: Exchange audit = admin cmdlets; FilePreviewed = birthday/beer files; discovered structured attach_* fields + MIME `content` in stream:smtp.
- R4: Full 11-event attachment inventory; both Bud bodies read — pwned.jpg thread is Fyodor banter, xlsx is HR; messagetrace sizes confirm no other Bud attachment exists.
- R5 (this round): traced pwned.jpg to its origin — downloaded by BTUN-L from temp-e.net 2 min before the email; no telemetry names the chart type.

## This round
### What I ran
- "pwned" across all 10 scoped feeds -> 2 hits, both stream:http; zero hits in osquery, symantec, code42, o365:management:activity, stream:smb
- stream:http "pwned" URL extraction -> GET http://temp-e.net/files/incoming/hoffa/pwned.jpg, src 192.168.3.130 (BTUN-L) -> 62.73.58.161, 2018-08-20T10:22:47Z, HTTP 200, 53644 bytes
- stream:http "pwned" status/content_type -> second event at 10:23:37Z, also HTTP 200 (URL not yet extracted)
- BTUN-L full HTTP history -> 2207 events, dominated by OCSP checks; the temp-e.net download is the only notable file fetch

### What it means
NOT_FOUND for the visualization type: the artifact is confirmed (pwned.jpg, downloaded from temp-e.net/files/incoming/hoffa/ by Bud's own workstation 2 minutes before he attached it), but its pixels exist only as base64 in MIME and as an HTTP response body — no indexed text anywhere names what the image depicted. The attachment half of the question is fully solved; the chart-type half needs either the second 10:23:37Z HTTP event's URL, other files under /files/incoming/hoffa/, or endpoint telemetry (Sysmon/osquery/WinHostMon) recording the file on disk — none of which I reached before the cap.

## Ruled out
- osquery:results, symantec:ep:* (4 feeds), code42:security, code42:user, o365:management:activity, stream:smb - zero "pwned" hits each; none indexed the filename
- Employee New Hire Dates.xlsx - HR thread, chronologically second
- "RE: Splunk service needs a restart on your workstations" - multipart/alternative, no attachment
- Miner vocabulary in stream:smtp - 0 events (miner/mining/monero/cryptocurrency/bitcoin/coin)
- 1534778082419.png - from ghoppy/hyunki, not Bud

## Open questions for SH
- Widen scope to XmlWinEventLog:Sysmon, WinHostMon, bash_history, and aws:s3 for "pwned" — the file's on-disk record or

_[truncated at 400 words]_

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
