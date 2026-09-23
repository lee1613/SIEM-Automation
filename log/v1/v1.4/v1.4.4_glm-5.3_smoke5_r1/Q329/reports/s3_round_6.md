# s3 - Q329 - Round 6
_stamped by runner: rounds_remaining=2 novel_spl=9_
**Scope:** sourcetype=o365:management:activity | stream:smtp | ms:o365:reporting:messagetrace | fields=Operation, UserId, SourceFileName, ClientIP, attach_filename, from_addr, Subject
**Insight:** partial
**Candidate:** none   **Confidence:** 15

## Prior rounds
- R1: upload-feed enumeration — 7 O365 FileUploaded docs, code42/S3 tarballs only, stream:http no POSTs. NOT_FOUND.
- R2: ransom email "All your datas belong to us" (hyunki1984@naver.com) with inline PNG 1534778082419.png; read_image -> FOUR. Partial.
- R3: hyunki1984 = only external SMTP sender; sent exactly one file (the PNG); tied to intrusion via fyodor's exfil transport rule. Partial, FOUR, conf 62.
- R4: no "Taedonggang" string in any reachable raw feed; base64 body undecodable. Partial, FOUR, conf 55.

## This round
### What I ran
- FileUploaded by ClientIP -> bgist's 4 uploads (morebeer.jpg, stout-2.jpg, stout.png, BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, 09:57:17-33) ALL from 104.207.83.63.
- All activity from 104.207.83.63 -> 14 ops: Add-MailboxPermission, Add-RecipientPermission, New-MailboxSearch (via compromised fyodor) + bgist's uploads/previews/sharing — 104.207.83.63 IS the attacker.
- read_image font-size check on the PNG -> FOUR is only capitalized, same letter height, NOT a larger point size.
- Full SMTP attachment inventory (11/11 rows) + "Birthday" search -> the uploaded images appear nowhere as attachments; all rival files are internal business mail.

### What it means
The actor's uploads are bgist's four files from attacker IP 104.207.83.63 — not the ransom PNG. FOUR is refuted on the question's own test (not a larger font size), and the PNG was an email attachment, not an upload. The three uploaded images' content is unread from O365 audit records and they are absent from SMTP — so no candidate currently passes, and I hold no value. The file that contains the oversized word is almost certainly one of morebeer.jpg / stout-2.jpg / stout.png; its content must be found in another feed.

## Ruled out
- FOUR / 1534778082419.png - careful re-read: FOUR is same point size, only capitalized; PNG was sent as an email attachment by the extortionist, not uploaded by the actor.
- All other SMTP attachments - internal business mail (pwned.jpg, Malware Alert Text.txt, Employee New Hire Dates.xlsx, image00x.jpg).
- ghoppy/mkraeusen/pcerf O365 uploads - from non-attacker IPs (174.215.12.64, 107.77.212.175, 104.238.59.42).
- Literal "Taedonggang" in o365:management:activity, stream:smtp, ms:o365:reporting:messagetrace raw, and the PNG - zero hits.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
