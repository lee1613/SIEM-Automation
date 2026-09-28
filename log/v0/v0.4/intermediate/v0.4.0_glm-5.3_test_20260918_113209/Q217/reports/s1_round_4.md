# s1 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=8_
**Scope:** sourcetype=ms:o365:reporting:messagetrace, stream:smtp, o365:management:activity | fields=SenderAddress, RecipientAddress, Subject, DateReceived, content_type, _raw, content, attach_filename, attach_type, attach_size, Operation, ObjectId
**Insight:** FOUND
**Candidate:** pwned.jpg   **Confidence:** 40

## Prior rounds
- R1: Mapped 102 sourcetypes; Bud=btun@froth.ly; 13 outbound subjects in messagetrace; that feed has no attachment fields.
- R2: "RE: Splunk service needs a restart on your workstations" (09:47:48Z) proven multipart/alternative — NO attachment; Bud's MIME attachments: pwned.jpg (10:24:29Z), Employee New Hire Dates.xlsx (11:11:17Z).
- R3: Exchange-workload audit = admin cmdlets only; FilePreviewed = birthday/beer files; discovered structured attach_* fields + full MIME `content` in stream:smtp.
- R4 (this round): enumerated the complete 11-event attachment inventory; read both Bud attachment bodies; messagetrace size audit confirms no other Bud email carries an attachment.

## This round
### What I ran
- attach_filename rex enumeration on stream:smtp -> 11 attachment events; Bud owns exactly 2: pwned.jpg @10:24:29Z, Employee New Hire Dates.xlsx @11:11:17Z
- Body read of pwned.jpg email -> text/plain holds only the quoted chain (Peat: "meeting with Fyodor... phoniest Russian accent... shrimpchips"); Bud's reply is attachment-only, no body text
- Body read of xlsx email -> "Sounds like a great idea. Here's the start dates..." — HR thread, not miner
- Messagetrace Size audit -> all other Bud emails are 13-23KB (no attachment); only 89446B (pwned.jpg) and 31176B (xlsx) carry attachments

### What it means
FOUND (attachment half): pwned.jpg is structurally the only possible answer — Bud's first and only viable attachment to a Frothly employee. Miner linkage is UNCONFIRMED: the thread is banter about Fyodor (whose account is the compromised one), and Bud — the Splunk admin — replies with no text, just "pwned.jpg", which reads as a compromise screenshot. The visualization type is NOT established: the jpg is base64 in MIME, unreadable as text, and nothing in scope names a chart type. The two-word chart answer requires either the HTML part's img alt/caption text or endpoint telemetry for pwned.jpg, both outside what I reached.

## Ruled out
- Employee New Hire Dates.xlsx - HR thread ("start dates"), chronologically second
- "RE: Splunk service needs a restart on your workstations" as attachment carrier - multipart/alternative, no attachment part
- Miner vocabulary in stream:smtp - 0 events for miner/mining/monero/cryptocurrency/bitcoin/coin
- o365:management:activity as attachment source - FilePreviewed = birthday/beer files; Exchange events = admin cmdlets
- 1534778082419.png - from ghoppy@froth.ly / hyunki1984@naver.com, not Bud

## Open questions for SH
- Confirm "RE: meeting with F" (Bud→pcerf,

_[truncated at 400 words]_

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
