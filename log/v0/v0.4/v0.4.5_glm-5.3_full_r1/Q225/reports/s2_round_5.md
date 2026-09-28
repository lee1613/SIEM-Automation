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
