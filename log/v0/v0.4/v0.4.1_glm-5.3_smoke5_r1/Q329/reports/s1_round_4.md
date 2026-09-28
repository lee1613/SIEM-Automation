# s1 - Q329 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=11_
**Scope:** sourcetypes=access_combined, stream:http (source /var/log/httpd/access_log); pivoted to stream:mysql for forum DB traffic
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
- Round 1: "taedonggang" absent from O365 UserId (12 ids), access_combined, stream:http, code42; all 8 O365 uploads by internal froth.ly users.
- Round 2: 3 anonymous S3 uploads to open bucket frothlywebcode (unattributed); brewertalk.com MyBB forum found behind /var/log/httpd/access_log; account registered from 172.16.0.149 at 13:47:04Z; SMTP attachments enumerated (only external sender hyunki1984@naver.com).
- Round 3: MyBB endpoints mapped — attachment.php serves only thumbnails, no avatar/upload/document paths; printthread.php?tid=16 viewed; no username in any URI.
- Round 4 (this round): web path exhausted for attribution; stream:mysql opened — attacker IP = X'ac100095', finduserthreads&uid=36 search logged; no mybb_users INSERT, no "taedonggang" string.

## This round
### What I ran
- xmlhttp/search/member/showthread URI listings, uri="*username*"/"*user=*"/"*name=*", uri="*.pdf/.docx/.txt/.doc/.html", uri="*uploads*"/"*avatar*" -> no username in any URI; only default_avatar.png served; only /robots.txt among document extensions.
- printthread raw event -> GET /printthread.php?tid=16, 2061 bytes, 13:22:49Z.
- stream:mysql | stats count by query -> 4192 distinct queries; attacker IP X'ac100095' in 2571 session DELETEs; mybb_searchlog INSERT with t.uid='36'.
- query="*mybb_users*" -> 1246 rows (25 read), all SELECTs; query="*INSERT*mybb_users*" -> 0; "taedonggang" in stream:mysql -> 0.

### What it means
NOT_FOUND: the web logs cannot attribute any upload to Taedonggang — no username in URIs, no avatar or attachment upload path, no served document. The MySQL stream is the new open lead: it carries the forum's live queries, the attacker's IP is visible in session records, and a uid=36 thread search was logged — but the registration INSERT and the username string were not captured. The file and its contents remain unrecovered; no word can be reported.

## Assumptions
- Coverage: uploads as (a) MyBB avatar/attachment endpoints — searched via URI patterns (*uploads*, *avatar*, attachment.php aid=), none exist in the logs; (b) served documents — searched by extension, only robots.txt; (c) forum DB inserts (mybb_users/posts/attachments) — mybb_users INSERT absent, mybb_posts/mybb_attachments NOT YET SEARCHED; (d) endpoint file writes — NOT YET SEARCHED. - VERIFIED a-b, UNVERIFIED c-d
- Selection: no candidate; nothing passes the "uploaded by Taedonggang" test. - VERIFIED
- Premise: Taedonggang is the account registered from 172.16.0.149. - UNVERIFIED: username never observed in any feed; only the registration POST and uid=36/40 profile views are circumstantial.
- Premise: the target file is a formatted document (font sizes imply HTML/docx/pdf). - UNVERIFIED: no file contents read.

## Ruled out
- Web-log attribution of an upload to Taedonggang — exhaustive URI checks found no username, no upload path, no served document.
- INSERT INTO mybb_users in stream:mysql — 0 events.
- Literal "taedonggang" in stream:mysql — 0 events.
- stream:http for brewertalk — 0 events (round 2).

## Open questions for SH
- Should the next round search stream:mysql for mybb_posts/mybb_threads INSERTs (post bodies may carry the oversized-word content) and mybb_attachments INSERTs (the forum's file-upload event), before pivoting to endpoint telemetry?
- Is uid=36 or uid=40 known from the case file to be the attacker's forum account (both were profile-viewed repeatedly by 172.16.0.149)?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:mysql | stats count by query` (50 of 4192 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:mysql query="*mybb_users*" | stats count by query` (25 of 1246 rows seen). A claim resting on them alone is UNVERIFIED._
