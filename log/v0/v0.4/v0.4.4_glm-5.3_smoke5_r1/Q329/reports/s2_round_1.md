# s2 - Q329 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=7_
**Scope:** index=botsv3 | all 102 sourcetypes enumerated via get_source_types | keyword sweep `"taedonggang"` over code42:security, aws:s3:accesslogs, stream:http, stream:smtp, aws:cloudtrail, symantec:ep:agent:file
**Insight:** partial (no candidate this round)   **Candidate:** none   **Confidence:** 55

## Prior rounds
- R1 (s1): literal-actor reading disproved — "taedonggang" absent from o365:management:activity and ms:o365:reporting:messagetrace (Operations/Workload, Sender/RecipientAddress).

## This round
### What I ran
- get_source_types -> 102 sourcetypes; identified unswept candidates: ms:o365:management (distinct from the feed s1 cleared), code42:api/computer/org/user, seven other symantec:ep:*:file feeds, WinEventLog, Sysmon, bash_history, access_combined, aws:elb:accesslogs, osquery:results, ess_content_importer.
- `sourcetype=code42:security "taedonggang" | stats count` -> 0
- `sourcetype=aws:s3:accesslogs "taedonggang" | stats count` -> 0
- `sourcetype=stream:http "taedonggang" | stats count` -> 0
- `sourcetype=stream:smtp "taedonggang" | stats count` -> 0
- `sourcetype=aws:cloudtrail "taedonggang" | stats count` -> 0
- `sourcetype=symantec:ep:agent:file "taedonggang" | stats count` -> 0

### What it means
NOT_FOUND this round. The literal string does not appear in the six artifact-bearing feeds most likely to name an uploaded file: cloud backup (code42), S3 object keys/requesters, HTTP upload URLs/bodies, SMTP MIME headers, CloudTrail S3 API calls, endpoint file events. Splunk keyword matching is case-insensitive, so casing is not the reason for the zeros. Two live explanations remain: the artifact sits in an unswept feed, or the name/content is base64/MIME-encoded so the literal string never appears in raw text (which would keep stream:smtp/http alive despite the zeros — the filename would live in MIME headers or a decoded body, recoverable only via get_raw_events). Next round: run get_sources first — the source axis is entirely unexamined and generic sourcetypes can hide distinct feeds — then ms:o365:management, access_combined/aws:elb:accesslogs (upload POST filenames), and the remaining code42/symantec variants.

## Ruled out
- code42:security — 0 events contain "taedonggang" (no cloud-upload exposure naming it)
- aws:s3:accesslogs — 0; no object key or requester names it
- stream:http — 0; no URL, parameter, or plaintext body literal (encoded bodies not excluded)
- stream:smtp — 0; no MIME filename/subject/sender literal (encoded attachments not excluded)
- aws:cloudtrail — 0; no S3 PutObject key or assumed-role user names it
- symantec:ep:agent:file — 0; no endpoint file event names it
- (R1) o365:management:activity, ms:o365:reporting:messagetrace — 0

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
