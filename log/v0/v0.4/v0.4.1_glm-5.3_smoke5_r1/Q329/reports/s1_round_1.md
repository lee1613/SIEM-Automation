# s1 - Q329 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=7_
**Scope:** all of index=botsv3 (no upload event located yet); feeds queried: o365:management:activity, code42:security, access_combined, stream:http
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
- Round 1 (this round): enumerated feeds; found no "taedonggang" in O365 UserId, access_combined, or stream:http; enumerated all O365 upload events — all by internal froth.ly users.

## This round
### What I ran
- get_source_types -> 102 sourcetypes available.
- search_keyword "Taedonggang" -> 0 matches (tool matches field names, not values — my error, corrected by direct SPL).
- o365:management:activity UserId="*taedonggang*" -> 0 events.
- o365:management:activity | stats count by UserId -> 12 UserIds (bgist, bstoll, fyodor, ghoppy, klagerfield, mkraeusen, pcerf + system/anon accounts); no Taedonggang.
- access_combined "taedonggang" -> 0 events; stream:http "taedonggang" -> 0 events.
- code42:security | stats count by files{}.fileName -> 13 filenames, none attacker-looking.
- o365:management:activity Operation="*upload*" -> 8 events, all by froth.ly employees (fyodor, bgist, pcerf, mkraeusen, ghoppy).

### What it means
NOT_FOUND: the only feed with explicit upload operations shows no Taedonggang activity, and the actor's name does not appear in the web access or HTTP stream feeds I checked. The upload event must live in a feed I have not yet searched — most likely aws:s3:accesslogs / aws:cloudtrail (object upload), stream:smtp (email attachment), or a source under a generic sourcetype I have not enumerated via get_sources.

## Assumptions
- Coverage: "files uploaded by Taedonggang" could appear as (a) O365 FileUploaded events — searched, 8 events, none by Taedonggang; (b) web-app upload POSTs in access_combined/stream:http — searched for the actor string, 0 events; (c) Code42 file events — 13 filenames enumerated, no match; (d) S3/CloudTrail object uploads — NOT YET SEARCHED; (e) SMTP attachments — NOT YET SEARCHED; (f) endpoint file-write telemetry (Sysmon/osquery/WinEventLog) — NOT YET SEARCHED. - VERIFIED for a-c, UNVERIFIED for d-f.
- Selection: no candidate selected; no upload event attributable to Taedonggang exists in the feeds searched. - VERIFIED by the queries above.
- Premise: "Taedonggang" is spelled exactly so in the data (Splunk terms are case-insensitive, so case is not a risk, but a different spelling e.g. "Taedong Gang" would be missed). - UNVERIFIED: could not test without a feed that contains the actor.

## Ruled out
- o365:management:activity as the upload feed — all 8 upload events belong to internal froth.ly users; Taedonggang is not among the 12 UserIds.
- access_combined and stream:http as feeds naming the actor — literal string search returned 0 events.
- code42:security — 13 filenames enumerated in full, no attacker upload.

## Open questions for SH
- Is Taedonggang known to be an external actor (e.g., a Gmail-based account) rather than a froth.ly employee? That would point me at stream:smtp / S3 rather than O365.
- Should I prioritize the AWS feeds (s3:accesslogs, cloudtrail) or the email path (stream:smtp attachments) next round?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
