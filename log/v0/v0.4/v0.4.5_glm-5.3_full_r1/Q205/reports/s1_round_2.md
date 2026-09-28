# s1 - Q205 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=4_
**Scope:** sourcetype=aws:s3:accesslogs (bucket_name=frothlywebcode) | sourcetype=aws:cloudtrail (eventName=PutBucketAcl) | fields=key, operation, http_status, request_time, requester, eventTime, requestParameters
**Insight:** FOUND   **Candidate:** OPEN_BUCKET_PLEASE_FIX.txt   **Confidence:** 98

## Prior rounds
- Round 1: Found 4 REST.PUT.OBJECT rows on frothlywebcode; only .txt among them was OPEN_BUCKET_PLEASE_FIX.txt (200, anonymous, 13:02:44). CloudTrail anchor unverified (wrong field casing); rivals held open per SH.

## This round
### What I ran
- `sourcetype=aws:cloudtrail eventSource="s3.amazonaws.com" | stats count by eventName` -> 15 eventNames; only write op is PutBucketAcl (2 events); no object-level PutObject in CloudTrail.
- `eventName="PutBucketAcl" | stats count by eventTime, userName, sourceIPAddress` -> 2 events: 13:01:46Z and 13:57:54Z, both bstoll @107.77.212.175.
- get_raw_events(PutBucketAcl) -> 13:01:46Z ACL on frothlywebcode grants AllUsers READ+WRITE (public open); 13:57:54Z ACL has no AllUsers grants (public closed). Window = 13:01:46Z–13:57:54Z.
- `bucket_name=frothlywebcode | stats count by operation, http_status` -> 32 rows; only object-write op is REST.PUT.OBJECT (200=3, 403=1); REST.PUT.ACL (2) are the ACL changes themselves.
- get_raw_events(OPEN_BUCKET_PLEASE_FIX) -> literal key confirmed: `REST.PUT.OBJECT OPEN_BUCKET_PLEASE_FIX.txt "PUT /OPEN_BUCKET_PLEASE_FIX.txt HTTP/1.1" 200` at [20/Aug/2018:13:02:44 +0000], remote 52.66.146.128, requester "-".

### What it means
FOUND. Window bounded by the two PutBucketAcl events (13:01:46Z open, 13:57:54Z close). Successful uploads inside it: OPEN_BUCKET_PLEASE_FIX.txt (13:02:44, .txt — the text file) and frothly_html_memcached.tar.gz (13:04:17, .tar.gz — not text). bstoll's tar.gz PUT at 14:19:19 is after the window closed; the encoded-key PUT at 14:15:05 failed (403) and is also outside. The only text file successfully uploaded while frothlywebcode was public is OPEN_BUCKET_PLEASE_FIX.txt, name unchanged from round 1.

## Ruled out
- frothly_html_memcached.tar.gz @13:04:17 — successful and in-window, but a .tar.gz archive, not a text file.
- frothly_html_memcached.tar.gz @14:19:19 (bstoll) — outside the public window (after 13:57:54Z close).
- URL-encoded-key PUT @14:15:05 — http_status 403 (failed) and outside the window.
- REST.PUT.ACL events — bucket-ACL modifications, not object uploads.
- aws:cloudtrail as upload evidence — no object-level PutObject events exist for this bucket.