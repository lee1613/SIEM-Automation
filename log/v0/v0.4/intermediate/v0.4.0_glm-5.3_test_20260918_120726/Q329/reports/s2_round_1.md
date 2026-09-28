# s2 - Q329 - Round 1
_stamped by runner: rounds_remaining=5 novel_spl=1_
**Scope:** sourcetype=o365:management:activity, stream:http, stream:smtp, symantec:ep:*, WinEventLog | fields=ObjectId, SourceFileName, ListItemUniqueId, subject, src
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- (Round 1) Confirmed the four artifacts exist in bgist@froth.ly's OneDrive "Documents/Birthday Pictures" via o365:management:activity metadata (FileAccessed/FilePreviewed); captured ListItemUniqueIds for each file.
- (Round 1) Confirmed the .lnk was downloaded to MalloryKraeusen (MKRAEUS-L) and BudStoll (BSTOLL-L) Edge download folders via Symantec AV submission + WinEventLog 4688 events.
- (Round 1) Eliminated stream:http as carrier of the upload bytes: zero events match morebeer, stout, or Naenara.
- (Round 1) Eliminated stream:smtp as direct carrier: only 3-4 "Quarentined email" notification flows from Microsoft EOP IPs; no filename tokens present.

## This round
### What I ran
- get_raw_events keyword=morebeer / stout.png / "BRUCE BIRTHDAY" -> 10 events each; all o365 metadata or AV/process-creation logs, no file bytes.
- get_raw_events sourcetype=stream:http keyword=morebeer|stout|Naenara -> 0 events.
- get_raw_events sourcetype=stream:smtp keyword=stout -> 4 events, all subject="Quarentined email"; keyword=stout.png/morebeer.jpg -> 0 events.
- get_sourcetype_fields stream:smtp -> confirmed body-bearing fields exist (content_type, server_response) but no attachment-content field surfaced.

### What it means
NOT_FOUND: no feed I reached contains the uploaded files' rendered content, so the "larger-font word" is unrecovered. The metadata chain (upload -> OneDrive -> .lnk download) is fully mapped, but the bytes themselves were not in stream:http or stream:smtp.

## Ruled out
- stream:http - no events matching any target filename or the NaenaraBrowser user-agent string.
- stream:smtp - only EOP quarantine notifications; no attachment bytes or filenames in bodies.
- o365:management:activity - metadata only (s1's prior scope), confirmed no content fields.

## Open questions for SH
- Should the next worker prioritize symantec:ep:packet:file (packet-level file capture) and code42:api (endpoint backup) for the actual file bytes?
- The 3 "Quarentined email" SMTP flows (~2018-08-20 09:16 UTC) are the strongest unexplored lead — is a messagetrace/quarantine retrieval in scope for this question?
- Is the intended answer recoverable from an S3 staging bucket (aws:s3:accesslogs) tied to the Taedonggang exfil path?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
