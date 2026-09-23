# s2 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=7_
**Scope:** sourcetype=stream:smtp | flow_id=8ff70a37-b52e-4810-8203-b00a8d9d8aeb | fields=attach_filename{}, attach_size{}, _raw, content[]
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 85

## Prior rounds
- R1-2 (s1, retired for transport failure): stream:smtp + O365 surfaced Bud's employee-wide brewertalk emails at 13:56:27Z and 14:24:22Z; ordering and visualization kind unsettled.
- R3 (mine): re-established Bud's 4 attachment emails; found an earlier 13:50:47Z employee-wide email (image001.jpg); refuted p2.
- R4 (mine): read both bodies — 13:56:27Z: "I did find the issue! Look at the Splunk chart below" (image002.jpg); 13:50:47Z: pre-discovery, metrics store search (image001.jpg); first read_image attempt failed.
- R5 (this): pinned the artifact; three further extraction strategies against the base64 JPEG; none rendered it.

## This round
### What I ran
- read_image extract_spl (rex on "attach_content":[) -> "returned no events"
- searchmatch probes on flow 8ff70a37 -> raw holds image002.jpg and JPEG magic /9j/4AAQSkZJRg; the "attach_content" hit is actually attach_content_decoded_md5_hash
- rex structure probes -> base64 begins as JSON string "/9j/…" right after the image002.jpg MIME headers (Content-ID <image002.jpg@01D4247D.2394E720>, base64)
- read_image extract_spl (lazy regex to MIME boundary) -> match_limit exceeded
- read_image extract_spl (negated-class "\"(?<img>/9j/[^\"]+)\"") -> extracted 5 base64 chunks (1840…1440 chars, ~9KB total vs attach_size 217092) but "No image found"

### What it means
NOT_FOUND for the visualization kind. The artifact is pinned and its payload exists in the indexed raw, but no available route rendered it: read_image reported "No image found" on every strategy, and only ~9KB of the 217092-byte encoded payload is retrievable as JSON string elements — the indexed raw appears split/truncated across the flow's 5 events, and the tool cannot reassemble or decode it.

ARTIFACT (per SH's framing): image002.jpg — first file attachment (attach_filename{} index 0, attach_size 217092 bytes encoded) of stream:smtp flow 8ff70a37-b52e-4810-8203-b00a8d9d8aeb, 2018-08-20 13:56:27Z UTC, "RE: Improved brewertalk.com - check it out!", bstoll@froth.ly → btun@froth.ly + allhands@froth.ly; body: "Wow Billy. I did find the issue! Look at the Splunk chart below … [cid:image002.jpg@01D4247D.2394E720]".
MISSING CAPABILITY: decoding/rendering (OCR) of the base64 JPEG payload.

## Ruled out
- 13:50:47Z email / image001.jpg as the illustrative email — body read in full: Bud pre-discovery, image is a metrics store search
- attach_content{} as a search-time field — not extracted; the raw match is attach_content_decoded_md5_hash
- read_image via mvindex, lazy-regex and negated-class extraction — no image rendered on any strategy
- email body text as the source of the kind — read in full for both candidates; says only "the Splunk chart"

Untried by me (in scope; ran out of calls): osquery:results and symantec:ep:agent:file for endpoint copies of image002.jpg; the text/html part of the 13:56:27Z email (possible alt= text); concatenating the base64 chunks across the flow's 5 events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p4 - amend or settle that one. The text you sent was discarded: "Bud's first email to Frothly employees that illustrates the coin miner issue is "
