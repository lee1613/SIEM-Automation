# s4 - Q217 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=1_
**Scope:** sourcetype=stream:smtp flow_id=8ff70a37-b52e-4810-8203-b00a8d9d8aeb | fields=content{}, _raw, attach_filename, attach_size_decoded
**Insight:** FOUND
**Candidate:** line chart   **Confidence:** 95

## Prior rounds
- R1 (s2/s3): thread mapped; 13:50:47Z email off-topic → first qualifying attachment is image002.jpg at 13:56:27Z; body references "the Splunk chart".
- R2 (retired senior): osquery/Symantec/o365 cannot hold the answer.
- R3 (me): "image002" absent from all five code42:* feeds and WinEventLog/Sysmon/WinHostMon.
- R4 (me): Code42 file inventory (13 names/14 paths, read in full) zero JPGs; Sysmon only pwned.jpg/~WRD000.jpg, earlier and unattributed.
- R5 (me): artifact quoted (flow 8ff70a37, image002.jpg first, 158,643 bytes); body prose quoted; attach_content{} shown not to exist.
- R6 (me): payload located in content{} elements 16–143; verified-clean 211,524-char base64 extracted; read_image rejected it twice (sibling-event pollution suspected).

## This round
### What I ran
- flow 8ff70a37 | where mvcount('content{}')>0 | stats count, len(_raw), mvcount('content{}') -> exactly 1 event: 481,070 chars, 285 content{} elements (the 4 sibling JSON events excluded)
- read_image, extract_spl = same narrowed search + mvjoin(mvindex('content{}',16,143)) + boundary-strip + whitespace-clean + | where isnotnull(img) AND len(img)>200000 | table img -> RENDERED (image002.jpg, 3072x977)

### What it means
FOUND. The recovered image002.jpg rendered successfully and shows a Splunk **line chart**: X-axis `_time` (12:36 AM–1:04 AM, Thursday July 26 2018), Y-axis average `%_Processor_Time` (0–125), legend `chrome`, `chrome#1`–`chrome#9`, spikes around 12:50 AM; the interface itself labels it "Line Chart" under the Visualization tab. The chain is fully verified: Bud's first qualifying illustrative email is the 13:56:27Z "RE: Improved brewertalk.com - check it out!" (body: "Look at the Splunk chart below… CPU of my local Chrome browser… spiked to 100%!" + [cid:image002.jpg@01D4247D.2394E720]); its first attachment is image002.jpg (158,643 bytes decoded); the payload lives in content{} elements 16–143; and the rendered content — chrome instances' processor time spiking — matches the body prose exactly, confirming the right image was read and not the Postmortem's later one. The two earlier render failures were result pollution from the flow's 4 sibling JSON events, not unrenderability. Answer: **line chart** (two words, per format guidance).

## Ruled out
- attach_content{} as the payload field — does not exist; payload is in content{} elements 16–143
- Body prose as the kind's source — read in full; says "the Splunk chart", names no type
- Code42 (all five feeds) — complete file inventory, zero JPGs/attachments
- WinEventLog .jpg activity — 0 events; Sysmon — only pwned.jpg/~WRD000.jpg, earlier unattributed email
- osquery:*/symantec:ep:*/o365 — closed by prior seniors
- "Unrenderable in this environment" — refuted: the isolated payload row rendered cleanly

