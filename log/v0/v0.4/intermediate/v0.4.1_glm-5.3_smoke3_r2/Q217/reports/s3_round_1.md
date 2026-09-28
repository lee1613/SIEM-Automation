# s3 - Q217 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=7_
**Scope:** mail/activity feeds — o365:management:activity, ms:o365:reporting:messagetrace, stream:smtp, ms:aad:signin, ess_content_importer, maillog-too_small | fields: UserId, Operation, Workload, ClientIP, SenderAddress, RecipientAddress, Subject, MessageId
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- (Context from SH) Prior senior exhausted endpoint/file-sync sources; this scope (mail/activity feeds) does not overlap it.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; mail-relevant: stream:smtp (138 ev), ms:o365:reporting:messagetrace (27), o365:management:activity, ms:o365:management, ms:aad:audit, maillog-too_small (3), ess_content_importer (2).
- o365:management:activity 08/20 10:20–10:40 UTC | stats by Operation/UserId/ClientIP -> 0 events.
- o365:management:activity | stats by UserId -> 12 users; pcerf@froth.ly = 3 events only.
- pcerf@froth.ly detail -> FileUploaded/FileAccessed/FileModified, OneDrive, IP 104.238.59.42, 2018-08-20 13:05:36–13:06:50 UTC. No Exchange/mail operations.
- ms:aad:signin (pcerf, then whole feed) -> 0 events; feed is empty.
- ess_content_importer raw -> 2 events, both Splunkd "not responding" errors; no mail content.
- messagetrace sample_events -> 3 of 27 read: pcerf "Whats going on with Grace" (15:07 UTC) and postmaster@hovepark.org.uk bounces; fields SenderAddress/RecipientAddress/Subject/Size/MessageId, no attachment field in rows seen.

### What it means
The PCERF-L anchor (10:24:46–10:33:05 UTC) does not land in o365:management:activity: that window is empty, and pcerf's only events there are OneDrive file ops at 13:05 UTC from 104.238.59.42 (the same IP as his outbound mail FromIP). The anchor therefore likely refers to another feed (ms:o365:management audit_exchange, unqueried) or a local-time reading. No Bud email, no attachment, no visualization type identified; no candidate value.

## Assumptions
- Coverage: mail concept could appear in (a) o365:management:activity — searched, pcerf has only OneDrive ops, no mail ops; (b) ms:o365:reporting:messagetrace — sampled 3/27 rows, metadata only, Bud's mail possibly among unread 24; (c) stream:smtp — NOT searched, UNVERIFIED, likely full MIME with attachment names; (d) ms:o365:management — NOT searched, UNVERIFIED, may hold the Exchange preview/open audit the anchor describes; (e) ess_content_importer — searched, errors only; (f) maillog-too_small (3 ev) — not searched, UNVERIFIED.
- Selection: n/a — no candidate found this round.
- Premise: the anchor window maps to o365:management:activity — tested and failed (0 events in window; pcerf's events are 13:05 UTC). UNVERIFIED: which feed the anchor actually comes from.
- Premise: Bud's email is identifiable by sender/subject in mail feeds — UNVERIFIED, not yet searched for "Bud" or coin-miner terms.

## Ruled out
- ess_content_importer as a mail-content feed — only 2 Splunkd error events.
- ms:aad:signin — zero events in the dataset.
- o365:management:activity as the source of pcerf's email preview/open — his only 3 events are OneDrive file ops at 13:05–13:06 UTC; no Exchange operations for him anywhere in the feed.

## Open questions for SH
- Does the PCERF-L anchor (10:24:46–10:33:05) come from ms:o365:management (audit_exchange) rather than o365:management:activity, and is it UTC or local time?
- Should the next round pivot to stream:smtp (138 events) to read Bud's coin-miner email MIME and its first attachment filename?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._
