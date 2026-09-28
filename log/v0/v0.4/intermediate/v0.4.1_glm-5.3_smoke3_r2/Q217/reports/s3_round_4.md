# s3 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=9_
**Scope:** sourcetype=stream:smtp + ms:o365:management | fields: attach_filename, From, To, Subject, timestamp, Operation, UserId, ObjectId, SourceFileName
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: mail feeds mapped; o365:management:activity has no pcerf mail ops; ess_content_importer/ms:aad:signin dead ends; messagetrace metadata only.
- R2: stream:smtp carries full MIME; "Malware Alert Text.txt" belongs to Bruce Gist; Bud's postmortem found with single inline attachment image002.jpg.
- R3: exhaustive Bud coverage (4 sent messages); postmortem body unread (encoded); ms:o365:management still unqueried at cap.

## This round
### What I ran
- ms:o365:management | stats by Operation,Workload -> 39 rows: no message-level Exchange audit; only admin ops, OneDrive/SharePoint file ops, eDiscovery.
- PreviewItemRendered raw (fyodor, 11:29Z) -> eDiscovery preview of "Newsfeed", not the postmortem.
- FileUploaded list -> 7 rows, no Bud screenshot files.
- Postmortem text/plain body extracted and read (base64 visible in raw): names the "coinminer", 100% CPU, bucket cleanup — confirms it is the coin-miner email; quoted thread shows "check out the metrics store search below.... [cid:image002.jpg@01D42481.0AB60870]".
- 13:56:27Z reply body read: CPU spike + "malicious code got into our forums" with [cid:image002.jpg]; 13:50:47Z reply body read: same "metrics store search" phrasing with image001.jpg.
- Keyword search of whole feed for chart/graph/dashboard/visualization/metrics store -> only the two Bud replies, matching "metrics store" only.

### What it means
The email and its first attachment are fully established: Bud's postmortem to btun + allhands, 14:24:22Z, single inline attachment image002.jpg illustrating a Splunk "metrics store search". But no mail-side text names the visualization kind, and ms:o365:management carries no message-level audit that could add attachment detail. The answer lives only in the JPEG's pixels, which mail/activity feeds cannot reveal. Per instruction, I do not invent a two-word guess.

## Assumptions
- Coverage: stream:smtp Bud messages — VERIFIED complete (4 events). Postmortem body — VERIFIED read (base64 decoded by inspection). ms:o365:management — VERIFIED searched (39 operation types, no message audit; eDiscovery preview = "Newsfeed"; no Bud uploads). Visualization vocabulary in any body — VERIFIED absent (keyword search over whole feed).
- Selection: postmortem chosen — only Bud message naming the coinminer and addressed to all employees — VERIFIED by decoded body and complete Bud listing.
- Premise: PCERF-L window is EDT — UNVERIFIED (14:24:22Z send fits 10:24:46 anchor to ~24 s; hint only, no open event found).
- Premise: image002.jpg is the first/only attachment — VERIFIED for the captured MIME (only filename in the event); the original message could not be cross-checked because no Exchange message audit exists.

## Ruled out
- "Malware Alert Text.txt" — Bruce Gist's financial-plan email.
- Bud's other three stream:smtp messages — birthday/brewertalk replies, not the incident email.
- ms:o365:management as a source of attachment names/ordering — no message-level Exchange audit exists in the feed.
- Body-text naming of the visualization — no chart/graph/dashboard/visualization word in any body; only "metrics store search".

## Open questions for SH
- The remaining gap is image content: image002.jpg's base64 blob sits in the postmortem stream:smtp event (and the 13:56:27Z reply). Is there a scope that can decode/view it, or an endpoint/OneDrive copy of the screenshot to pivot on?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
