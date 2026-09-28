# s2 - Q225 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:http | rex field=_raw max_match=1 "(?i)(?<imgfile>[\w./%+-]+\.(?:jpeg|jpg))" | stats count by imgfile
- index=botsv3 sourcetype=stream:http site="www.lilyandhops.com" OR site="tapsosmitty.com" | stats count by site, uri_path, status
- index=botsv3 sourcetype=stream:http "CRYP70KOL5CH" OR "6HOUL" OR "Taedonggang" OR "taedonggang" | stats count by site, uri_path
- index=botsv3 sourcetype=stream:http uri_path="/assets/brunch.jpeg" OR uri_path="/images/index1.jpeg" | stats count by site, uri_path, http_content_length
### What it means
Intention: `/assets/brunch.jpeg` is a 8.5KB asset on 21st-amendment.com — a normal site asset, not a 631KB defacement image. Now let me check S3 access logs for the tarball and any .jpeg object names, to tie the defacement kit to the memcached payload deployment.

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:http | rex field=_raw max_match=1 "(?i)(?<imgfile>[\w./%+-]…` (50 of 243 rows seen). A claim resting on them alone is UNVERIFIED._
