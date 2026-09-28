# s1 - Q300 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Scope:** sourcetype=o365:management:activity, ms:o365:management | fields=Operation, SourceFileName, SourceFileExtension, ObjectId, UserAgent, UserId, ClientIP, CreationTime
**Insight:** FOUND
**Candidate:** Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 Fedora/1.9.1-2.5.rs3.0 NaenaraBrowser/3.5b4   **Confidence:** 99

## Prior rounds
(none — first round)

## This round
### What I ran
- get_source_types -> confirmed o365:management:activity and ms:o365:management exist.
- get_sourcetype_fields o365:management:activity -> 977 events; ObjectId top value is the .lnk file; UserAgent field not in first 31 rows returned.
- `Operation=FileUploaded | stats count by ObjectId, UserId, ClientIP` -> 7 uploads total; exactly one .lnk: "BRUCE BIRTHDAY HAPPY HOUR PICS.lnk", bgist@froth.ly, 104.207.83.63.
- `Operation=FileUploaded SourceFileName="BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" | stats count by UserAgent` -> 1 event, UA = the Naenara string.
- get_raw_events keyword=NaenaraBrowser -> 5 raw events; UA string confirmed character-exact.
- Cross-feed: `(ms:o365:management OR o365:management:activity) Operation=FileUploaded SourceFileExtension=lnk` -> 2 events, one per feed, identical UA.

### What it means
The only .lnk file uploaded to OneDrive in the entire O365 activity dataset is "BRUCE BIRTHDAY HAPPY HOUR PICS.lnk", uploaded 2018-08-20T09:57:33 by bgist@froth.ly from 104.207.83.63. Its upload record carries UserAgent "Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 Fedora/1.9.1-2.5.rs3.0 NaenaraBrowser/3.5b4" — the Naenara browser of North Korea's Red Star OS, itself the compromise indicator. The same UA/IP created an anonymous-edit link on the file 29 seconds later, and that link was then used by bstoll@froth.ly and anonymous users — confirming this is the malicious link file. Both O365 feeds record the identical UA, so the answer is feed-independent.

## Ruled out
- Other FileUploaded events (morebeer.jpg, stout-2.jpg, stout.png, HomeBrewingGuide.pdf, Frothly_GABF_Deck-2018-MK.pptx, Beer styles.pptx) — not .lnk files; the SourceFileExtension=lnk filter returns only the one event.
- "ExportWorker" UA (app@sharepoint FileAccessed on the .lnk) — an internal SharePoint app service account, not the upload event.
- Edge/17.17134 UA (AnonymousLinkUsed events) — access events by link recipients, not the upload.
- Endpoint/network feeds — question is about the O365-recorded upload UA; both O365 feeds agree.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "o365:management:activity"}` (31 of 125 rows seen); `get_raw_events: {"keyword": "BRUCE BIRTHDAY HAPPY HOUR PICS.lnk", "limit": 10, "sourcetype": "o365:managem…` (5 of 10 rows seen). A claim resting on them alone is UNVERIFIED._
