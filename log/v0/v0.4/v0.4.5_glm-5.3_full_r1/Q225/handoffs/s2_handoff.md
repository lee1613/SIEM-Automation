# s2 - Q225 - Round 5
_stamped by runner: rounds_remaining=0 novel_spl=7_
**Scope:** sourcetype=stream:http, aws:s3:accesslogs, aws:cloudtrail | fields=uri_path, site, status, http_content_length, http_content_type, key, operation, remote_ip, _time
**Insight:** FOUND
**Candidate:** index1.jpeg   **Confidence:** 88

## Prior rounds
- Retired scope (s1, r1-2): memcached UDP 13.125.33.130 -> 172.16.0.178:11211, payloads CRYP70KOL5CH-OWNS-YOU / 6HOUL@G3RpwnzFrothyl4Life; tarball frothly_html_memcached.tar.gz in frothlywebcode; reported zero matches in web/object feeds.
- R1: bash_history holds only the s3-upload.py upload on mars; access_combined has zero .jpeg URIs.
- R2: osquery:results and linux_audit carry no .jpeg/.jpg string (rex-verified with control); FIM ran only on hoth; no unpack trace.
- R3: stream:http rex found image filenames; index1.jpeg identified on two brewery sites; rivals eliminated.
- R4: S3/CloudTrail hold no .jpeg object; tarball GETs by 5 web-server IPs confirmed deployment; FOUND index1.jpeg.
- R5 (this): premises settled with direct quotes; timing corrected; answer unchanged.

## This round
### What I ran
- stream:http ".jpeg" | stats count -> 17 events; by uri_path -> 4 distinct .jpeg files (brunch.jpeg/21st-amendment, index1.jpeg/lilyandhops, 2x fsd.servicemax WordPress).
- Defaced-site kit: site=lilyandhops OR tapsosmitty | stats count by site, uri_path, status -> 9 rows; both sites serve identical kit /, /images/index1.jpeg, /styles/layout.css (lilyandhops: 561B html, 631287B image/jpeg, 6443B css).
- Multi-site image census (rex, dc(site)>1) -> exactly 3 rows: /images/index1.jpeg on 2 brewery sites; two greenflashbrew.com logo .jpgs on one website's two hostnames.
- Tarball timeline: key=frothly_html_memcached.tar.gz -> 20 rows; GETs 21:03-22:25 +08 by 5 IPs, 2 extra PUTs; kit serving was 17:48-19:17 +08.

### What it means
FOUND, unchanged: index1.jpeg. The kit composition is now explicitly quoted — both brewery websites serve the identical three-file kit whose only image is /images/index1.jpeg (631,287 bytes, image/jpeg). The complete census shows it is the only .jpeg on more than one brewery site; every rival is single-site (brunch.jpeg, pwned.jpg, fsd.servicemax WordPress .jpegs) and the only other multi-site images are greenflashbrew.com's own logos on its two hostnames. p3's tokenization mechanism was REFUTED by direct test (term search returns 17 events) — the answer does not depend on it. p4's selection is VERIFIED; its timing clause corrected: the kit was live before the tarball GETs, so the tarball activity is staging/re-deployment.

## Ruled out
- /assets/brunch.jpeg - 21st-amendment.com only, 8,512B normal asset.
- /files/incoming/hoffa/pwned.jpg - temp-e.net only, forum upload, .jpg not .jpeg.
- fsd.servicemax.com WordPress .jpegs - single unrelated domain.
- greenflashbrew.com logo .jpgs - one website's own assets on two hostnames, .jpg not .jpeg.
- aws:s3:accesslogs, aws:cloudtrail - no .jpeg/.jpg object name in either feed.

