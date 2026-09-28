# s2 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** sourcetype=stream:smtp | source=stream:smtp | fields=_raw, attach_filename, attach_type, attach_content, content
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
None — this is round 1 on the SMTP scope.

## This round
### What I ran
- get_source_types / get_sources / get_sourcetype_fields(stream:smtp) -> feed exists: 879 events, one source (stream:smtp); attachments live as raw-JSON arrays (attach_filename/attach_type/attach_content, base64).
- get_raw_events keyword=btun@froth.ly (5 events) -> From identities in feed: "Billy Tun <btun@froth.ly>" (Bud, matches SH's established identity) and "Bud Stoll <bstoll@froth.ly>"; one event showed the attach_* array structure.
- `attach_filename=*` field filter -> 0 events (multivalue field; unreachable as a filter).
- `sourcetype=stream:smtp "attach_filename"` | stats by _raw, sorted by earliest time -> 11 attachment-bearing events total.
- rex extraction of filename/type/from/subject over those 11 -> only first 2 rows returned (truncated, "showing 2 of 11"): (1) Bruce Gist, "Malware Alert Text.txt", application/octet-stream, subj "Draft Financial Plan for Brewery FY2019", epoch 1534758914; (2) Billy Tun <btun@froth.ly>, "pwned.jpg", image/jpeg, subj "RE: meeting with F" to Peat Cerf, epoch 1534760669.

### What it means
NOT_FOUND for the visualization type. SMTP exposes the attachment artifact (filename, MIME, size) but no field names the Splunk visualization depicted — that must come from body prose or the base64 image, neither of which I read. Bud's earliest attachment in this feed is pwned.jpg, but its subject ("RE: meeting with F") is not self-evidently the coin-miner illustration, and 9 later attachment events remain unread; the miner illustration may be among them. No value is submittable: I hold an attachment candidate, not the two-word visualization answer, and I will not guess it.

## Ruled out
- Bruce Gist "Malware Alert Text.txt" — earliest attachment in the feed, but sender is bgist@froth.ly, not Bud.
- `attach_filename=*` as a field filter — 0 results; attachment data is reachable only via raw-text search on "attach_filename".
- O365 / messagetrace feeds — retired by SH this round, out of scope.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:smtp"}` (47 of 94 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:smtp "attach_filename" | rex field=_raw "\"attach_filename\…` (2 of 11 rows seen). A claim resting on them alone is UNVERIFIED._
