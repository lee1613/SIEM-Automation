# s1 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=8_
**Scope:** sourcetype=ms:o365:reporting:messagetrace | o365:management:activity | stream:smtp | fields=Subject, SenderAddress, MessageId, Operation, UserId
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1: enumerated feeds; messagetrace has no attachment fields and no miner-related subject from any sender; o365:management:activity has zero btun@froth.ly events; stream:smtp is only inbound mail to host matar with no miner content.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; identified email-relevant feeds.
- get_sourcetype_fields ms:o365:reporting:messagetrace -> 711 events / 15 messages; fields are Subject, SenderAddress, Size, Status — no attachment fields at all.
- messagetrace SenderAddress="btun@froth.ly" | stats count by Subject, MessageId, DateReceived -> 16 rows, all 15 Bud subjects read in full; none mention miners/coins/crypto.
- messagetrace | stats count by Subject, SenderAddress -> 127 rows, 50 returned; no miner subject among those read.
- messagetrace Subject="*miner*" OR "*coin*" OR "*crypto*" OR "*monero*" OR "*CPU*" -> 0 events.
- get_raw_events stream:smtp keyword=miner -> 0 events.
- o365:management:activity UserId=btun -> 0 events; all users by Operation -> 55 rows, btun absent.

### What it means
NOT_FOUND. The three feeds I could reach do not contain the Bud coin-miner email: messagetrace covers only 2018-08-20, has no attachment fields, and no miner-related subject from anyone; o365:management:activity records no activity by btun@froth.ly; stream:smtp captures only inbound SMTP to the brewertalk web server (matar). The email, its attachment, and the visualization type remain unidentified.

## Assumptions
- Coverage: messagetrace — searched subjects for miner/coin/crypto/monero/CPU (0 hits) and confirmed no attachment fields exist in the feed; o365:management:activity — searched for btun (0 events); stream:smtp — keyword search for miner (0 events). UNVERIFIED: ms:o365:management (separate sourcetype, never queried — likely holds O365 management API message data with attachment names), stream:http, Sysmon/WinHostMon file-creation events, aws:s3:accesslogs, code42:api.
- Selection: Bud identified as btun@froth.ly from messagetrace sender list — VERIFIED (15 distinct subjects from that address).
- Premise: the miner email is an internal Frothly email from Bud — its absence from messagetrace suggests it is dated outside Aug 20 or carried in a different feed — UNVERIFIED.

## Ruled out
- ms:o365:reporting:messagetrace as the answer's carrier — no attachment fields, no miner-related subject, single-day coverage.
- o365:management:activity — zero events for btun@froth.ly.
- stream:smtp — only inbound SMTP to host matar; no miner content.

## Open questions for SH
- Should the next round query the ms:o365:management sourcetype (distinct from o365:management:activity) for Bud's sent-mail with attachment metadata?
- Is the coin-miner email expected to be dated after 2018-08-20, i.e. outside messagetrace coverage, and if so which date range is in scope?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 3 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="o365:management:activity" | stats count by UserId, Operation` (50 of 55 rows seen); `get_sourcetype_fields: {"min_count": 5, "sourcetype": "stream:smtp"}` (44 of 89 rows seen); `run_splunk_search: index=botsv3 sourcetype="ms:o365:reporting:messagetrace" | stats count by Subject, SenderA…` (50 of 127 rows seen). A claim resting on them alone is UNVERIFIED._
