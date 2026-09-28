# s2 - Q225 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=8_
**Scope:** sourcetype=osquery:results, linux_audit | fields=host, name, columns.target_path, columns.command, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 40

## Prior rounds
- Retired scope (s1, r1-2): memcached UDP 13.125.33.130 -> 172.16.0.178:11211 with payloads CRYP70KOL5CH-OWNS-YOU / 6HOUL@G3RpwnzFrothyl4Life; tarball frothly_html_memcached.tar.gz in bucket frothlywebcode; no .jpeg in stream:udp, aws:s3:accesslogs, aws:cloudtrail.
- R1 (mine): bash_history holds only the s3-upload.py upload on mars; access_combined has zero .jpeg/.jpg URIs in 3907 events.
- R2 (this): osquery:results and linux_audit carry no .jpeg/.jpg string; FIM ran only on hoth; no unpack trace of the tarball exists.

## This round
### What I ran
- osquery:results ".jpeg" OR ".jpg" -> 0 events.
- rex _raw for [\w./-]+\.(jpeg|jpg) -> 0 rows; control rex for \.py -> s3-upload.py (3), setup.py (1), proving the pipeline works.
- | stats count by name -> 38 packs; pack_fim_file_events (406) is the only file-inventory feed.
- FIM target_path -> 119 rows, 50 read, all hoth (/etc, /home/klagerfield, /tmp/blargh.tgz, /tmp/colonel, /tmp/loot.txt); host!="hoth" -> 0 (FIM never ran on mars or gacrux).
- rex for .tar.gz -> /home/ec2-user/AWS_SCENARIOS/AWS_ENVIRONMENT/frothly_html_memcaced.tar.gz (mars, 1) plus the two upload-command variants — all shell-history lines.
- get_sourcetype_fields linux_audit -> 112 events, only ADD_USER/ADD_GROUP/CONFIG_CHANGE on gacrux; no file-path fields.

### What it means
NOT_FOUND. Host-side osquery and linux_audit telemetry does not contain the .jpeg filename: no image string exists in any of osquery's 219,997 events (rex-verified against a working control), the only file-inventory pack (FIM) monitored hoth alone and saw no images, and linux_audit carries no file paths at all. The tarball was never unpacked on a monitored host. The filename must live in a feed not yet searched: stream:http bodies (upload POST or defaced page), Sysmon file-create on Windows endpoints, or an S3 object-read in aws:cloudtrail.

## Ruled out
- osquery:results - no .jpeg/.jpg string in 219,997 events (rex with proven control); FIM pack monitored only hoth /etc, /home/klagerfield, /tmp.
- linux_audit - 112 events of user/group management on gacrux; carries no file paths.
- hoth /tmp artifacts (blargh.tgz, colonel, loot.txt, backpipe) - separate netcat/backpipe chain, not the memcached tarball.

## Next
stream:http bodies for the tarball upload or a defaced index.html; Sysmon file-create on Windows; aws:cloudtrail GetObject on frothlywebcode.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "osquery:results"}` (38 of 153 rows seen); `run_splunk_search: index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" | stats count by colum…` (50 of 119 rows seen). A claim resting on them alone is UNVERIFIED._
