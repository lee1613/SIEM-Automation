# s1 - Q321 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=6_
**Scope:** sourcetype=stream:smtp (source=stream:smtp), ms:o365:reporting:messagetrace | fields: _raw, content, attach_filename, SenderAddress, Subject, DateReceived, FromIP
**Insight:** partial
**Candidate:** 29   **Confidence:** 55

## Prior rounds
R1: Ruled out literal "Taedonggang" (0 events index-wide); mapped mail feeds; read 50 of 56 messagetrace rows to ghoppy — all benign; stream:smtp keyword hits for "Taedonggang"/"naver.com" were 0 because bodies live in raw events.

## This round
### What I ran
- messagetrace recipient=ghoppy | sort -SenderAddress | head 12 -> 12 rows (pcerf, mkraeusen, jwortoski, it@frothly.com); all 56 rows to ghoppy now read, none brag of exfiltration.
- get_raw_events stream:smtp "Hoppy" -> 10 events; first: 15:19:35Z "Fw: All your datas belong to us" from Grace Hoppy, quoting "From: HyunKi Kim <hyunki1984@naver.com> ... Subject: All your datas belong to us".
- get_raw_events "All your datas belong to us" -> 2 events: adversary original 15:15:00Z (sender IP 125.209.224.215, inline PNG 1534778082419.png) and Grace's 15:19:35Z forward.
- rex around "customer" -> Grace's note "Are these our customers?" above the quoted adversary mail.
- rex after "Gracie," -> body: "We brought your data and imported it: https://pastebin.com/sdBUkwsE Also, you should not be too hard Bruce. He good man" — no number.
- rex on the Outlook link-preview card -> title "( ) ) ) - Pastebin.com" — no number.
- stream:http "sdBUkwsE" -> 0 events (pastebin is HTTPS; content not captured).
- read_image 1534778082419.png (twice) -> Naver webmail screenshot: mailbox search "gist" returns 29 results ("검색결과 (29)"), top hit an exfiltrated Frothly email (ghoppy→btun re: Bruce Gist, 2018-07-26).
- stream:smtp "hyunki1984" -> exactly 2 events (original + forward); no second adversary email.

### What it means
The bragging email is identified and fully read. Its body states no number; its only numeric artifact is the attached screenshot showing the adversary's imported Frothly mail with 29 search results. 29 is therefore the candidate for "how many Frothly emails were revealed" — but the screenshot's 29 hits are for the term "gist" (internal mail about Bruce Gist), while the question says "customer emails", whose proper home is the pastebin dump sdBUkwsE, absent from the dataset. Submitted as partial at 55 for that reason.

## Ruled out
- All 56 messagetrace rows to ghoppy@froth.ly as the bragging email — benign subjects, all read.
- Email body text / pastebin link-preview title as the source of the number — extracted in full, no number present.
- pastebin content via stream:http — 0 events for "sdBUkwsE" (HTTPS, not captured).
- A second adversary email to Grace — only 2 hyunki1984 events exist (original + forward).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The number of Frothly emails the adversary revealed is 29, read from the sole nu"
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_raw_events: {"keyword": "Hoppy", "limit": 10, "sourcetype": "stream:smtp"}` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
