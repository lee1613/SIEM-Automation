# s1 - Q206 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=7_
**Scope:** sourcetype=aws:s3:accesslogs | bucket_name=frothlywebcode | fields=key, http_method, http_status, object_size, request_time, requester, remote_ip
**Insight:** FOUND
**Candidate:** 2.93   **Confidence:** 95

## Prior rounds
- Q205 (prior context carried in): bucket frothlywebcode; public window 2018-08-20T13:01:46Z–13:57:54Z; in-window .tar.gz upload key frothly_html_memcached.tar.gz.

## This round
### What I ran
- get_sourcetype_fields aws:s3:accesslogs -> object_size field present (values incl. 3076532); key/file_path values include frothly_html_memcached.tar.gz (24 events).
- `index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode key=frothly_html_memcached.tar.gz http_method=PUT | stats count by _time, request_time, http_status, object_size, remote_ip, requester` -> 2 events: 13:04:17Z, status 200, object_size 3076532, requester "-" (anonymous, 35.182.246.222); 14:19:19Z, status 200, object_size 3057116, requester bstoll.
- Epoch-bounded in-window PUT listing (`_time>=1534770106 _time<=1534773474`) -> 4 events: ACL PUTs at 13:01:46Z and 13:57:54Z (key "-"), OPEN_BUCKET_PLEASE_FIX.txt (377 B) at 13:02:44Z, frothly_html_memcached.tar.gz (3076532) at 13:04:17Z — the only .tar.gz in the window.
- Size computation: `... request_time="20/Aug/2018:13:04:17 +0000" | stats max(object_size) as bytes | eval size_mb = round(bytes/1024/1024, 2)` -> bytes=3076532, size_mb=2.93.
- CloudTrail cross-checks: PutObject/free-text for the key -> 0 events; PutBucketAcl on frothlywebcode -> 2 successes at 13:01:46Z and 13:57:54Z, matching the established window.

### What it means
The S3 access log records the successful (http_status 200) PUT of frothly_html_memcached.tar.gz at 13:04:17Z — inside the public-access window (13:01:46Z–13:57:54Z, corroborated by CloudTrail PutBucketAcl successes at both boundaries) — with object_size 3076532 bytes. SPL computed 3076532/1024/1024 = 2.93 MB. The rival 14:19:19Z PUT of the same key (3057116 bytes) falls after the window closed and is excluded.

## Ruled out
- 14:19:19Z PUT of frothly_html_memcached.tar.gz (3057116 bytes, bstoll) - outside the public window (closed 13:57:54Z); would yield 2.91.
- OPEN_BUCKET_PLEASE_FIX.txt (13:02:44Z, 377 bytes) - in window but not a .tar.gz.
- CloudTrail as size source - no PutObject/data event for this key exists in aws:cloudtrail (0 events).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "aws:s3:accesslogs"}` (38 of 76 rows seen). A claim resting on them alone is UNVERIFIED._
