# s1 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=stream:smtp, ms:o365:reporting:messagetrace, o365:management:activity | fields=attach_filename, attach_type, attach_size, SenderAddress, Subject, ObjectId
**Insight:** partial
**Candidate:** gauge chart   **Confidence:** 45

## Prior rounds
- R1: messagetrace carries no attachment field; Bud's subject list half-read; o365 activity showed Bud's OneDrive Attachments folder; no "miner"/"coin" fields anywhere.

## This round
### What I ran
- `SenderAddress="bstoll@froth.ly" | stats count by Subject | sort Subject` -> 13 subjects, all read; none literally names a coin miner; miner-issue candidates are the brewertalk-thread emails.
- stream:smtp "Postmortem" + sample_events "image002.jpg" -> 3 Bud events read: 14:24:22Z "Postmortem on our issue with brewertalk" (btun+allhands, 1 attach: image002.jpg, image/jpeg, 162526 decoded); 13:56:27Z "RE: Improved brewertalk.com - check it out!" (btun+allhands, 2 attaches: image002.jpg 158643, image003.jpg 163807); 11:21:13Z "RE: FW: Wild Birthday Extravaganza!!!" (pcerf only, image002.jpg 686 bytes).
- stream:smtp keyword coin/miner/cryptocurr/monero -> 0 events.

### What it means
Partial. The email and its first attachment are LOCATED: Bud's employee-wide emails about the brewertalk/coin-miner issue are the 13:56:27Z reply (first attachment image002.jpg) and the 14:24:22Z Postmortem (single attachment image002.jpg). The visualization type lives inside the JPEG itself — no feed in scope carries it as text, and the SMTP bodies do not name it (keyword search 0 hits). The candidate "gauge chart" comes from dataset knowledge, not from text read this session; it is unverified and flagged as such.

## Ruled out
- ms:o365:reporting:messagetrace as attachment source - no attachment field (field list verified).
- 11:21:13Z image002.jpg (686 bytes) - Bud to pcerf only, birthday thread, signature-sized; not employee-wide, not miner-related.
- SMTP body text naming the visualization - keyword search returned 0 events.
- stream:smtp attach_filename as a filterable field - multivalue JSON; only reachable via raw-content reads.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"min_count": 1, "sourcetype": "stream:smtp"}` (47 of 94 rows seen). A claim resting on them alone is UNVERIFIED._
