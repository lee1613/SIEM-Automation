# s3 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=12_
**Scope:** sourcetype=stream:smtp (searched exhaustively for Bud) + ms:o365:management (NOT searched — cap hit) | fields: attach_filename, From, To, Subject, timestamp
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: mail feeds mapped; o365:management:activity has no pcerf mail ops (OneDrive only, 13:05Z, attacker IP); ess_content_importer = errors; ms:aad:signin empty; messagetrace = metadata only.
- R2: stream:smtp carries full MIME with attach_filename; "Malware Alert Text.txt" belongs to Bruce Gist, not Bud; Bud's postmortem email found with single inline attachment image002.jpg.

## This round
### What I ran
- stream:smtp | rex From | search from="Bud Stoll <bstoll@froth.ly>" + Subject/timestamp/attach rex -> 4 events, complete: birthday reply (11:21Z, image002.jpg), two brewertalk replies (13:50Z image001.jpg; 13:56Z image002+003.jpg), Postmortem (14:24:22Z, image002.jpg).
- Postmortem raw re-read: To btun + allhands@froth.ly, X-MS-Has-Attach: yes, only MIME filename image002.jpg (inline jpeg, 222408 B).
- Body extraction: rex windows around "miner" -> 0; "coin" -> 0; post-Subject window -> only Exchange diagnostic headers; three text/plain slice regexes -> 0.

### What it means
Exhaustive Bud coverage settles the selection: the postmortem is Bud's only message to Frothly employees about the brewertalk/coin-miner incident, and its only captured attachment is image002.jpg. But the visualization type inside that JPEG is not determinable from mail metadata: the body text is encoded (the words "coin"/"miner" appear nowhere in the raw), my regex slices of the JSON-escaped MIME failed, and ms:o365:management was never reached. No two-word value.

## Assumptions
- Coverage: stream:smtp Bud-sent messages — VERIFIED complete (4 events, full listing). ms:o365:management — NOT searched (UNVERIFIED), may carry Exchange audit naming attachments for this message. Postmortem body text — UNREAD (encoded; extraction failed).
- Selection: postmortem chosen — only Bud message about the incident and only one addressed to allhands; other 3 Bud messages are birthday/brewertalk replies — VERIFIED by complete listing.
- Premise: PCERF-L window is EDT — UNVERIFIED (14:24:22Z send fits 10:24:46 anchor to 24 s; hint only).
- Premise: image002.jpg is the first/only attachment — VERIFIED for the stream:smtp capture; UNVERIFIED for the original message (audit feed unqueried).
- Caveat: round-2's coarse listing showed extra Bud-subject rows absent from this round's from-filtered search — likely partial captures where the first "From: " sits in quoted reply text; UNVERIFIED.

## Ruled out
- "Malware Alert Text.txt" as Bud's attachment — Bruce Gist's email.
- Bud's other three stream:smtp messages — birthday/brewertalk replies, not the incident email.
- Keyword search of the postmortem body — "coin"/"miner" absent from raw; body is encoded.

## Open questions for SH
- Authorize ms:o365:management query next round (Exchange audit for the postmortem's MessageId/recipients) — it is the last unsearched mail/activity feed and may name attachment ordering?
- If the body must be read, is a base64-decode pivot on the postmortem's text part acceptable within mail scope, or does image002.jpg content require an out-of-scope pivot?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
