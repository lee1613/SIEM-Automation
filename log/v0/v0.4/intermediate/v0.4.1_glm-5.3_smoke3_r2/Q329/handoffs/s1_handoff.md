# s1 - Q329 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="aws:s3:accesslogs" http_method="PUT" | stats count by bucket | sort -count
- index=botsv3 sourcetype="stream:http" "taedonggang*" | stats count
- index=b transactions=botsv3 sourcetype="aws:s3:accesslogs" "taedonggang*" | stats count
- index=botsv3 sourcetype="aws:s3:accesslogs" "taedonggang*" | stats count
### What it means

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "aws:s3:accesslogs"}` (38 of 76 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: Two consecutive rounds produced no usable reported results on the assigned upload-telemetry path, so anti-thrash blocks further continue. Handoff: no actor mapping or candidate file established; literal-name searches for taedong/taedonggang were empty in O365, SMTP, message trace, CloudTrail, and attempted S3/HTTP probes did not yield reported evidence.
- Scope I owned: sourcetypes=['o365:management:activity', 'ms:o365:reporting:messagetrace', 'aws:s3:accesslogs', 'code42:security', 'code42:api', 'stream:http'] sources=[] fields=['UserId', 'Operation', 'ObjectId', 'SourceFileName', 'SenderAddress', 'RecipientAddress', 'Subject', 'fileName', 'fullPath', 'fileEventType', 'uri_path', 'url', 'object', 'key', 'user']
- Rounds worked: 3/8  (iterations: 30, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=b transactions=botsv3 sourcetype="aws:s3:accesslogs" "taedonggang*" | stats count
- index=botsv3 "taedonggang" | stats count by sourcetype, source | sort -count
- index=botsv3 sourcestype="o365:management:activity" "taedong" | stats count
- index=botsv3 sourcetype="aws:cloudtrail" "taedong" | stats count by eventName
- index=botsv3 sourcetype="aws:cloudtrail" "taedular" OR "taedong" | stats count
- index=botsv3 sourcetype="aws:elb:accesslogs" "taedong" | stats count
- index=botsv3 sourcetype="aws:s3:accesslogs" "taedong" | stats count
- index=botsv3 sourcetype="aws:s3:accesslogs" "taedonggang*" | stats count
- index=botsv3 sourcetype="aws:s3:accesslogs" http_method="PUT" | stats count by bucket | sort -count
- index=botsv3 sourcetype="aws:s3:accesslogs" http_method="PUT" | stats count by user | sort -count
- index=botsv3 sourcetype="aws:s3:accesslogs" | stats count by http_method | sort -count
- index=botsv3 sourcetype="aws:s3:bucket" http_method="PUT" | stats count by bucket | sort -count
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" "taedong" | stats count by SenderAddress, RecipientAddress
- index=botsv3 sourcetype="o365:management:activity" "taedong" | stats count
- index=botsv3 sourcetype="o365:management:activity" "taedong" | stats count by Operation, UserId
- index=botsv3 sourcetype="o365:management:activity" "taedonggang" | stats count by Operation, UserId
- index=botsv3 sourcetype="o365:management:activity" | stats count by UserId | sort -count
- index=botsv3 sourcetype="stream:http" "taedong" | stats count
- index=botsv3 sourcetype="stream:http" "taedonggang*" | stats count
- index=botsv3 sourcetype="stream:smtp" "taedong" | stats count by source
