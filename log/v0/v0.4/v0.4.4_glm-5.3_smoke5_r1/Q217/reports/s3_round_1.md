# s3 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=8_
**Scope:** index=botsv3 sourcetype=stream:smtp (event location only); endpoint/file-security sources not yet reached
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Inherited (retired SMTP senior): first qualifying attachment = image002.jpg in Bud's 13:56:27Z "RE: Improved brewertalk.com - check it out!" (flow 8ff70a37); SMTP attach_content not renderable; p2/p4 refuted; p3 open.
- R1 (mine, this round): failed to resolve the given flow_id; confirmed the subject exists (7 events); endpoint/file search not started.

## This round
### What I ran
- `sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb"` -> 0 events.
- `sourcetype=stream:smtp "Improved brewertalk.com"` and `... brewertalk` -> 0 events each (free text unsearchable here).
- `sourcetype=stream:smtp earliest=08/20/2018:13:50:00 latest=08/20/2018:14:00:00` -> 0 events (no stream:smtp in that window as the search head reads time).
- `sourcetype=stream:smtp | stats count` -> 879 events; `| top limit=20 subject` -> 137 carry a subject; "RE: Improved brewertalk.com - check it out!" = 7 events.

### What it means
NOT_FOUND — I never reached the endpoint/file-security scope SH directed; the round went to locating the target event, and all three locators I was handed failed in ways I have now characterized rather than assumed. (1) The briefing's flow_id resolves to zero events and cannot be a locator. (2) Free-text terms return 0 in stream:smtp even though the subject exists as a field value — field filters are mandatory. (3) No stream:smtp events are indexed in the Aug 20 13:50–14:00 window under the search head's time interpretation; prior evidence showed a Sep 15 2018 MIME date on a sibling flow, so _time and MIME Date diverge here and the claimed 13:56:27Z _time is unconfirmed. The one solid result: the subject filter is a working locator and cuts 879 events to 7 — the complete candidate set for the target email. No body text, no image, and no endpoint record has been read by anyone, so no two-word visualization kind can be stated.

## Ruled out
- flow_id 8ff70a37-b52e-4810-8203-b00a8d9d8aeb as a locator — 0 events in stream:smtp.
- Free-text/phrase search on stream:smtp ("brewertalk", "Improved brewertalk.com") — 0 events despite the subject existing; tokenization does not cover these terms.
- Aug 20 13:50–14:00 (as typed) as a time locator — 0 stream:smtp events in that window.

## Next round
List the 7 subject-matching events (`subject="RE: Improved brewertalk.com - check it out!" | stats count by _time, flow_id, attachments`) to get the true flow_id/_time of the image002.jpg event; read its body with get_raw_events; then run SH's untouched deviation — symantec:ep:agent:file, osquery:results, and a cross-sourcetype "image002" pass for a saved endpoint copy or its path/metadata.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
