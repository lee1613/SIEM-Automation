# s1 - Q321 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=4_
**Scope:** sourcetype=ms:o365:reporting:messagetrace, stream:smtp | fields: SenderAddress, Subject, DateReceived, FromIP, RecipientAddress, method, content_type
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
(none — round 1)

## This round
### What I ran
- search_keyword "Taedonggang" -> 0 events anywhere in the index.
- get_source_types -> 102 sourcetypes; mail feeds present: stream:smtp, ms:o365:reporting:messagetrace, ms:o365:management, o365:management:activity.
- get_sources sourcetype=stream:smtp -> one source (stream:smtp), 879 events.
- `index=botsv3 sourcetype="ms:o365:reporting:messagetrace" recipient="ghoppy@froth.ly" | stats count by SenderAddress, Subject, DateReceived, FromIP` -> 56 rows, 50 returned and read; senders all froth.ly/it@frothly.com, subjects benign (brewer conference, VPN, brewertalk, Bruce Gist thread).
- `index=botsv3 sourcetype=stream:smtp "Taedonggang"` -> 0; `... "naver.com"` -> 0.
- get_sourcetype_fields stream:smtp -> 879 events, all 2018-08-20, host=matar, dest=172.31.38.181:25 Postfix; 185 EHLO/DATA/QUIT sessions; content_type on 137 events (bodies in raw events).

### What it means
NOT_FOUND. The adversary's name never appears in the data, so the bragging email must be found by content, and I never read a message body. Two concrete unexplored paths remain: the 6 unread messagetrace rows to ghoppy (of 56), and the stream:smtp raw DATA bodies (185 sessions, readable via get_raw_events). Among the 50 rows read, only four arrived from non-Frothly IPs (it@frothly.com "Quarentined email"; jwortoski "New Customer" and "RE: Re:"; bgist "RE: I Lied, One More...") — leads, not evidence.

## Ruled out
- Literal "Taedonggang" in index=botsv3 — keyword search returned 0 events.
- stream:smtp containing "Taedonggang" or "naver.com" — 0 events each.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="ms:o365:reporting:messagetrace" recipient="ghoppy@froth.ly" | sta…` (50 of 56 rows seen); `get_sourcetype_fields: {"sourcetype": "stream:smtp"}` (47 of 94 rows seen). A claim resting on them alone is UNVERIFIED._
