# s1 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=ms:o365:reporting:messagetrace, stream:smtp, o365:management:activity | fields=SenderAddress, RecipientAddress, Subject, DateReceived, content_type, _raw (MIME)
**Insight:** FOUND
**Candidate:** pwned.jpg   **Confidence:** 55

## Prior rounds
- R1: Mapped 102 sourcetypes; confirmed Bud=btun@froth.ly; enumerated his 13 outbound subjects; found no attachment fields in messagetrace; "coin" absent from stream:smtp text.

## This round
### What I ran
- get_raw_events/sample_events on stream:smtp "workstations" -> 5 events exist but display empty (oversized)
- index=botsv3 sourcetype=stream:smtp "workstations" | stats count by content_type -> all 5 are multipart/alternative: NO attachment on the 09:47:48Z "RE: Splunk service needs a restart" email
- index=botsv3 sourcetype=stream:smtp "filename" | rex ... | stats by timestamp -> 11 attachment-bearing events; Bud owns exactly 2: "pwned.jpg" @10:24:29Z and "Employee New Hire Dates.xlsx" @11:11:17Z
- Cross-check vs messagetrace timing -> pwned.jpg rides "RE: meeting with F" to pcerf@froth.ly (sent 10:24:27Z); xlsx rides "RE: Need hire dates pls" to ghoppy@froth.ly (11:11:15Z)

### What it means
FOUND (attachment half): SH's hypothesis is confirmed — Bud's earliest relevant outbound message IS "RE: Splunk service needs a restart on your workstations" (09:47:48Z), but it has NO attachment, so the first attached file on Bud's mail is "pwned.jpg" on "RE: meeting with F" (10:24:29Z, to pcerf@froth.ly). The miner-issue linkage is inferred from the "pwned" name and timing, not from a read body. The visualization type is NOT established: the jpg exists only as base64 MIME, unsearchable as text, and I exhausted iterations before extracting the HTML body part or checking endpoint/OneDrive telemetry for the file.

## Ruled out
- "RE: Splunk service needs a restart on your workstations" as the attachment carrier - multipart/alternative, no attachment part
- "Employee New Hire Dates.xlsx" as first attachment - chronologically second (11:11:17Z) and HR-themed
- stream:smtp literal "coin" search - 0 events; token absent from all journaled mail

## Open questions for SH
- Confirm "RE: meeting with F" is in-scope as a coin-miner-issue email, or name the thread SH means
- Next round priority: extract the text/html body of the pwned.jpg email, or sweep o365:management:activity FilePreviewed/osquery for the file?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
