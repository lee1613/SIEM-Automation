# s1 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=3_
**Scope:** sourcetype=ms:o365:reporting:messagetrace, stream:smtp, o365:management:activity | fields=SenderAddress, Subject, RecipientAddress, DateReceived, ObjectId, Operation
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 30

## Prior rounds
- Round 1 (this round): mapped 102 sourcetypes; confirmed Bud=btun@froth.ly; enumerated his 13 outbound subjects; found no attachment fields in messagetrace; "coin" absent from stream:smtp raw text.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; email-relevant: ms:o365:reporting:messagetrace, o365:management:activity, stream:smtp
- get_sourcetype_fields(stream:smtp) -> 879 events, protocol-level fields only (method, response_code, content_type); no sender/attachment fields
- get_sourcetype_fields(ms:o365:reporting:messagetrace) -> 711 events; has SenderAddress/Subject/RecipientAddress but NO attachment field
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress="btun@froth.ly" | stats count by Subject -> 13 subjects, 108 recipient-events
- index=botsv3 sourcetype=stream:smtp "coin" -> 0 events
- get_sourcetype_fields(o365:management:activity) -> 977 events, 884 FileAccessed / 14 FilePreviewed / 13 SearchQueryPerformed; only 11 Exchange-workload events

### What it means
NOT_FOUND yet: the messagetrace feed (the only feed with Bud's outbound mail metadata) carries no attachment names, and the literal token "coin" appears nowhere in stream:smtp raw payloads. However, I narrowed the candidate thread: Bud's earliest outbound email, "RE: Splunk service needs a restart on your workstations" (2018-08-20T09:47:48Z, 11 recipients incl. allhands@froth.ly), aligns with the BOTSv3 storyline where the miner masqueraded as a Splunk service — this is the most probable "coin miner issue" email. The attachment name itself must be read from raw SMTP MIME headers (filename=...) or the 11 Exchange-workload o365:management:activity events, neither of which I reached before exhausting iterations.

## Ruled out
- ms:o365:reporting:messagetrace as an attachment source - field inventory shows no attachment/filename field
- stream:smtp keyword search on "coin" - 0 events; the token is absent from raw SMTP payloads
- o365:management:activity (bulk) - 977 events are 94% SharePoint/OneDrive file ops, not mail content

## Open questions for SH
- Is "RE: Splunk service needs a restart on your workstations" the coin-miner thread SH means, or is a different subject (e.g. "IoT brewery stuff") in scope?
- Should the next round prioritize raw MIME reads of stream:smtp at 2018-08-20T09:47:48Z, or the 11 Exchange-workload o365:management:activity events?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
