# s1 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=11_
**Scope:** sourcetype=ms:o365:management | fields=UserId, Operation, Workload, ObjectId, SourceFileName, CreationTime
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1: messagetrace (Aug 20 only, no attachment fields, no miner subject from any sender), o365:management:activity (zero btun events), stream:smtp (inbound to matar only) — all eliminated as carriers of the Bud miner email.
- Round 2: ms:o365:management fully characterized — OneDrive/SharePoint/AAD/Exchange admin activity, Aug 20 only, no message content, no miner/splunk-named files.

## This round
### What I ran
- get_sourcetype_fields ms:o365:management -> 1073 events, 6 workloads, all 2018-08-20.
- ObjectId keyword search (miner/coin/splunk/crypto) -> 0 events.
- | stats count by ObjectId -> 923 groups (50 read): bgist Birthday Pictures, bstoll Attachments/New Beer Styles - Draft.pptm, ghoppy Attachments/d3dx9_38.pdf.dll, fyodor Documents.
- ObjectId="*bstoll*" -> 1 event; ObjectId="*btun*" -> 0 (btun has no OneDrive objects).
- Extension filter over ObjectId -> 684 distinct files (50 read), none miner/splunk-related.
- Workload="Exchange" -> 10 admin cmdlet events, no message metadata.
- SourceFileName keyword search (miner/coin/splunk/crypto/monero/cpu) -> 0 events.

### What it means
NOT_FOUND. ms:o365:management cannot answer the question: it is admin/file activity, not mail content. It holds no Subject, MessageId, or attachment-name fields for sent mail, and neither ObjectId nor SourceFileName (785 values) contains any miner/coin/splunk-named file. The Bud coin-miner email and its first attachment remain unidentified in every feed queried so far.

## Assumptions
- Coverage: ms:o365:management ObjectId — searched miner/coin/splunk/crypto (0 hits) and enumerated 50 of 923 groups; SourceFileName — searched miner/coin/splunk/crypto/monero/cpu (0 hits); Workload=Exchange — enumerated all 10 events, admin cmdlets only. VERIFIED for this feed. UNVERIFIED: the 77 messagetrace subject rows never read (round 1 truncation), stream:http, Sysmon/WinHostMon, aws:s3:accesslogs, code42:api, osquery:results.
- Selection: "Bud" is ambiguous — btun@froth.ly (Bud Inger) and bstoll@froth.ly (Bud Stoll) both exist; bstoll is the IT/Splunk admin and likelier author of a miner-issue email, but neither's miner email was found — UNVERIFIED which Bud the question means.
- Premise: the attachment is identifiable from mail/file metadata in O365 feeds — REFUTED for this feed by the queries above.

## Ruled out
- ms:o365:management as the answer's carrier — no message content, no attachment fields, no miner/splunk-named files.
- bstoll's "New Beer Styles - Draft.pptm" — beer content, unrelated to the miner issue.
- ghoppy's "d3dx9_38.pdf.dll" — malware dropper in ghoppy's mailbox, not a Bud-sent illustration.

## Open questions for SH
- Should the next round enumerate ALL messagetrace subjects (127 rows, 77 unread) for both bstoll@froth.ly and btun@froth.ly to find the miner-issue email by subject wording other than the keywords already excluded?
- Which non-O365 feed should I pivot to for the attachment content: endpoint Sysmon/WinHostMon file events, stream:http, aws:s3:accesslogs, or code42:api?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 6 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "ms:o365:management"}` (32 of 131 rows seen); `run_splunk_search: index=botsv3 sourcetype="ms:o365:management" | stats count by ObjectId, UserId, Operation,…` (50 of 1060 rows seen); `run_splunk_search: index=botsv3 sourcetype="ms:o365:management" | stats count by ObjectId` (50 of 923 rows seen); `run_splunk_search: index=botsv3 sourcetype="ms:o365:management" (ObjectId="*.pdf" OR ObjectId="*.png" OR Obje…` (25 of 713 rows seen); `run_splunk_search: index=botsv3 sourcetype="ms:o365:management" (ObjectId="*.pdf" OR ObjectId="*.png" OR Obje…` (50 of 684 rows seen); `run_splunk_search: index=botsv3 sourcetype="ms:o365:management" | stats count by SourceFileName` (50 of 785 rows seen). A claim resting on them alone is UNVERIFIED._
