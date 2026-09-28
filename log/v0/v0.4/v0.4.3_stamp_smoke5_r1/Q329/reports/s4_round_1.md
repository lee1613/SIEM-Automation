# s4 - Q329 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=6_
**Scope:** sourcetype=o365:management:activity, code42:security, stream:smtp | fields=Operation, SourceFileName, ObjectId, files{}.fileName, files{}.fileEventType, processOwner
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Retired senior: literal searches for Taedonggang/Taedong/TDG across feeds found no feed; no entity established.
- This round: confirmed the negative on the two richest text feeds and mapped the upload-channel telemetry.

## This round
### What I ran
- `sourcetype=o365:management:activity "taedonggang"` -> 0 events.
- `sourcetype=stream:smtp "taedong"` -> 0 events.
- `sourcetype=o365:management:activity | stats count by Operation` -> 28 rows; FileUploaded=7, FileSyncUploadedFull=1, FilePreviewed=14.
- `Operation=FileUploaded | stats count by UserId, SourceFileName, ObjectId, SiteUrl` -> 7 rows, all read: bgist (BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, morebeer.jpg, stout-2.jpg, stout.png), ghoppy (HomeBrewingGuide.pdf), mkraeusen (Frothly_GABF_Deck-2018-MK.pptx), pcerf (Beer styles.pptx) — all to the user's own OneDrive.
- `get_sourcetype_fields code42:security` -> 63 events; files{}.fileEventType UPLOAD=9, DOWNLOAD=31, SCAN=14; files{}.fileName 13 distinct (only 3 visible: frothly_html_memcached.tar.gz, OneDrive, desktop.ini); ruleName com.code42.rules.AWSPEMKeyMatch.

### What it means
No candidate word yet: I established the upload channels but have not enumerated the attacker-attributable uploads or recovered any document content. The O365 FileUploaded set is fully read and contains only Frothly-user uploads to their own OneDrive — attribution, if any, must be indirect (compromised account, most plausibly mkraeusen, unverified). The code42:security feed is the dedicated file-exfil telemetry and holds 9 UPLOAD file events whose filenames I have not yet listed — that enumeration, plus stream:http POST bodies and aws:s3:accesslogs PUTs, are the unsearched paths for the upload act. The oversized-font word itself requires document text or preview content, which I have not yet located.

## Ruled out
- Literal "taedonggang" in o365:management:activity — 0 events.
- Literal "taedong" in stream:smtp — 0 events.
- O365 FileUploaded as a directly attacker-named channel — all 7 events are Frothly users uploading to their own OneDrive (kept live only as an indirect-attribution path).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
