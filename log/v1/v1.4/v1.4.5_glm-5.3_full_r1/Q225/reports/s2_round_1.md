# s2 - Q225 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=4_
**Scope:** sourcetype=bash_history, access_combined | fields=_raw, host, uri, file, root
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 40

## Prior rounds
- Retired scope (s1, rounds 1-2): established memcached UDP conversation 13.125.33.130 -> 172.16.0.178:11211 with payloads CRYP70KOL5CH-OWNS-YOU / 6HOUL@G3RpwnzFrothyl4Life, and tarball frothly_html_memcached.tar.gz in bucket frothlywebcode; no .jpeg filename found in stream:udp, aws:s3:accesslogs, aws:cloudtrail.
- This round (r1): bash_history and access_combined searched for post-upload deployment traces; no .jpeg filename found.

## This round
### What I ran
- sourcetype=bash_history "frothly_html_memcached" | stats count by host,_raw -> 2 events, both on mars.i-08e52f8b5a034012d.
- get_raw_events bash_history keyword=frothly_html_memcached -> 3 lines, all "python /home/ec2-user/tools/s3-upload.py --bucket frothlywebcode --file <frothly_html_memcaced.tar.gz|frothly_web_memcaced.tar.gz> --target frothly_html_memcached.tar.gz".
- Full bash_history read on mars (20 events) -> ls, pwd, s3-upload.py x3, sudo pip install boto3, cd AWS_ENVIRONMENT/, cd AWS_SCENARIOS, splunk restart, vi inputs.conf. No tar extraction, no image name.
- sourcetype=access_combined ".jpeg" OR ".jpg" -> 0 events.
- get_sourcetype_fields access_combined -> 3907 events, 5 gacrux hosts; root=images (660) are MyBB forum assets; no .jpeg/.jpg values in any field.

### What it means
NOT_FOUND. The uploading host's shell history holds only the S3 upload commands — the tarball was never unpacked via a logged shell command, and the web access log serves no .jpeg/.jpg. The filename lives in a feed not yet searched: osquery:results file inventory, stream:http bodies (upload POST / defaced page), linux_audit, or Sysmon file-create events.

## Ruled out
- bash_history (all hosts) - only tarball mention is the s3-upload.py line on mars; no extraction, no image filename.
- access_combined - zero .jpeg/.jpg URIs across all 3907 events; images/ requests are MyBB forum assets.
- ping_ip wget of http://178.128.11.199/rvs on brewertalk.com - separate router-exploit activity, unrelated to the memcached tarball.

## Next
osquery:results for paths ending .jpeg/.jpg on mars/gacrux; stream:http bodies for the tarball upload or a defaced index.html referencing the image; linux_audit and Sysmon file-create events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
