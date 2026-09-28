# s3 - Q329 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=9_
**Scope:** sourcetype=stream:smtp | o365:management:activity | ms:o365:reporting:messagetrace | fields=attach_filename, from_addr, Subject, Operation, Parameters, _raw
**Insight:** partial
**Candidate:** FOUR   **Confidence:** 55

## Prior rounds
- R1: enumerated upload feeds — 7 O365 FileUploaded docs (all froth.ly users), code42/S3 only tarballs, stream:http no POSTs. NOT_FOUND.
- R2: stream:smtp pivot; ransom email "All your datas belong to us" with inline PNG 1534778082419.png; read_image -> FOUR largest-font word. Partial, attribution inferred from Korean origin.
- R3: actor identified as hyunki1984@naver.com (only external sender, 20/20 rows); sent exactly one file (the PNG); tied to intrusion via exfil transport rule. Partial, FOUR, conf 62.

## This round
### What I ran
- Ransom email CTE check -> original body is base64, forward is quoted-printable (plaintext string search therefore not conclusive for the original).
- get_raw_events o365:management:activity hyunki1984 -> New-TransportRule by fyodor@froth.ly: BlindCopyTo=hyunki1984@naver.com, rule name "SOX", Mode=Enforce — attacker exfil rule; no Taedonggang string.
- ms:o365:reporting:messagetrace "taedonggang" | stats count -> 0 (full raw, this feed now searched).
- Four attempts to extract/decode the base64/quoted-printable ransom body via rex -> all failed (escaped-CRLF patterns did not match); body remains unread.

### What it means
Partial. The named-entity tie SH asked for does NOT exist in the feeds I can reach: "Taedonggang" returns zero in stream:smtp raw, o365:management:activity raw, messagetrace raw, and the PNG itself; the transport rule is named "SOX". The attribution of 1534778082419.png to the actor rests on behavior — hyunki1984@naver.com is the only external sender in the SMTP route, its one email is the ransom note, and the compromised-account transport rule BCCs it — which is strong but is not the question's literal name. The candidate FOUR stands on that chain: actor's only sent file -> read_image -> FOUR is the largest-font word. The one unread place that could still carry the name is the original ransom email's base64 body, which I could not decode before tool access ended.

## Ruled out
- Literal "Taedonggang" in stream:smtp, o365:management:activity, ms:o365:reporting:messagetrace (full raw) and inside the PNG - all zero hits.
- Transport-rule name as the actor name - it is "SOX", not Taedonggang.
- All other SMTP attachments as the actor's file - sent by froth.ly users (pwned.jpg, Malware Alert Text.txt, Employee New Hire Dates.xlsx, image00x.jpg).
- 7 O365 FileUploaded documents - all froth.ly users, no attacker indicator, no recoverable content.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
