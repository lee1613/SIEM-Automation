# s3 - Q217 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=6_
**Scope:** sourcetype=stream:smtp (Bud coin-miner thread images only) | fields: attach_filename, _raw, timestamp, Subject, From, To
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: mail feeds mapped; o365:management:activity has no pcerf mail ops; ess_content_importer/ms:aad:signin dead ends.
- R2: stream:smtp carries full MIME; "Malware Alert Text.txt" = Bruce Gist's; Bud postmortem found with single inline image002.jpg.
- R3: Bud coverage = 4 sent messages; postmortem body unread (encoded) at cap.
- R4: postmortem body decoded — names "coinminer"/100% CPU; attachment = "metrics store search" screenshot; no chart-type word in any body.
- R5: image artifact worked — valid decodable JFIF; MIME/HTML metadata carries no description.
- R6: anchor disproved as Bud's path — PCERF-L 10:24:46–10:33:05 UTC = Billy Tun's "RE: meeting with F" (pwned.jpg); EDT ruled out.
- R7: SOF0 dimensions decoded (image001 3072x870; image002 1088x980; image003 2371x857); no embedded text metadata; web lookups empty.

## This round
### What I ran
- Postmortem HTML img tag decoded from base64 -> `<img width="2113" height="598" ... id="Picture_x0020_1" src="cid:image002.jpg@01D42481.0AB60870">` — no alt/title.
- 13:56:27Z HTML img tags (quoted-printable) -> width/height/id/src only, no alt/o:title.
- Base64 search of postmortem HTML for chart/graph/line/bar/column/area/pie/timechart/Splunk fragments -> only CSS "line;}" false positives.

