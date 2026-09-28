# s3 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=9_
**Scope:** sourcetype=stream:smtp (searched) + ms:o365:management (NOT searched — cap hit) | fields: attach_filename, From/Subject via rex, timestamp
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: mail/activity feeds mapped. o365:management:activity holds no pcerf mail ops (only OneDrive file ops 13:05–13:06Z from attacker IP 104.238.59.42); ess_content_importer = Splunkd errors only; ms:aad:signin empty; messagetrace fields are SenderAddress/Subject (27 events, metadata only).

## This round
### What I ran
- get_raw_events stream:smtp (3 samples) -> full MIME JSON with attach_filename arrays; premise "feed carries attachment names" VERIFIED.
- rex attach_filename over whole feed -> 7 complete attachment sets; "Malware Alert Text.txt" traced via From/Subject rex to Bruce Gist's "Draft Financial Plan for Brewery FY2019" — not Bud.
- rex From/Subject over feed -> 114 rows (50 read); all Bud Stoll subjects enumerated.
- get_raw_events "Postmortem on our issue with brewertalk" -> 1 event: Bud Stoll <bstoll@froth.ly> to Billy Tun + allhands@froth.ly, timestamp 2018-08-20T14:24:22.695685Z, attach_filename ["image002.jpg"] inline image/jpeg 222408 B.
- rex filename= max_match=0 on that event -> only image002.jpg; no other MIME filenames in the 258k-char raw.

### What it means
The coin-miner-issue email is identified with high confidence: Bud's postmortem to allhands (Frothly employees), sent 14:24:22Z — which aligns with the PCERF-L window 10:24:46–10:33:05 under a UTC-4 (EDT) reading, Peat opening 24 s after send. Its only attachment is inline image002.jpg. The Splunk visualization inside that JPEG cannot be read from metadata; the email body text was never extracted and ms:o365:management was never queried before the cap. No two-word value.

## Assumptions
- Coverage: stream:smtp searched for Bud messages and attachment names — VERIFIED (7 attachment sets, complete; postmortem event read). ms:o365:management — NOT searched (UNVERIFIED), may carry Exchange audit with AttachmentName/MessageId for the original message. From/Subject listing truncated at 50 of 114 rows — UNVERIFIED whether the unread 64 hold another Bud coin-miner email.
- Selection: postmortem chosen as the coin-miner email — it is Bud's only message to allhands about the brewertalk incident; other Bud subjects (kombucha, VPN, supplies, birthday, conference, brewertalk announcements) are unrelated — VERIFIED by subject read.
- Premise: PCERF-L anchor is UTC-4 — UNVERIFIED (14:24:22Z send vs 10:24:46 anchor is consistent but no open event found).
- Premise: "first file attachment" = image002.jpg — VERIFIED for stream:smtp's copy (only MIME filename present); UNVERIFIED whether the original message carried more attachments stream:smtp did not parse (its Received headers show replayed dates, e.g. Sep 15 2018).

## Ruled out
- "Malware Alert Text.txt" as Bud's coin-miner attachment — belongs to Bruce Gist's financial-plan email.
- Other Bud Stoll subjects in stream:smtp — none is a coin-miner-issue email to employees.
- ess_content_importer, ms:aad:signin, o365:management:activity as carriers of the message/anchor (R1).

## Open questions for SH
- Is the PCERF-L 10:24:46–10:33:05 window EDT (UTC-4)? The postmortem send at 14:24:22Z fits it to within 24 s.
- Should the next round extract the postmortem's text/plain or text/html body (rex inside the 258k raw) and query ms:o365:management for the Exchange audit of this message before any image-content pivot?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:smtp"}` (47 of 94 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:smtp | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | r…` (3 of 137 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:smtp | rex field=_raw "From: (?<from>[^\\\\]*)" | rex field…` (50 of 114 rows seen). A claim resting on them alone is UNVERIFIED._