_Premise updates refused by the runner:_
- p3 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['bash_history', 'osquery:results', 'linux_audit', 'stream:http', 'access_combined'] sources=[] fields=['_raw', 'columns.command', 'name', 'uri_path', 'url', 'file', 'path', 'cmdline']
- Rounds worked: 5/5  (iterations: 48, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "frothly_html_memcached" | stats count by sourcetype, source
- index=botsv3 sourcetype=access_combined ".jpeg" OR ".jpg" | stats count by uri_path, status
- index=botsv3 sourcetype=aws:cloudtrail "memcached" OR "memcaced" | stats count by eventName, requestParameters
- index=botsv3 sourcetype=aws:cloudtrail | rex field=_raw max_match=1 "(?<imgobj>[\w./-]+\.(?:jpeg|jpg))" | stats count by imgobj, eventName
- index=botsv3 sourcetype=aws:s3:accesslogs bucket_name="frothlywebcode" | stats count by key, operation, remote_ip
- index=botsv3 sourcetype=aws:s3:accesslogs key="frothly_html_memcached.tar.gz" | stats count by operation, remote_ip, _time
- index=botsv3 sourcetype=aws:s3:accesslogs operation="REST.GET.OBJECT" OR operation="REST.HEAD.OBJECT" OR operation="REST.PUT.OBJECT" | stats count by bucket_name, key, operation, remote_ip
- index=botsv3 sourcetype=aws:s3:accesslogs | rex field=_raw max_match=1 "(?<imgobj>[\w./-]+\.(?:jpeg|jpg))" | stats count by imgobj, bucket_name
- index=botsv3 sourcetype=bash_history "frothly_html_memcached" | stats count by host, _raw
- index=botsv3 sourcetype=bash_history (tar OR curl OR wget OR unzip) | stats count by host, _raw | sort -_time
- index=botsv3 sourcetype=osquery:results ".jpeg" OR ".jpg" | stats count by host, name
- index=botsv3 sourcetype=osquery:results "memcaced" OR "Taedonggang" OR "taedonggang" | stats count by host, name, columns.command
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" host!="hoth" | stats count by columns.target_path, host
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" | stats count by columns.target_path, host
- index=botsv3 sourcetype=osquery:results | rex field=_raw max_match=1 "(?<pyfile>[\w./-]+\.py)" | stats count by pyfile
- index=botsv3 sourcetype=osquery:results | rex field=_raw max_match=1 "(?<tarball>[\w./-]+\.tar\.gz)" | stats count by tarball, host
- index=botsv3 sourcetype=osquery:results | rex field=_raw max_match=1 "(?i)(?<imgfile>[\w./-]+\.(?:jpeg|jpg))" | stats count by imgfile
- index=botsv3 sourcetype=osquery:results | stats count by name
- index=botsv3 sourcetype=stream:http ".jpeg" | stats count
- index=botsv3 sourcetype=stream:http ".jpeg" | stats count by uri_path, site, http_content_length
- index=botsv3 sourcetype=stream:http "CRYP70KOL5CH" OR "6HOUL" OR "Taedonggang" OR "taedonggang" | stats count by site, uri_path
- index=botsv3 sourcetype=stream:http site="tapsosmitty.com" | stats count by uri_path, status, http_content_type
- index=botsv3 sourcetype=stream:http site="www.lilyandhops.com" OR site="tapsosmitty.com" | stats count by site, uri_path, http_content_length, http_content_type
- index=botsv3 sourcetype=stream:http site="www.lilyandhops.com" OR site="tapsosmitty.com" | stats count by site, uri_path, status
- index=botsv3 sourcetype=stream:http site="www.lilyandhops.com" OR site="tapsosmitty.com" | stats count by site, uri_path, status, http_content_length, http_content_type
- index=botsv3 sourcetype=stream:http site="www.lilyandhops.com" uri_path="/" | stats count by http_user_agent, src_ip, _raw
- index=botsv3 sourcetype=stream:http uri_path="/assets/brunch.jpeg" OR uri_path="/images/index1.jpeg" | stats count by site, uri_path, http_content_length
- index=botsv3 sourcetype=stream:http uri_path="/files/incoming/hoffa/pwned.jpg" | stats count by site, http_content_length, http_method
- index=botsv3 sourcetype=stream:http uri_path="/images/index1.jpeg" | stats count by site, status
- index=botsv3 sourcetype=stream:http | rex field=_raw max_match=1 "(?i)(?<imgfile>[\w./%+-]+\.(?:jpeg|jpg))" | stats count by imgfile
- index=botsv3 sourcetype=stream:http | rex field=_raw max_match=1 "(?i)(?<imgfile>[\w./%+-]+\.(?:jpeg|jpg))" | stats dc(site) as sites, values(site) as site_list, max(http_content_length) as size by imgfile | where sites > 1
- index=botsv3 sourcetype=stream:http | rex field=_raw max_match=1 "(?i)(?<imgfile>[\w./%+-]+\.jpeg)" | stats count by imgfile, site, http_content_length
