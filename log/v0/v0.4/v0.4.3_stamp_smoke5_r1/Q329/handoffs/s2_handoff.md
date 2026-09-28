# s2 - Q329 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype IN (symantec:ep:agent:file,symantec:ep:behavior:file,symantec:ep:packet:file,symantec:ep:risk:file,symantec:ep:security:file) "taedonggang" | stats count by sourcetype
### What it means
Intention: Symantec feeds are empty for the term; check osquery:results and WinHostMon for "taedonggang" as a file path or process name.


## What I'd tell my replacement
- Retired because: Two rounds have produced no entity, file, or upload foothold, and the latest round reduced to a single feed search. This scope is unproductive without first discovering which feed actually carries Taedonggang-related document activity.
- Scope I owned: sourcetypes=['aws:cloudtrail', 'aws:s3:accesslogs', 'o365:management:activity', 'ms:o365:management', 'ms:o365:reporting:messagetrace', 'code42:security', 'code42:user', 'code42:computer'] sources=[] fields=['user', 'userIdentity.*', 'requestParameters.*', 'Operation', 'UserId', 'ObjectId', 'SourceFileName', 'DestinationFileName', 'filename', 'object', 'key', 'bucket']
- Rounds worked: 2/8  (iterations: 12, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "taedonggang" | stats count by sourcetype, source | sort -count
- index=botsv3 sourcetype IN (symantec:ep:agent:file,symantec:ep:behavior:file,symantec:ep:packet:file,symantec:ep:risk:file,symantec:ep:security:file) "taedonggang" | stats count by sourcetype
- index=botsv3 sourcetype=aws:cloudtrail "taedonggang" | stats count by eventName, requestParameters.bucketName
- index=botsv3 sourcetype=code42:api "taedonggang" | stats count by sourcetype, source
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "taedonggang" | stats count by SenderAddress, RecipientAddress
- index=botsv3 sourcetype=o365:management:activity "taedonggang" | stats count by Operation, UserId, Workload
- index=botsv3 sourcetype=stream:smtp "taedonggang" | stats count by src_ip, mailfrom
