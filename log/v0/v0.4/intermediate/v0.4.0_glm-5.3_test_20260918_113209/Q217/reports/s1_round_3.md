# s1 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=10_
**Scope:** sourcetype=ms:o365:reporting:messagetrace, stream:smtp, o365:management:activity | fields=SenderAddress, RecipientAddress, Subject, DateReceived, content_type, _raw, Operation, ObjectId, attach_filename (newly discovered)
**Insight:** FOUND
**Candidate:** pwned.jpg   **Confidence:** 50

## Prior rounds
- R1: Mapped 102 sourcetypes; confirmed Bud=btun@froth.ly; 13 outbound subjects in messagetrace; no attachment fields in that feed; "coin" absent from stream:smtp.
- R2: Proved "RE: Splunk service needs a restart on your workstations" (09:47:48Z) is multipart/alternative — NO attachment; Bud's only outbound MIME attachments: pwned.jpg (10:24:29Z) and Employee New Hire Dates.xlsx (11:11:17Z).
- R3 (this round): Exchange-workload audit and FilePreviewed events contain no attachment or miner artifacts; discovered structured attach_* fields + full MIME `content` field in stream:smtp.

## This round
### What I ran
- o365:management:activity Operation="FilePreviewed" -> 14 events: all Birthday Pictures jpgs and beer documents; no pwned.jpg, no miner files
- o365:management:activity Workload=Exchange -> 9 events: admin cmdlets only (New-DistributionGroup, New-MailboxSearch, New-TransportRule); no mail-content records
- stream:smtp ("miner" OR "mining" OR "monero" OR "cryptocurrency" OR "bitcoin") -> 0 events; miner vocabulary absent from journaled mail
- stream:smtp "btun@froth.ly" | head 1 | substr(_raw,1,900) -> revealed attach_filename/attach_type/attach_size/attach_disposition/attach_transfer_encoding structured fields and full MIME in `content` (sample: 1534778082419.png, image/png, inline — From ghoppy, not Bud)
- attach_filename="*" enumerations -> 0 rows; field not directly filterable (multivalue JSON array)

### What it means
FOUND (attachment half, still unconfirmed as the miner thread): pwned.jpg remains the only viable candidate for Bud's first attachment to a Frothly employee — "RE: meeting with F" to pcerf@froth.ly at 10:24:29Z. Its miner linkage is inferred (name "pwned", timing 37 min after the restart thread, Bud's Splunk-admin role), not proven from body text. The visualization type is NOT established: the jpg is base64 inside the MIME `content` field and I found no text anywhere naming the chart. The structured attach_* fields are the unexploited path — they were invisible in the field summary and unfilterable by my syntax, so an enumeration via rex/mvexpand is the highest-value next query.

## Ruled out
- o365:management:activity as an attachment/miner-content source - FilePreviewed shows only birthday/beer files; Exchange-workload events are admin cmdlets only
- "RE: Splunk service needs a restart on your workstations" as attachment carrier - multipart/alternative, 5 journaled copies, no attachment part
- Miner keywords in stream:smtp - 0 events for miner/mining/monero/cryptocurrency/bitcoin
- 1534778082419.png (inline png, 15:19:34Z) as Bud's attachment - From is ghoppy@froth.ly

## Open questions for SH
- Can you confirm "RE: meeting with F" (Bud -> pcerf, 10:24:27Z) is the

_[truncated at 400 words]_

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
