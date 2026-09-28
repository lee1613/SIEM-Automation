# s1 - Q205 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=3_
**Scope:** sourcetype=aws:s3:accesslogs (bucket_name=frothlywebcode) | sourcetype=aws:cloudtrail (eventName=PutBucketAcl) | fields=key, operation, http_status, request_time, requester, eventTime
**Insight:** FOUND   **Candidate:** OPEN_BUCKET_PLEASE_FIX.txt   **Confidence:** 99

## Prior rounds
- Round 1: 4 REST.PUT.OBJECT rows on frothlywebcode; only .txt was OPEN_BUCKET_PLEASE_FIX.txt (200, anonymous, 13:02:44). CloudTrail anchor unverified (field-casing errors).
- Round 2: CloudTrail PutBucketAcl pair found — 13:01:46Z grants AllUsers READ+WRITE (open), 13:57:54Z removes them (close). Raw access-log event confirmed literal key. Rivals ruled out.
- Round 3 (this): time-bounded re-query settled both open premises p1 and p2.

## This round
### What I ran
- `bucket_name=frothlywebcode operation="REST.PUT.OBJECT" earliest=1534770106 latest=1534773474 | stats count by key, http_status, request_time, remote_ip, requester` -> exactly 2 rows, both 200: OPEN_BUCKET_PLEASE_FIX.txt @13:02:44 (anonymous, 52.66.146.128) and frothly_html_memcached.tar.gz @13:04:17 (anonymous, 35.182.246.222).
- `bucket_name=frothlywebcode operation="REST.PUT.ACL" | stats count by request_time, remote_ip, requester, http_status` -> 2 rows at 13:01:46 and 13:57:54, both bstoll @107.77.212.175, 200 — matching the CloudTrail PutBucketAcl eventTimes to the second.

### What it means
FOUND, premises settled. p1 (coverage) VERIFIED: the epoch-bounded window (13:01:46Z open → 13:57:54Z close) contains exactly 2 REST.PUT.OBJECT rows, both successful; the access-log REST.PUT.ACL rows carry the same timestamps/IP/user as the CloudTrail PutBucketAcl events, tying the feeds; the unbounded 4-row PUT listing shows the other two PUTs (14:15:05 403, 14:19:19) outside the window; REST.PUT.OBJECT is the only object-write op on the bucket. p2 (selection) VERIFIED: the complete in-window successful-upload set is OPEN_BUCKET_PLEASE_FIX.txt (.txt — text file) and frothly_html_memcached.tar.gz (.tar.gz — not text). The only text file successfully uploaded while frothlywebcode was public is OPEN_BUCKET_PLEASE_FIX.txt, name unchanged.

## Ruled out
- frothly_html_memcached.tar.gz @13:04:17 — in-window and successful, but a .tar.gz archive, not a text file.
- frothly_html_memcached.tar.gz @14:19:19 (bstoll) — outside the public window.
- URL-encoded-key PUT @14:15:05 — 403 failed, outside the window.
- REST.PUT.ACL rows — bucket-ACL changes, not object uploads.
- aws:cloudtrail as upload evidence — no object-level PutObject events for this bucket.

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['aws:s3:accesslogs', 'aws:cloudtrail'] sources=[] fields=['bucket_name', 'key', 'object', 'uri', 'operation', 'requester', 'http_status', 'eventName', 'eventTime', 'eventID', 'requestParameters']
- Rounds worked: 3/3  (iterations: 22, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudtrail (eventname="PutBucketAcl" OR eventname="PutBucketPolicy" OR eventname="CreateBucket") | stats count by eventname, requestParameters, eventtime, sourceIPAddress, useridentity.arn | sort eventtime
- index=botsv3 sourcetype=aws:cloudtrail eventname="*Bucket*" | stats count by eventname, eventTime, requestParameters, sourceIPAddress | sort eventTime
- index=botsv3 sourcetype=aws:cloudtrail eventName="PutBucketAcl" | stats count by eventTime, requestParameters, sourceIPAddress, userName, userAgent, errorCode
- index=botsv3 sourcetype=aws:cloudtrail eventName="PutBucketAcl" | stats count by eventTime, userName, sourceIPAddress
- index=botsv3 sourcetype=aws:cloudtrail eventSource="s3.amazonaws.com" (eventName="PutBucketAcl" OR eventName="PutBucketPolicy" OR eventName="CreateBucket" OR eventName="DeleteBucketAcl" OR eventName="PutBucketCors") | stats count by eventName, eventTime, requestParameters, sourceIPAddress, userName | sort eventTime
- index=botsv3 sourcetype=aws:cloudtrail eventSource="s3.amazonaws.com" | stats count by eventName
- index=botsv3 sourcetype=aws:cloudtrail frothlywebcode | stats count by eventName, eventTime, requestParameters, sourceIPAddress | sort eventTime
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode operation="REST.PUT.ACL" | stats count by request_time, remote_ip, requester, http_status
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode operation="REST.PUT.OBJECT" earliest=1534770106 latest=1534773474 | stats count by key, http_status, request_time, remote_ip, requester
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode operation="REST.PUT.OBJECT" earliest=2018-08-20T13:01:46Z latest=2018-08-20T13:57:54Z | stats count by key, http_status, request_time, remote_ip, requester
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode operation="REST.PUT.OBJECT" | stats count by key, http_status, request_time, remote_ip, requester
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode | stats count by operation, http_status
