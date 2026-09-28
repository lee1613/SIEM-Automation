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

## What I'd tell my replacement
- Retired because: s1 completed the O365 metadata work: it identified the Taedonggang persona as bgist@froth.ly, enumerated the four uploaded files, and established that O365 contains no file content or rendering clues. Further progress now requires a different artifact class, so this senior should hand off rather than continue in a metadata-only scope.
- Scope I owned: sourcetypes=['stream:http', 'o365:management:activity', 'aws:s3:accesslogs', 'access_combined', 'osquery:results'] sources=[] fields=['user', 'src', 'dest', 'uri', 'uri_path', 'http_method', 'form_data', 'object', 'file', 'path', '_raw']
- Rounds worked: 2/8  (iterations: 16, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "Taedonggang" | stats count by sourcetype, source | sort -count
- index=botsv3 sourcetype=aws:cloudtrail | top limit=50 eventName
- index=botsv3 sourcetype=code42:security Taedonggang | stats count by fileStats{}.fileName, fileStats{}.md5, fileStats{}.sha256
- index=botsv3 sourcetype=code42:security | top limit=50 user
- index=botsv3 sourcetype=o365:management:activity ClientIP=104.207.83.63 OR ClientIP=23.101.160.30 OR ClientIP=157.97.121.5 | stats count by ClientIP, Operation, SourceFileName, SourceRelativeUrl, UserAgent | sort ClientIP, Operation
- index=botsv3 sourcetype=o365:management:activity Operation=AnonymousLinkCreated OR Operation=AnonymousLinkUsed OR Operation=SharingSet OR Operation=SiteCollectionCreated OR Operation=Set-Mailbox OR Operation=New-TransportRule OR Operation=Add-MailboxPermission OR Operation=New-MailboxSearch OR Operation=Add-RecipientPermission OR Operation=FolderDeleted OR Operation=SiteCollectionAdminAdded | stats count by Operation, UserId, SourceFileName, ObjectId, SiteUrl, ClientIP
- index=botsv3 sourcetype=o365:management:activity Operation=FileUploaded OR Operation=FileSyncUploadedFull | stats count by Operation, UserId, SourceFileName, SiteUrl, SourceRelativeUrl, ObjectId, ClientIP, Workload
- index=botsv3 sourcetype=o365:management:activity Taedonggang | stats count by Operation, UserId, SourceFileName | sort -count
- index=botsv3 sourcetype=o365:management:activity UserId=fyodor@froth.ly | stats count by Operation, SourceFileName, ObjectId, SiteUrl, ClientIP, Workload
- index=botsv3 sourcetype=o365:management:activity | stats count by ClientIP, UserId, UserAgent, Operation | sort ClientIP
- index=botsv3 sourcetype=o365:management:activity | top limit=50 Operation
- index=botsv3 sourcetype=o365:management:activity | top limit=50 UserId
- index=botsv3 sourcetype=stream:dns "taedong" | stats count by query, answer{} | sort -count
- index=botsv3 sourcetype=stream:http "taedong" | stats count by http_user_agent, uri, url, client_ip | sort -count
- index=botsv3 sourcetype=stream:smtp "taedonggang" | stats count by src_user, recipient, attach_filename{}
