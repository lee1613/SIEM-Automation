# s3 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=4_
**Scope:** sourcetype=stream:smtp | o365:management:activity | fields=attach_filename, content, Operation, SourceFileName, UserId, ObjectId
**Insight:** partial
**Candidate:** FOUR   **Confidence:** 60

## Prior rounds
- R1: enumerated upload feeds — 7 O365 FileUploaded docs (all froth.ly users), code42/S3 uploads only tarballs, stream:http has no POSTs. NOT_FOUND, no file content reached.
- R2: O365 upload paths showed no attacker tie; pivoted to stream:smtp raw events; found the ransom email and read its attachment image.

## This round
### What I ran
- o365:management:activity Operation="FileUploaded" | stats by UserId, SourceFileName, ObjectId, SourceRelativeUrl -> 7 events, all personal OneDrive docs, no attacker indicator in any field.
- get_sourcetype_fields stream:smtp -> 879 events, 137 content-bearing; attachments live only in _raw (attach_filename is not an extracted field — stats on it returned 0).
- stream:smtp "taedonggang" | stats count -> 0 hits (p1: this feed now searched, zero).
- get_raw_events keyword=filename -> 10 attachment-bearing emails; the ransom email "All your datas belong to us" carries inline PNG 1534778082419.png (87,446 bytes decoded), original arriving 15:15Z with SPF pass from Korean IP 125.209.224.215, forwarded by ghoppy at 15:19Z.
- read_image 1534778082419.png -> Korean-webmail screenshot (검색결과 29) of a Frothly internal email (ghoppy→btun re: Bruce Gist's EA, "four, yes FOUR, layovers!!"); the word FOUR appears in the largest font size in the image.

### What it means
Partial: the ransom email is the adversary's act (external Korean origin, ransom subject, proof-of-access screenshot of a Frothly mailbox), and its inline PNG is the only attacker-associated file in scope whose content is recoverable. The largest word in that file is FOUR. The Taedonggang attribution is inferred from the ransom email's origin, not from a verified literal string, and the larger-font rendering is vision-model-attested — so this is a credible candidate, not a confirmed one.

## Ruled out
- 7 O365 FileUploaded documents as Taedonggang's files - all by froth.ly users on personal OneDrive; no attacker indicator in filename/path/site, and audit records carry no file content.
- code42:security, aws:s3:accesslogs, stream:http POST - no document uploads (R1).
- stream:smtp literal "taedonggang" - 0 hits.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:smtp"}` (47 of 94 rows seen); `get_raw_events: {"keyword": "filename", "limit": 10, "sourcetype": "stream:smtp"}` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
