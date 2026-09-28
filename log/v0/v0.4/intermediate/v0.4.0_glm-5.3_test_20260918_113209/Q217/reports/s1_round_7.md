# s1 - Q217 - Round 7
_stamped by runner: rounds_remaining=1 novel_spl=8_
**Scope:** sourcetype=stream:smtp, stream:http, ms:o365:reporting:messagetrace | fields=content, _raw, attach_filename, url, src, dest, Subject, RecipientAddress, DateReceived
**Insight:** NOT_FOUND
**Candidate:** none (visualization type unknown; attachment = pwned.jpg, established)   **Confidence:** 15

## Prior rounds
- R1: Mapped 102 sourcetypes; Bud=btun@froth.ly; 13 outbound subjects; messagetrace carries no attachment fields.
- R2: "RE: Splunk service needs a restart" (09:47:48Z) proven attachment-free; Bud's MIME attachments: pwned.jpg (10:24:29Z), Employee New Hire Dates.xlsx (11:11:17Z).
- R3: Exchange audit = admin cmdlets; FilePreviewed = birthday/beer files; discovered structured attach_* fields + full MIME `content` in stream:smtp.
- R4: Full 11-event attachment inventory; both Bud bodies read — pwned.jpg thread is Fyodor banter, xlsx is HR; messagetrace sizes confirm no other Bud attachment.
- R5: Traced pwned.jpg origin — BTUN-L downloaded it from temp-e.net/files/incoming/hoffa/ at 10:22:47Z, 2 min before emailing.
- R6: Sysmon puts pwned.jpg on disk on both endpoints; recipient opened it twice; PowerPoint ran later but is unlinked.
- R7 (this round): second HTTP event is a flow aggregate, not a new fetch; every Bud thread body now read; chart-type vocabulary returns 0 events dataset-wide.

## This round
### What I ran
- stream:http "pwned" full-raw extraction -> 10:23:37Z event is an aggregate of the 10:22:47Z flow (same flow_id/uri/bytes); download referrer = bing.com, content-type image/jpeg
- stream:smtp "pwned.jpg" text/html extraction -> Word CSS boilerplate only, no img alt/caption
- "Malware Alert Text.txt" body -> generic malware-stripped notice, unrelated
- "RE: Splunk service needs a restart" bodies (5 events) -> UBA install request + reply-all banter, no chart mention
- "IoT brewery stuff" body -> IoT home-brewing product question
- "FW: Bruce Gist" bodies (4 events) -> Bruce account deactivation
- (stream:smtp OR stream:http) chart-type vocabulary search -> 0 events

### What it means
NOT_FOUND for the visualization type. The artifact chain is complete and verified end-to-end (bing.com image search -> temp-e.net download -> outbound attachment -> on-disk on both endpoints), but the image's content exists only as base64 in MIME and as HTTP response bytes. Every Bud thread body has now been read in full; none describes the image or names a chart. The literal two-word chart vocabulary (line/column/pie/area/bar/scatter chart) returns zero events in mail and web feeds. I did not decode the image and will not guess a chart type. The attachment half of the question is solved (pwned.jpg); the visualization half is not answerable from the indexed text evidence available to me.

## Ruled out
- Second

_[truncated at 400 words]_

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
