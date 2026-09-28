# s1 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=9_
**Scope:** sourcetype=ms:o365:reporting:messagetrace | stream:smtp | fields=SenderAddress,RecipientAddress,Subject,DateReceived,MessageTraceId,content_type,_raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
R1: Enumerated email feeds; messagetrace has no attachment fields and covers only Aug 20; o365:management:activity has no send events; ess_content_importer is 2 errors; stream:smtp holds 185 full SMTP DATA sessions with MIME — unread.
R2 (this): Confirmed Bud = Bud Stoll (bstoll@froth.ly), found his 4 attachment emails in stream:smtp, and the attachment metadata fields.

## This round
### What I ran
- messagetrace | stats by MessageTraceId,Sender,Subject,Date,Size -> 165 rows (50 read): full Aug-20 inventory; no miner-named subject.
- messagetrace Subject="*miner*"/"*coin*"/"*crypto*" -> 0 events (complete result).
- get_raw_events keyword=filename stream:smtp -> 3 events: JSON fields attach_filename/attach_type/attach_size/attach_disposition + full MIME in "content"; one is From: Bud Stoll, To: Billy Tun + allhands, Subject "Postmortem on our issue with brewertalk", attach image002.jpg (image/jpeg, 222408 B, inline, base64), 2018-08-20T14:24:22Z.
- stream:smtp "attach_filename" | rex From + attach_filename -> 7 rows: Bud Stoll 4 events (image001.jpg; image002.jpg; image002.jpg+image003.jpg); Billy Tun 2 (Employee New Hire Dates.xlsx, pwned.jpg); bgist 1 (Malware Alert Text.txt); ghoppy/hyunki1984 (1534778082419.png); fyodor/pcerf (image001.jpg).

### What it means
NOT_FOUND as to the visualization type. I identified the sender (Bud Stoll) and his 4 attachment-bearing emails with filenames, but ran out of iterations before (a) ordering all 4 by time/subject to pick the FIRST miner-issue email and (b) reading the attachment content or body text that would name the Splunk visualization. The attachments are base64 inline JPEGs; the answer requires reading the chosen email's "content" field or a textual artifact naming the chart. No value is submitted — guessing a two-word chart type from the example would be invention.

## Ruled out
- Billy Tun (btun@froth.ly) as "Bud" - raw From lines show "Bud Stoll <bstoll@froth.ly>" and "Billy Tun <btun@froth.ly>" as distinct people.
- Any miner-named subject in messagetrace - wildcard search for *miner*/*coin*/*crypto* returned 0 events.
- messagetrace as attachment source - no attachment fields exist in the feed.
- Other senders' attachments (Billy Tun's xlsx/pwned.jpg, Gist's Malware Alert Text.txt, Hoppy's png) - wrong sender; the question names Bud.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=ms:o365:reporting:messagetrace | stats count by MessageTraceId, Se…` (50 of 165 rows seen). A claim resting on them alone is UNVERIFIED._
