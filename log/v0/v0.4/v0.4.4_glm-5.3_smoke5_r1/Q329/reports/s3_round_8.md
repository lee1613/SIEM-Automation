# s3 - Q329 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=8_
**Scope:** sourcetype=o365:management:activity | stream:smtp | ms:o365:reporting:messagetrace | XmlWinEventLog:Sysmon | fields=Operation, SourceFileName, ClientIP, UserAgent, ObjectId, attach_filename, _raw
**Insight:** partial
**Candidate:** none   **Confidence:** 10

## Prior rounds
- R1: upload-feed enumeration — 7 O365 FileUploaded docs, code42/S3 tarballs only; stream:http POST search later found invalid (field absent). NOT_FOUND.
- R2: ransom email PNG 1534778082419.png; read_image -> FOUR. Partial.
- R3: hyunki1984@naver.com = only external SMTP sender, one file (the PNG); tied to intrusion via fyodor's exfil rule. Partial, FOUR, conf 62.
- R4: no "Taedonggang" string in any reachable raw feed; base64 body undecodable. Partial, FOUR, conf 55.
- R5: actor IP 104.207.83.63 = bgist's 4 uploads; FOUR refuted (same point size); PNG was an attachment, not an upload. Partial, none.
- R6: NaenaraBrowser/ko-KP actor fingerprint; uploads metadata-only in O365; Sysmon 0 hits for image names. Partial, none.

## This round
### What I ran
- "Quarentined email" "morebeer" -> 0 hits (earlier "stout OR morebeer" matched "stout" alone); notices are quoted-printable, about a spoofed phishing mail.
- messagetrace RecipientAddress=bgist -> 45 rows; identified the "Wild Birthday Extravaganza!!!" thread as the birthday-pics distribution.
- stream:smtp "Wild Birthday Extravaganza" -> 2 events: image002.jpg (bstoll), image001.jpg (pcerf).
- read_image image002.jpg -> 252x56 pixels, output "N" — an email signature banner, not a document with an oversized word, and not an actor upload.

### What it means
No value. The uploaded file set is established beyond doubt (bgist's four from attacker IP 104.207.83.63, NaenaraBrowser/ko-KP), but the unreadable-content wall is now proven with quotes: O365 raw events for the uploads carry only ObjectId/ListId/CorrelationId metadata; Sysmon returns zero events for "morebeer" OR "stout"; stream:smtp has no attachment with those names; the uploads went to OneDrive over HTTPS, which stream:http (port 80 only) cannot carry. The one image content reachable on the birthday thread is a 252x56 signature banner. The word is not recoverable from the feeds I reached.

## Ruled out
- FOUR / ransom PNG - not a larger point size; an attachment, not an upload.
- image002.jpg "N" - 252x56 signature banner, internal email, not an actor upload.
- O365 audit, Sysmon, stream:smtp, messagetrace as content carriers for the uploaded images - metadata-only or zero hits (quoted above).
- stream:http upload bodies - HTTPS destination, port-80-only capture.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
