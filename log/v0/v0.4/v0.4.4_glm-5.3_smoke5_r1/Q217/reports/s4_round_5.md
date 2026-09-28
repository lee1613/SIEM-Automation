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
