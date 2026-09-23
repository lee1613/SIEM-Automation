# s2 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** sourcetype=stream:smtp | source=stream:smtp | fields=src_user, flow_id, _time, attach_filename{}, attach_size{}, attach_content{}, content[]
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 65

## Prior rounds
- R1-2 (s1, retired for transport failure, not disproof): stream:smtp + O365 surfaced Bud's employee-wide brewertalk emails at 13:56:27Z (image002/003.jpg) and 14:24:22Z (image002.jpg); ordering and visualization type left unsettled; endpoint file logs unsearched.

## This round
### What I ran
- get_sourcetype_fields stream:smtp -> flow-level fields only; MIME fields absent from summary
- search_keyword "attach" -> real field names: attach_filename{}, attach_content{}, attach_transfer_encoding{}
- stream:smtp attach_filename=* -> 0 events (unbraced name does not exist)
- stream:smtp "attach_filename{}"=* by src_user -> 7 senders; bstoll@froth.ly has 4 attachment events
- Bud's 4 events by flow_id with times/sizes -> 11:21:13Z, 13:50:47Z, 13:56:27Z, 14:24:23Z UTC
- rex Subject/To/Date by flow_id -> all four emails identified (4 rows, read in full)

### What it means
NOT_FOUND for the visualization kind: it lives inside a base64-encoded JPEG, and no source I queried renders or textually describes image contents.

Ordering re-established, unambiguous under both _time and MIME Date header for the employee-wide emails:
1. 11:21:13Z "RE: FW: Wild Birthday Extravaganza!!!" -> Peat Cerf only, image002.jpg (686 B) — not employee-wide
2. 13:50:47Z "RE: Improved brewertalk.com - check it out!" -> btun@ + allhands@froth.ly, image001.jpg (226222 B) — FIRST employee-wide brewertalk-thread attachment
3. 13:56:27Z same thread -> image002.jpg + image003.jpg
4. 14:24:23Z "Postmortem on our issue with brewertalk" -> image002.jpg

This refutes p2: an earlier employee-wide email (13:50:47Z, image001.jpg) exists that the prior premise missed. Caveat: I did not read that email's body, so "illustrates the coin miner issue" rests on thread + recipients; if its body is off-topic, the first qualifying attachment is image002.jpg at 13:56:27Z.

Artifact + missing capability (per SH's framing): attachment = image001.jpg, 226222 bytes, base64 image data in attach_content{}; unreadable without image rendering/OCR. Untried avenues: body text in content[] (possible description/alt text), endpoint copies (symantec:ep:agent:file, osquery:results).

## Ruled out
- Bud 11:21:13Z email (flow ac25c1c0) — single recipient, birthday subject, 686 B image
- 14:24:23Z postmortem email — third employee-wide email, later than both candidates
- stream:smtp flow-level/summary fields — carry no image or visualization content
- attach_filename (unbraced) — nonexistent field, 0 events

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:smtp"}` (47 of 94 rows seen). A claim resting on them alone is UNVERIFIED._
