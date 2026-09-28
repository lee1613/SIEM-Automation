# s1 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=5_
**Scope:** sourcetype=o365:management:activity | fields=Operation, UserId, SourceFileName, SiteUrl, ObjectId, SourceRelativeUrl, ClientIP, UserAgent
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: located upload feed (7 FileUploaded + 1 FileSyncUploadedFull in o365); literal "Taedonggang" absent from o365/code42/smtp/http/dns.
- R2 (this): opened the upload population, attributed the Taedonggang persona, enumerated its 4 uploaded files; confirmed O365 carries no file content.

## This round
### What I ran
- Operation=FileUploaded OR FileSyncUploadedFull | stats by all fields -> 8 events; 4 belong to the Taedonggang session.
- | stats count by ClientIP, UserId, UserAgent, Operation -> bgist@froth.ly sessions from 104.207.83.63/23.101.160.30/157.97.121.5 all run NaenaraBrowser/3.5b4 (ko-KP, North Korean Red Star OS) = Taedonggang persona.
- Taedonggang-IP file profile -> 25 events: FolderCreated "Birthday Pictures", 4 uploads, AnonymousLinkCreated/Shared .lnk used from 7 external IPs.
- sample_events blargh.tgz/stout.png/morebeer.jpg + fieldsummary -> O365 events are metadata-only; no size or content fields exist.

### What it means
NOT_FOUND for the word itself, but the question's first half is solved: Taedonggang = bgist@froth.ly via NaenaraBrowser, and its uploads are BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, morebeer.jpg, stout-2.jpg, stout.png in Documents/Birthday Pictures. The .lnk is a shortcut (cannot render fonts), so the oversized-font word lives in one of the three "images" — one is almost certainly HTML masquerading as an image. O365 cannot say which: this sourcetype has no content or size fields. Content recovery must move to stream:http POST bodies, aws:s3:accesslogs, code42:security, WinHostMon, or the SMTP email that carried the anonymous link.

## Ruled out
- fyodor blargh.tgz, ghoppy HomeBrewingGuide.pdf, mkraeusen GABF deck, pcerf Beer styles.pptx - normal Office/SkyDrive UAs, not the Taedonggang session.
- BRUCE BIRTHDAY HAPPY HOUR PICS.lnk as the font-bearing file - .lnk is a shortcut, not a rendered document.
- o365:management:activity as a content source - fieldsummary shows 125 fields, all metadata.

## Open questions for SH
- Can you widen my scope to stream:http / aws:s3:accesslogs / code42:security / stream:smtp so I can recover the bytes of morebeer.jpg, stout-2.jpg, stout.png and identify the HTML-masquerading one?
- Is the SMTP email that distributed the anonymous link in scope? Its body may quote the file's content directly.