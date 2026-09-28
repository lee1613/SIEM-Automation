# s3 - Q329 - Round 2
_stamped by runner: rounds_remaining=2 novel_spl=9_
**Scope:** sourcetype=stream:smtp | source=stream:smtp | fields=_raw, content_type, method, src, dest, src_ip, dest_ip
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
- R1: mapped 102 sourcetypes; ess_content_importer = 2 daemon-error events only; "taedonggang" absent in plaintext across 9 feeds; stream:smtp confirmed to hold 185 DATA-bearing MIME sessions.
- R2 (this round): token map — bgist=27, stout=4, font-size=54, h1=19; morebeer/lnk/OneDrive/birthday/taedonggang all 0 in plaintext.
- Font-size histogram: outliers 41/36/34/31/28px against a body mass of 10-16px.
- Large-font contexts identified: Groupon 41px logo, Dropbox "Add files" h1, 4 O365 quarantine phishing emails (awards@greatamericanbeerfestival.com, 'Awards for you').
- 4 unread emails from Postfix host "STOUT" (localhost) to ghoppy@/bgist@/bstoll@/fyodor@froth.ly at 2018-09-15T01:14:16Z.
- Two "Open Sans" large-font bodies (#404040, #FFFFFF) remain unextracted — regex defeated by quoted-printable soft breaks.

## This round
### What I ran
- searchmatch token map over stream:smtp -> counts above; all named filenames zero in plaintext.
- font-size histogram -> outliers 41/36/34/31/28px.
- Context extraction after large sizes -> Groupon logo, Dropbox h1, 4 quarantine-phishing emails; two "Open Sans" contexts unmatchable.
- stout-context rex -> 4 attacker-IP Received headers (45.77.53.176) + 4 STOUT-host bulk emails to all four Frothly users.

### What it means
NOT_FOUND for the word, but the carrier is narrowed to two precise targets: the Open Sans large-font HTML bodies (34-36px) and the four STOUT-sent bulk emails. Filenames are base64-encoded inside MIME, invisible to keyword search — decoding, not scanning, is the remaining step.

## Ruled out
- morebeer.jpg, stout-2.jpg, stout.png, BRUCE BIRTHDAY HAPPY HOUR PICS.lnk, OneDrive, Birthday, taedonggang as plaintext tokens in stream:smtp - zero hits; they ride inside base64 MIME.
- Groupon 41px logo, Dropbox h1, O365 quarantine template - identified as benign template markup, not a single oversized word.

## Open questions for SH
- Should the next round prioritize decoding the 4 STOUT-sent bulk emails to the four Frothly users, or the Open Sans large-font bodies first?
- Is the 45.77.53.176 sender (quarantine-phishing chain) confirmed as the Taedonggang persona, so I can treat its HTML as in-scope?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
