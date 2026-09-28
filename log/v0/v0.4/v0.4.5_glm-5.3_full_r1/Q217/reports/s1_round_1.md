# s1 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=4_
**Scope:** sourcetype=ms:o365:reporting:messagetrace | stream:smtp | o365:management:activity | ess_content_importer | fields=SenderAddress,Subject,DateReceived,RecipientAddress,Size,content_type
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 10

## Prior rounds
(none — first round)

## This round
### What I ran
- get_source_types -> 102 sourcetypes; email-capable: messagetrace, stream:smtp, o365:management:activity, ess_content_importer.
- get_sourcetype_fields ms:o365:reporting:messagetrace -> 711 events, all 2018-08-20, 15 distinct messages; fields are sender/recipient/subject/size/status only — no attachment field.
- get_sourcetype_fields stream:smtp -> 879 events, all 2018-08-20, 185 full SMTP DATA sessions to internal Postfix 172.31.38.181; content_type present on 137 events incl. multipart — raw MIME not yet read.
- o365:management:activity | stats count by Operation, Workload -> 29 rows; zero email-send/attachment operations.
- get_sourcetype_fields ess_content_importer -> 2 error events only.
- messagetrace SenderAddress="btun@froth.ly" | stats count by Subject,DateReceived,RecipientAddress -> 120 rows (50 returned): 8+ distinct btun messages on Aug 20; no miner-related subject in rows read.

### What it means
NOT_FOUND. No feed I queried exposes an attachment name, and no subject from btun@froth.ly in the rows I read mentions a coin miner. The messagetrace and stream:smtp feeds both cover only Aug 20, so Bud's miner email may sit in the unread 70 messagetrace rows, in the unread stream:smtp raw MIME payloads, or outside these feeds entirely (stream:http webmail, code42, WinEventLog, aws:s3:accesslogs). I hold no candidate value.

## Ruled out
- ms:o365:reporting:messagetrace as an attachment source - no attachment-name field exists in the feed.
- o365:management:activity - contains no email-send or attachment operations (file/SharePoint and Exchange admin cmdlets only).
- ess_content_importer - 2 error events, no email content.
- Keyword search for "attachment" across fields - only AWS ENI attachment fields in aws:cloudtrail, unrelated.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:smtp"}` (47 of 94 rows seen); `run_splunk_search: index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress="btun@froth.ly" | sta…` (50 of 120 rows seen). A claim resting on them alone is UNVERIFIED._
