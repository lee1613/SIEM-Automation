# s4 - Q329 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=aws:s3:accesslogs "ba_advertising" | stats count by Operation, bucket, key
- index=botsv3 sourcetype=stream:http "mallorykraeusen" | stats count by http_method, uri, dest_ip
- index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPURI "ba_advertising" | stats count by http_method, uri, dest_ip
- index=botsv3 sourcetype=access_combined method=POST | stats count by file, clientip, status
### What it means
Intention: The 172.16.0.149 client POSTing to member.php/xmlhttp.php is suspicious — check what URIs and user agents this client used across access_combined, to see if it's the attacker and whether it uploaded files.
