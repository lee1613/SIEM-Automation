# s1 - Q217 - Round 6
_stamped by runner: rounds_remaining=2 novel_spl=8_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinHostMon, osquery:results, aws:s3:accesslogs, stream:http | fields=Image, TargetFilename, CommandLine, url, src, dest, _raw
**Insight:** NOT_FOUND
**Candidate:** none (visualization type unknown; attachment = pwned.jpg, established)   **Confidence:** 20

## Prior rounds
- R1: Mapped 102 sourcetypes; Bud=btun@froth.ly; 13 outbound subjects; messagetrace carries no attachment fields.
- R2: "RE: Splunk service needs a restart" (09:47:48Z) proven attachment-free; Bud's MIME attachments: pwned.jpg (10:24:29Z), Employee New Hire Dates.xlsx (11:11:17Z).
- R3: Exchange audit = admin cmdlets; FilePreviewed = birthday/beer files; discovered structured attach_* fields + full MIME `content` in stream:smtp.
- R4: Full 11-event attachment inventory; both Bud bodies read — pwned.jpg thread is Fyodor banter, xlsx is HR; messagetrace sizes confirm no other Bud attachment.
- R5: Traced pwned.jpg origin — BTUN-L downloaded it from temp-e.net/files/incoming/hoffa/ at 10:22:47Z, 2 min before emailing.
- R6 (this round): Sysmon puts pwned.jpg on disk on both endpoints; recipient opened it twice; PowerPoint ran later but is unlinked; no text names the chart.

## This round
### What I ran
- "pwned" across Sysmon/WinHostMon/osquery/S3/stream:http -> 6 Sysmon + 2 stream:http hits; zero in osquery:results, WinHostMon, aws:s3:accesslogs
- Sysmon EventID 11 extraction -> OUTLOOK.EXE wrote pwned.jpg to INetCache\Content.Outlook on BTUN-L @10:24:07 and on PCERF-L @10:24:46, plus "pwned (002).jpg" @10:25:03 (double write = Peat opened it)
- PCERF-L process/file survey -> POWERPNT.EXE launched 13:02:56Z with bare command line; no POWERPNT TargetFilename events; 635 process-creation events reviewed

### What it means
NOT_FOUND for the visualization type. The artifact chain is now complete end-to-end — external download (temp-e.net, 10:22:47Z) → outbound attachment (10:24:29Z) → on-disk on sender BTUN-L (10:24:07) → on-disk on recipient PCERF-L (10:24:46, 10:25:03, opened twice) — but the image's content exists only as base64 in MIME and as HTTP response bytes. No indexed text in any feed queried across six rounds names, captions, or describes the chart. PowerPoint activity three hours later has no command-line or file-event link to pwned.jpg. I did not decode the image and will not guess a two-word chart type.

## Ruled out
- osquery:results, WinHostMon, aws:s3:accesslogs - zero "pwned" hits; none indexed the filename
- POWERPNT.EXE on PCERF-L - launched with no file argument; created no files per Sysmon EventID 11
- stream:smb, code42:*, symantec:ep:* (R5) - zero "pwned" hits
- Employee New Hire Dates.xlsx - HR thread, chronologically second
- Miner vocabulary in stream:smtp - 0 events

## Open questions for SH
- The text/html part of the pwned.jpg email was never

_[truncated at 400 words]_

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
