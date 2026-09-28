# s1 - Q206 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=2_
**Scope:** sourcetype=aws:s3:accesslogs | bucket_name=frothlywebcode | fields=key, http_method, http_status, object_size, request_time, requester
**Insight:** FOUND
**Candidate:** 2.93   **Confidence:** 97

## Prior rounds
- Round 1: Found both PUTs of frothly_html_memcached.tar.gz (13:04:17Z, 3076532 B, anonymous; 14:19:19Z, 3057116 B, bstoll); in-window listing showed only the 13:04:17Z .tar.gz PUT; SPL computed 2.93 MB; CloudTrail corroborated window boundaries (PutBucketAcl 13:01:46Z, 13:57:54Z), no PutObject for the key.
- Round 2: Verified p1 from the raw access-log line — the 13:04:17Z PUT record itself carries object_size 3076532; CloudTrail holds no size for this key.

## This round
### What I ran
- `key=frothly_html_memcached.tar.gz http_method=PUT http_status=200 | stats count by request_time, requester, http_status, object_size` -> exactly 2 events: 13:04:17Z (requester "-", 200, 3076532) and 14:19:19Z (bstoll, 200, 3057116).
- Window-spanning PUT listing (`_time>=1534768800 _time<=1534777200`) -> 6 events: ACL PUTs at 13:01:46Z and 13:57:54Z (key "-", bstoll — the window boundaries), OPEN_BUCKET_PLEASE_FIX.txt (13:02:44Z, 377 B), frothly_html_memcached.tar.gz (13:04:17Z, 200, 3076532, anonymous), a 403 anonymous PUT at 14:15:05Z on a quote-mangled key variant, and the bstoll PUT at 14:19:19Z (3057116).

### What it means
p2 is settled: the complete successful-PUT set for the key is two rows, and the window boundaries (13:01:46Z open, 13:57:54Z close, seen as the two key="-" ACL PUTs in the same feed and matching CloudTrail) place the 13:04:17Z PUT inside the public window and the 14:19:19Z PUT 21m25s after it closed. The 14:15:05Z 403 on the mangled-key variant further confirms the bucket was no longer publicly writable after 13:57:54Z. The successful in-window .tar.gz upload is the 13:04:17Z PUT, object_size 3076532 bytes; round(3076532/1024/1024, 2) = **2.93**.

## Ruled out
- 14:19:19Z PUT of frothly_html_memcached.tar.gz (3057116 B, bstoll) - outside the public window (closed 13:57:54Z); would yield 2.91.
- 14:15:05Z mangled-key PUT attempt - HTTP 403, failed, and outside the window.
- OPEN_BUCKET_PLEASE_FIX.txt (13:02:44Z, 377 B) - in window but not a .tar.gz.
- aws:cloudtrail as size source - no PutObject/data event for this key (0 events).

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['aws:s3:accesslogs', 'aws:cloudtrail'] sources=[] fields=['bucket_name', 'key', 'operation', 'http_status', 'request_time', 'bytes', 'eventTime', 'eventName', 'requestParameters']
- Rounds worked: 3/3  (iterations: 18, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com eventName=PutBucketAcl requestParameters.bucketName=frothlywebcode | stats count by _time, eventName, errorCode
- index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com eventName=PutObject requestParameters.bucketName=frothlywebcode requestParameters.key=frothly_html_memcached.tar.gz | stats count by _time, eventName, errorCode, responseElements
- index=botsv3 sourcetype=aws:cloudtrail frothly_html_memcached.tar.gz | stats count by _time, eventName, eventSource, errorCode
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode http_method=PUT _time>=1534768800 _time<=1534777200 | stats count by request_time, key, requester, http_status, object_size
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode http_method=PUT _time>=1534770106 _time<=1534773474 | stats count by request_time, key, http_status, object_size, remote_ip, requester
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode http_method=PUT earliest=2018-08-20T13:01:46Z latest=2018-08-20T13:57:54Z | stats count by request_time, key, http_status, object_size, remote_ip, requester
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode key=frothly_html_memcached.tar.gz http_method=PUT http_status=200 | stats count by request_time, requester, http_status, object_size
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode key=frothly_html_memcached.tar.gz http_method=PUT request_time="20/Aug/2018:13:04:17 +0000" | stats max(object_size) as bytes | eval size_mb = round(bytes/1024/1024, 2) | table bytes, size_mb
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode key=frothly_html_memcached.tar.gz http_method=PUT | stats count by _raw
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode key=frothly_html_memcached.tar.gz http_method=PUT | stats count by _time, request_time, http_status, object_size, remote_ip, requester, operation
