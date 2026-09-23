# s2 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=8_
**Scope:** sourcetype=stream:smtp, osquery:results, symantec:ep:agent:file | source=stream:smtp | fields=src_user, flow_id, attach_filename{}, attach_size{}, attach_content{}, content[]
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 85

## Prior rounds
- R1-2 (s1, retired for transport failure): stream:smtp + O365 surfaced Bud employee-wide brewertalk emails at 13:56:27Z and 14:24:22Z; ordering and visualization type unsettled.
- R3 (mine): re-established Bud's 4 attachment emails from stream:smtp; found an earlier 13:50:47Z employee-wide email with image001.jpg; refuted p2; image unreadable.
- R4 (this): read both email bodies; pinned the qualifying email and attachment; read_image could not extract the base64 JPEG.

## This round
### What I ran
- stream:smtp "Splunk" | stats by flow_id -> 11 flows; among Bud's, only 8ff70a37 (13:56:27Z) matches
- rex window around "Splunk" in flow 8ff70a37 -> 1 row: "Wow Billy. I did find the issue! Look at the Splunk chart below - I saw some instances spin up... CPU... spiked to 100%!... [cid:image002.jpg@01D4247D.2394E720]"
- rex body of flow 2a2e1c18 (13:50:47Z) -> 1 row: "I haven't figured it out yet...but check out the metrics store search below.... [cid:image001.jpg@01D4247C.58AEEAB0]"
- read_image on flow 8ff70a37, image002.jpg -> "No image found"; with extract_spl (mvindex 'attach_content{}') -> "returned no events"; eval/mvcount probes failed (field not search-time extracted)

### What it means
NOT_FOUND for the visualization kind: it sits inside a base64 JPEG no available route rendered. The qualifying email is now pinned by body text, not assumption: the 13:56:27Z email is Bud announcing he found the issue and pointing to "the Splunk chart" (image002.jpg); the earlier 13:50:47Z email is pre-discovery and its image001.jpg is a metrics store search, so it does not illustrate the coin miner.

ARTIFOLD + MISSING CAPABILITY (per SH's framing): artifact = image002.jpg, first attachment (attach_filename{} index 0, 217092 bytes encoded, base64 in attach_content{}) of stream:smtp flow 8ff70a37-b52e-4810-8203-b00a8d9d8aeb, 2018-08-20 13:56:27Z UTC, "RE: Improved brewertalk.com - check it out!", to btun@froth.ly + allhands@froth.ly. Missing capability: decoding/rendering the base64 JPEG — read_image could not locate it in the raw JSON, and extract_spl isolating attach_content{} returned no events because the braced field is not usable at search time. Next-round fix: extract_spl with | stats values('attach_content{}') as img, or a rex slice of _raw between the image002.jpg MIME headers. Unsearched: osquery:results and symantec:ep:agent:file for endpoint copies of image002.jpg.

Contextual constraint only (not submitted as the answer): the chart shows instances spinning up and CPU at 100% — a time-series chart; no text states the exact kind.

## Ruled out
- 13:50:47Z email / image001.jpg as the illustrative email — body read in full: Bud pre-discovery, image is a metrics store search
- 11:21:13Z email (flow ac25c1c0) — single recipient, birthday thread
- 14:24:23Z postmortem email — later than the qualifying one
- Email body text as the source of the kind — read in full for both candidates; says only "the Splunk chart"

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p4 - amend or settle that one. The text you sent was discarded: "Bud's first email to Frothly employees that illustrates the coin miner issue is "
- coverage premise not filed: you already have an open coverage premise p3 - amend or settle that one. The text you sent was discarded: "The visualization kind inside image002.jpg can be read only from: (a) read_image"
- p4 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