### What it means
Every in-scope avenue is exhausted: MIME headers, HTML img attributes, body text, JPEG payload structure, dimensions, and embedded-metadata searches carry no visualization name; the pixels cannot be rendered with this tooling. The two-word Splunk visualization type is not recoverable from the available evidence. The strongest defensible conclusion is: the attachments are screenshots of a Splunk metrics store search (image001.jpg 3072x870 being the first illustrating attachment; image002.jpg the postmortem's only attachment). The wide-short aspect is consistent with a time-series chart but does not distinguish line/bar/area — an inference, not evidence, and not submitted. No value; nothing invented.

## Assumptions
- Coverage: stream:smtp Bud-thread image payloads — VERIFIED exhausted (SOF0 dimensions decoded; EOI confirms completeness; no XMP/comment text; no alt/title in HTML; no chart-type vocabulary in any base64 or plain text). JPEG pixel content — not renderable with available tooling; the only carrier of the answer.
- Selection: postmortem as the coin-miner email — VERIFIED (decoded body names the coinminer; only Bud message to all employees about it). First attachment = image002.jpg (postmortem) / image001.jpg (first illustrating message) — VERIFIED as the only attachments present.
- Premise: wide-short 3.5:1 metrics screenshot implies a time-series chart — UNVERIFIED inference; explicitly not submitted.

## Ruled out
- HTML img alt/title attributes as carriers — none exist in either encoding.
- Embedded JPEG metadata (XMP/comments) — no fragments found.
- MIME Content-Description — filename only.
- Body text — only "metrics store search".
- PCERF-L anchor as Bud's postmortem path — Billy Tun's "RE: meeting with F" (pwned.jpg), literal UTC.
- "Malware Alert Text.txt" (Bruce Gist's); Bud's non-incident messages; ms:o365:management, ess_content_importer, ms:aad:signin, o365:management:activity, messagetrace as carriers.

## Open questions for SH
- None. The case can stop here: the two-word visualization type is not recoverable from the available evidence without image-rendering/OCR capability on the base64 JPEG payloads (image001.jpg in the 13:50:47Z event, or image002.jpg in the postmortem event).

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['o365:management:activity', 'ms:o365:reporting:messagetrace', 'stream:smtp'] sources=[] fields=['UserId', 'Operation', 'Subject', 'SenderAddress', 'MessageId', 'DateReceived', 'Size']
- Rounds worked: 8/8  (iterations: 98, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv2 sourcetype=stream:smtp "From: Bud Stoll" | stats count
- index=botsv3 sourcetyp=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: text/plain[^\\\\]*\\\\r\\\\n(?<body>.{1500})" | stats list(body) as body
- index=botsv3 sourcetyp=stream:smtp "pwned.jpg" | rex field=_raw "(?s)Content-Type: text/plain.{0,150}(?<body>.{4000})" | stats list(body) as body
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" earliest=08/20/2018:14:20:00 latest=08/20/2018:14:40:00 | stats count by host, EventCode | sort - count
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=PCERF-L (TargetFilename="*WRD*" OR TargetFilename="*image00*" OR TargetFilename="*.jpg" OR TargetFilename="*.png") | stats count by TargetFilename, Image, _time | sort _time
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=PCERF-L earliest=1534758200 latest=1534758900 | stats count by EventCode, TargetFilename | sort - count
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=PCERF-L earliest=1534774800 latest=1534776000 EventCode=11 | stats count by TargetFilename, Image, _time | sort _time
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=PCERF-L earliest=1534774800 latest=1534776000 | stats count by EventCode | sort - count
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" | stats count, min(_time) as mint, max(_time) as maxt by host | sort - count
- index=botsv3 sourcetype=ms:aad:signin UserId=pcerf@froth.ly OR UserId="peat.cerf@froth.ly" OR UserId="pcerf" | stats count by UserId, _time, IPAddress, ClientApplicationUsed | sort _time
- index=botsv3 sourcetype=ms:aad:signin | stats count by UserId | sort - count
- index=botsv3 sourcetype=ms:o365:management Operation=FileUploaded | stats count by UserId, SourceFileName, SiteUrl | sort - count
- index=botsv3 sourcetype=ms:o365:management Workload=SecurityComplianceCenter OR Workload=Exchange | stats count by Operation, UserId, _time | sort _time
- index=botsv3 sourcetype=ms:o365:management | stats count by Operation, Workload | sort - count
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace | stats count by sender_address, recipient_address, subject | sort - count
- index=botsv3 sourcetype=o365:management:activity earliest=08/20/2018:10:20:00 latest=08/20/2018:10:40:00 | stats count by Operation, UserId, ClientIP | sort - count
- index=botsv3 sourcetype=o365:management:activity earliest=2018-08-20T10:20:00:00Z latest=2018-08-20T10:40:00:00Z | stats count by Operation, UserId, ClientIP | sort - count
- index=botsv3 sourcetype=o365:management:activity UserId=pcerf@froth.ly | stats count by Operation, Workload, ClientIP, _time | sort _time
- index=botsv3 sourcetype=o365:management:activity | stats count, min(_time) as mint, max(_time) as maxt by UserId | sort - count
- index=botsv3 sourcetype=stream:smtp "Bud Stoll" | stats count
- index=botsv3 sourcetype=stream:smtp "From: Bud Stoll" | rex field=_raw "Subject: (?<subj>[^\\\\]*)" | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | rex field=_raw "\"attach_filename\":\[(?<attach>[^\]]*)\]" | stats count by subj, ts, attach | sort ts
- index=botsv3 sourcetype=stream:smtp "image001.jpg" "Bud Stoll" | rex field=_raw "(?s)Content-Type: text/plain.{0,150}(?<body>.{2500})" | stats list(body) as body
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?<metafrag>(eG1w|SUNDX1|U3BsdW5r|Y2hhcnQ|Q1BV|bWV0cmlj|ZGFzaGJvYXJk).{0,80})" max_match=0 | stats list(metafrag) as frags
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?<sof>(/8AAEQ|wAEQI|wAEQC).{0,20})" max_match=0 | stats list(sof) as sofs
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?<sof>(?:/w.AEQ|ABEI).{0,16})" max_match=0 | stats list(sof) as sofs
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?<sof>wAEQ.{0,16})" max_match=0 | stats list(sof) as sofs
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?<tail>.{60})/9k=" | stats list(tail) as tails
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?s)(?<pre>.{0,400})cid:image001.jpg@01D4247C.58AEEAB0" max_match=0 | stats list(pre) as pres
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?s)(?<pre>.{0,450})58AEEAB0" max_match=0 | stats list(pre) as pres
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?s)(?<pre>.{0,450})cid:image001.jpg@01D=\\r\\n4247C.58AEEAB0" max_match=0 | stats list(pre) as pres
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?s).{0,200}(?<ctx>cid:image001[^\"<]{0,80}).{0,400}" max_match=0 | stats list(ctx) as ctxs
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?s).{0,300}(?<ctx>cid:image001.jpg@01D=\\r\\n4247C.58AEEAB0).{0,500}" max_match=0 | stats list(ctx) as ctxs
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?s).{0,350}(?<ctx>cid:image001.jpg@01D4247C.58AEEAB0).{0,350}" max_match=0 | stats list(ctx) as ctxs
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "(?s)cid:image001.jpg@01D4247C.58AEEAB0(?<post>.{0,400})" max_match=0 | stats list(post) as posts
- index=botsv3 sourcetype=stream:smtp "image001.jpg" | rex field=_raw "Content-Transfer-Encoding: base64\\\\r\\\\n\\\\r\\\\n\",\"(?<blob>.{400})" | stats list(blob) as blob
- index=botsv3 sourcetype=stream:smtp "image003.jpg" | rex field=_raw "(?<ctx>(?:alt=3D\"[^\"]{0,80}\"|o:title=\"[^\"]{0,80}\"|title=3D\"[^\"]{0,80}\"))" max_match=0 | stats list(ctx) as ctxs
- index=botsv3 sourcetype=stream:smtp "image003.jpg" | rex field=_raw "(?s)(?<ctx>.{0,80})cid:image00[23].jpg@01D4247D" max_match=0 | stats list(ctx) as ctxs
- index=botsv3 sourcetype=stream:smtp "image003.jpg" | rex field=_raw "(?s)Content-Type: text/plain.{0,150}(?<body>.{1500})" | stats list(body) as body
- index=botsv3 sourcetype=stream:smtp "image003.jpg" | rex field=_raw "Content-Transfer-Encoding: base64\\\\r\\\\n\\\\r\\\\n\",\"(?<blob>.{400})" max_match=0 | stats list(blob) as blobs
- index=botsv3 sourcetype=stream:smtp "image003.jpg" | rex field=_raw "Content-Transfer-Encoding: base64\\r\\n\\r\\n\",\"(?<blob>.{400})" max_match=0 | stats list(blob) as blobs
- index=botsv3 sourcetype=stream:smtp "Malware Alert Text.txt" | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | rex field=_raw "From: (?<from>[^\r\n]*)" | rex field=_raw "Subject: (?<subj>[^\r\n]*)" | stats count by ts, from, subj
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?<frag>(?:PGltZw|BpbWc|aaW1n|YWx0PQ|FsdD0|BsdD0|dGl0bGU9|0aXRsZT0|Gl0bGU9).{0,120})" max_match=0 | stats list(frag) as frags
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?<frag>(?:PGltZ|aW1n|YWx0P|sdD0|bHQ9|dGl0bG|0aXRsZT0|Gl0bGU9).{0,100})" max_match=0 | stats list(frag) as frags
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?<frag>(?:Y2hhcnQ|NoYXJ0|jaGFydA|Z3JhcGg|dyYXBo|ncmFwaA|bGluZQ|saW5l|xpbmU|YmFy|Jhcg|Y29sdW1u|NvbHVtbg|jb2x1bW4|YXJlYQ|FyZWE|cmVhcg|cGll|BpZQ|waWU|dGltZWNoYXJ0|0aW1lY2hhcnQ|U3BsdW5r|NwbHVuaw|wbHVuaw).{0,60})" max_match=0 | stats list(frag) as frags
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?<frag>PGltZyB3aWR0aD0iMjExMyI.{0,400})" max_match=0 | stats list(frag) as frags
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s).{0,60}(?<ctx>cid:image002.{450})" max_match=0 | stats list(ctx) as ctxs
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s).{100}(?<ctx>coin.{500})" | stats list(ctx) as context
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s).{200}(?<ctx>miner.{600})" | stats list(ctx) as context
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s).{200}miner.{600}" | stats list(_raw) as raw
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s).{80}(?<ctx>(?i)(splunk|dashboard|chart|graph|visual|monero|cryptocurr|mining|malware).{400})" max_match=0 | stats list(ctx) as contexts
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: image/jpeg.{0,260}" | stats list(_raw) as hdr
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: image/jpeg.{0,260}(?<hdr>.{0,260})" | stats list(hdr) as headers
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: text/html.{0,120}(?<html>.{2000})" | stats list(html) as html
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: text/plain.{0,150}(?<body>.{1200})" | stats list(body) as body
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: text/plain.{0,150}(?<body>.{3000})" | stats list(body) as body
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: text/plain;[^\\\\]*\\\\r\\\\n[^\\\\]*\\\\r\\\\n\\\\r\\\\n(?<body>.{1800})" | stats list(body) as body
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: text/plain[^\\\\]*\\\\r\\\\n(?<body>.{1500})" | stats list(body) as body
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Subject: Postmortem on our issue with brewertalk.{200}(?<ctx>.{1200})" | stats list(ctx) as context
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "Content-Type: image/jpeg(?<hdr>.{340})" | stats list(hdr) as hdr
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "filename=(?<fn>[^\\\\\"]*)" | stats count by fn
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "filename=[^A-Za-z0-9]*(?<fn>[A-Za-z0-9 ._-]+)" max_match=0 | stats values(fn) as filenames, count by _time
- index=botsv3 sourcetype=stream:smtp "Postmortem on our issue with brewertalk" | rex field=_raw "filename=\"(?<fn>[^\"]*)" max_match=0 | stats values(fn) as filenames, count by _time
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | rex field=_raw "(?s)Content-Type: text/plain.{0,150}(?<body>.{2500})" | stats list(body) as body
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | rex field=_raw "(?s)Content-Type: text/plain.{0,150}(?<body>.{4000})" | stats list(body) as body
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | rex field=_raw "From: (?<from>[^\\\\]*)" | rex field=_raw "Subject: (?<subj>[^\\\\]*)" | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | rex field=_raw "\"attach_filename\":\[(?<attach>[^\]]*)\]" | stats count by from, subj, ts, attach
- index=botsv3 sourcetype=stream:smtp ("chart" OR "graph" OR "dashboard" OR "visualization" OR "metrics store") | rex field=_raw "From: (?<from>[^\\\\]*)" | rex field=_raw "Subject: (?<subj>[^\\\\]*)" | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | stats count by from, subj, ts | sort ts
- index=botsv3 sourcetype=stream:smtp ("From: Bud Stoll" OR "From: Billy Tun") | rex field=_raw "From: (?<from>[^\\\\]*)" | rex field=_raw "Subject: (?<subj>[^\\\\]*)" | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | rex field=_raw "\"attach_filename\":\[(?<attach>[^\]]*)\]" | stats count by from, subj, ts, attach | sort ts
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "\"attach_filename\":\[(?<attach>[^\]]*)\]" | search attach=* | stats count by attach | sort - count
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | rex field=_raw "From: (?<from>[^\r\n]*)" | rex field=_raw "Subject: (?<subj>[^\r\n]*)" | stats count by from, subj, ts | sort ts
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "From: (?<from>[^\\\\]*)" | rex field=_raw "Subject: (?<subj>[^\\\\]*)" | stats count by from, subj | sort - count
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "From: (?<from>[^\\\\]*)" | search from="Bud Stoll <bstoll@froth.ly>" | rex field=_raw "Subject: (?<subj>[^\\\\]*)" | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | rex field=_raw "\"attach_filename\":\[(?<attach>[^\]]*)\]" | stats count by subj, ts, attach | sort ts
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "From: (?<from>[^\\\\]*)" | search from="Bud Stoll*" | rex field=_raw "Subject: (?<subj>[^\\\\]*)" | rex field=_raw "\"timestamp\":\"(?<ts>[^\"]*)\"" | rex field=_raw "\"attach_filename\":\[(?<attach>[^\]]*)\]" | stats count by subj, ts, attach | sort ts
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "From: (?<from>[^\\]*)" | rex field=_raw "Subject: (?<subj>[^\\]*)" | stats count by from, subj | sort - count
- index=botsv3 sourcetype=stream:smtp | stats count by attach_filename, attach_type | sort - count