_Premise updates refused by the runner:_
- p6 stays VERIFIED: its quote is in no result you ran - copy the query output that shows it word for word


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'WinEventLog', 'WinHostMon', 'code42:security', 'code42:api', 'code42:computer', 'code42:user'] sources=[] fields=['host', 'ComputerName', 'Image', 'TargetFilename', 'file_path', 'path', 'filename', 'ObjectId', 'user', 'dest', 'action']
- Rounds worked: 5/8  (iterations: 47, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "image002" | stats count by sourcetype, source
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" ".jpg" | stats count by _time, host, TargetFilename, Image, ProcessGuid
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" ".jpg" | stats count by host, EventCode
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "image002" | stats count by source
- index=botsv3 sourcetype=code42:api "image002" | stats count by source
- index=botsv3 sourcetype=code42:computer OR sourcetype=code42:org OR sourcetype=code42:user "image002" | stats count by sourcetype
- index=botsv3 sourcetype=code42:security "image002" | stats count by source
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace "pwned" | stats count by _time, SenderAddress, RecipientAddress, Subject, Size
- index=botsv3 sourcetype=stream:smtp "image002.jpg" | stats count values(subject) as subject values(mailfrom) as mailfrom values(rcptto) as rcptto values(attachments) as attachments by _time, flow_id
- index=botsv3 sourcetype=stream:smtp "pwned" | stats count values(rcptto) as rcptto values(attachments) as attachments by _time, flow_id, subject, mailfrom
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | stats count values(rcptto) as rcptto values(attachments) as attachments by _time, flow_id, subject, mailfrom
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | eval all=mvjoin('content{}', "") | rex field=all "filename=\"image002\.jpg\"(?s).*?\r\n\r\n(?<img>[A-Za-z0-9+/=\r\n]+?)--" | stats count, values(eval(len(all))) as joined_len, values(eval(len(img))) as img_len
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | eval e143=mvindex('content{}',143) | stats values(eval(len(e143))) as len143, values(eval(substr(e143,-200))) as tail143
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | eval e8=substr(mvindex('content{}',8),1,400), e9=substr(mvindex('content{}',9),1,300), e15=substr(mvindex('content{}',15),1,300), e16=substr(mvindex('content{}',16),1,300) | stats values(e8) as elem8, values(e9) as elem9, values(e15) as elem15, values(e16) as elem16
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | eval i2=mvfind('content{}', "image002"), i3=mvfind('content{}', "image003"), ib=mvfind('content{}', "Content-Type: image/jpeg") | stats values(i2) as idx_image002, values(i3) as idx_image003, values(ib) as idx_jpeg_hdr
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | eval i3=mvfind('content{}', "Content-Description: image003.jpg"), n=mvcount('content{}') | stats values(i3) as idx_image003_header, values(n) as total_elems
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | eval img=mvjoin(mvindex('content{}',16,143), "") | eval img2=replace(img, "\s+", "") | stats count, values(eval(len(img))) as joined_len, values(eval(len(img2))) as cleaned_len, values(eval(substr(img2,1,40))) as head, values(eval(substr(img2,-40))) as tail
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | eval img=mvjoin(mvindex('content{}',16,143), "") | rex field=img mode=sed "s/--_005_BN7PR17MB2257.*//" | eval img=replace(img, "\s+", "") | stats count, values(eval(len(img))) as cleaned_len, values(eval(substr(img,1,30))) as head, values(eval(substr(img,-30))) as tail
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | eval n=mvcount('content{}'), l0=len(mvindex('content{}',0)), l1=len(mvindex('content{}',1)), l2=len(mvindex('content{}',2)), rawlen=len(_raw) | stats values(n) as content_elems, values(l0) as len_elem0, values(l1) as len_elem1, values(l2) as len_elem2, values(rawlen) as raw_len, count as events
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | fieldsummary | table field count distinct_count
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | rex field=_raw "\"(?<attach_key>attach_[a-z_]+)\":" max_match=10 | stats values(attach_key) as keys
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | rex field=_raw "\"(?<content_key>[a-z_]+)\":\"(?=[A-Za-z0-9+/]{500})" max_match=20 | stats values(content_key) as keys
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | rex field=_raw "\"(?<key>[a-z_]+)\":\"(?<b64>[A-Za-z0-9+/=]{2000,})" max_match=10 | stats values(key) as keys, count by b64
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | rex max_match=4 field=_raw "(?<body_context>[^\"]{0,250}[Ss]plunk[^\"]{0,450})" | stats values(body_context) as contexts
- index=botsv3 sourcetype=stream:smtp flow_id="8ff70a37-b52e-4810-8203-b00a8d9d8aeb" | where mvcount('content{}')>0 | stats count, values(eval(len(_raw))) as raw_len, values(eval(mvcount('content{}'))) as content_elems
- index=botsv3 sourcetype=WinEventLog ".jpg" | stats count by host, EventCode
- index=botsv3 sourcetype=WinEventLog "image002" | stats count by source
- index=botsv3 sourcetype=WinHostMon "image002" | stats count by source
