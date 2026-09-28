# s1 - Q205 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=5_
**Scope:** sourcetype=aws:s3:accesslogs | source=s3://frothlyweblogs/* | fields=key, operation, http_status, request_time, remote_ip, requester, bucket_name
**Insight:** FOUND   **Candidate:** OPEN_BUCKET_PLEASE_FIX.txt   **Confidence:** 85

## Prior rounds
- (Round 1) None — this is the first round on this question.

## This round
### What I ran
- get_source_types / get_sources(aws:s3:accesslogs) -> confirmed aws:s3:accesslogs feed exists (1274 events, buckets frothlyweblogs/frothlywebcode/frothlyweb).
- get_sourcetype_fields(aws:s3:accesslogs) -> key fields: bucket_name, key, operation, http_status, requester, remote_ip, request_time.
- `index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode operation="REST.PUT.OBJECT" | stats count by key, http_status, request_time, remote_ip, requester` -> 4 events (full result read): OPEN_BUCKET_PLEASE_FIX.txt 200 @13:02:44 anonymous; frothly_html_memcached.tar.gz 200 @13:04:17 anonymous; frothly_html_memcached.tar.gz 200 @14:19:19 by bstoll; URL-encoded key 403 @14:15:05 (failed).
- CloudTrail queries for the public-access-enabling event (PutBucketAcl/PutBucketPolicy/CreateBucket, `*Bucket*`, frothlywebcode) -> 0 rows each; get_sourcetype_fields(aws:cloudtrail) confirmed camelCase field names.

### What it means
FOUND. The only text file successfully uploaded into frothlywebcode is OPEN_BUCKET_PLEASE_FIX.txt (HTTP 200, REST.PUT.OBJECT, 2018-08-20 13:02:44 UTC). Its requester is "-" (anonymous) from 52.66.146.128 — an unauthenticated successful write is itself positive evidence the bucket was publicly accessible at that moment, so the "while public" condition is satisfied by the record's own content, not just the CloudTrail anchor. The rival .tar.gz uploads are not text files, and the encoded-key PUT failed with 403.

## Ruled out
- frothly_html_memcached.tar.gz (both the anonymous 13:04:17 and bstoll's 14:19:19 PUTs) — .tar.gz archive, not a text file.
- URL-encoded key PUT at 14:15:05 — http_status 403, not a successful upload.
- CloudTrail as the upload evidence source — carries no object-level PUT records for this act; S3 access logs do.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 3 result(s) this round returned only their first rows — `get_sources: {"sourcetype": "aws:s3:accesslogs"}` (50 of 100 rows seen); `get_sourcetype_fields: {"sourcetype": "aws:s3:accesslogs"}` (38 of 76 rows seen); `get_sourcetype_fields: {"sourcetype": "aws:cloudtrail"}` (50 of 429 rows seen). A claim resting on them alone is UNVERIFIED._
