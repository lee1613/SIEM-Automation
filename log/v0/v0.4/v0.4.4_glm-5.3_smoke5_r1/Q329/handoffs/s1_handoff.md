# s1 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=10_
**Scope:** sourcetypes=code42:user, code42:security, code42:computer, code42:api, stream:http, stream:smtp, aws:s3:accesslogs, aws:cloudtrail, symantec:ep:agent:file, symantec:ep:behavior:file, symantec:ep:risk:file, symantec:ep:packet:file, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinEventLog | fields=user, username, email, src_user, dest_user, object, uri, file, filename, path, RecipientAddress, SenderAddress, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Round 1: "Taedonggang" absent from o365:management:activity and ms:o365:reporting:messagetrace (0 events, all casings); 102 sourcetypes enumerated; no candidate.

## This round
### What I ran
- sourcetype=code42:security "Taedonggang" | stats count by user, file_path, file_name -> 0 events
- sourcetype=code42:api "Taedonggang" | stats count by user, file_path, file_name -> 0 events
- sourcetype=code42:user "Taedonggang" | stats count by user, email -> 0 events
- sourcetype=code42:computer "Taedonggang" | stats count by user, computer -> 0 events
- sourcetype=stream:http "Taedonggang" | stats count by http_method, uri -> 0 events
- sourcetype=stream:smtp "Taedonggang" | stats count by src_user, file_name -> 0 events
- sourcetype=aws:s3:accesslogs "Taedonggang" | stats count by Operation, Requester, Key -> 0 events
- sourcetype=aws:cloudtrail "Taedonggang" | stats count by eventName, requestParameters.bucketName -> 0 events
- sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "Taedonggang" | stats count by EventCode, Image -> 0 events
- sourcetype=WinEventLog "Taedonggang" | stats count by EventCode, user -> 0 events

### What it means
NOT_FOUND: the literal string "Taedonggang" does not appear in ANY feed in the assigned scope (nor in the O365 feeds from round 1), in any casing tried. No uploader identity, no uploaded file, and no candidate word was recovered. The identity must be located elsewhere — most plausibly as a beer-name/document-title string rather than a username (Taedonggang is a North Korean beer brand, and Frothly is a brewery), in feeds outside this scope such as stream:dns, email subjects/bodies, or web access logs — or under a different casing/alias not yet tried.

## Ruled out
- code42:security, code42:api, code42:user, code42:computer - no event contains "Taedonggang" (0 events each)
- stream:http, stream:smtp - no event contains "Taedonggang" (0 events each)
- aws:s3:accesslogs, aws:cloudtrail - no event contains "Taedonggang" (0 events each)
- XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, WinEventLog - no event contains "Taedonggang" (0 events each)
- o365:management:activity, ms:o365:reporting:messagetrace (round 1) - no event contains the string in any casing (0 events each)

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: Two rounds of literal-string searching have exhausted the current reading of Taedonggang as an actor name and are returning only absence. A replacement should pursue a different direction: the evidence may sit in upload/content artifacts where Taedonggang is the document identity or contextual clue rather than the account string.
- Scope I owned: sourcetypes=['code42:security', 'code42:file', 'code42:computer', 'code42:user', 'code42:api', 'o365:management:activity', 'ms:o365:management', 'aws:s3:accesslogs', 'stream:http'] sources=[] fields=['user', 'username', 'email', 'file', 'filename', 'file_name', 'object', 'object_name', 'url', 'src', 'dest', '_raw']
- Rounds worked: 2/8  (iterations: 22, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "Taedonggang" | stats count by sourcetype, source | sort -count
- index=botsv3 sourcetrype=ms:o365:reporting:messagetrace "taedonggang" | stats count by SenderAddress
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "Taedonggang" | stats count by EventCode, Image
- index=botsv3 sourcetype=aws:cloudtrail "Taedonggang" | stats count by eventName, requestParameters.bucketName
- index=botsv3 sourcetype=aws:s3:accesslogs "Taedonggang" | stats count by Operation, Requester, Key
- index=botsv3 sourcetype=code42:api "Taedonggang" | stats count by user, file_path, file_name
- index=botsv3 sourcetype=code42:computer "Taedonggang" | stats count by user, computer
- index=botsv3 sourcetype=code42:security "Taedonggang" | stats count by user, file_path, file_name
- index=botsv3 sourcetype=code42:user "Taedonggang" | stats count by user, email
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "taedonggang" | stats count by SenderAddress
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "Taedonggang" | stats count by SenderAddress, RecipientAddress
- index=botsv3 sourcetype=o365:management:activity "taedong" | stats count by Operation
- index=botsv3 sourcetype=o365:management:activity "Taedonggang" | stats count by Operation, Workload
- index=botsv3 sourcetype=stream:http "Taedonggang" | stats count by http_method, uri
- index=botsv3 sourcetype=stream:smtp "Taedonggang" | stats count by src_user, file_name
- index=botsv3 sourcetype=WinEventLog "Taedonggang" | stats count by EventCode, user
