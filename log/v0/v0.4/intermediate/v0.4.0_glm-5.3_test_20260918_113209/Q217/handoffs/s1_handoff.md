# s1 - Q217 - Round 7
_stamped by runner: rounds_remaining=1 novel_spl=8_
**Scope:** sourcetype=stream:smtp, stream:http, ms:o365:reporting:messagetrace | fields=content, _raw, attach_filename, url, src, dest, Subject, RecipientAddress, DateReceived
**Insight:** NOT_FOUND
**Candidate:** none (visualization type unknown; attachment = pwned.jpg, established)   **Confidence:** 15

## Prior rounds
- R1: Mapped 102 sourcetypes; Bud=btun@froth.ly; 13 outbound subjects; messagetrace carries no attachment fields.
- R2: "RE: Splunk service needs a restart" (09:47:48Z) proven attachment-free; Bud's MIME attachments: pwned.jpg (10:24:29Z), Employee New Hire Dates.xlsx (11:11:17Z).
- R3: Exchange audit = admin cmdlets; FilePreviewed = birthday/beer files; discovered structured attach_* fields + full MIME `content` in stream:smtp.
- R4: Full 11-event attachment inventory; both Bud bodies read — pwned.jpg thread is Fyodor banter, xlsx is HR; messagetrace sizes confirm no other Bud attachment.
- R5: Traced pwned.jpg origin — BTUN-L downloaded it from temp-e.net/files/incoming/hoffa/ at 10:22:47Z, 2 min before emailing.
- R6: Sysmon puts pwned.jpg on disk on both endpoints; recipient opened it twice; PowerPoint ran later but is unlinked.
- R7 (this round): second HTTP event is a flow aggregate, not a new fetch; every Bud thread body now read; chart-type vocabulary returns 0 events dataset-wide.

## This round
### What I ran
- stream:http "pwned" full-raw extraction -> 10:23:37Z event is an aggregate of the 10:22:47Z flow (same flow_id/uri/bytes); download referrer = bing.com, content-type image/jpeg
- stream:smtp "pwned.jpg" text/html extraction -> Word CSS boilerplate only, no img alt/caption
- "Malware Alert Text.txt" body -> generic malware-stripped notice, unrelated
- "RE: Splunk service needs a restart" bodies (5 events) -> UBA install request + reply-all banter, no chart mention
- "IoT brewery stuff" body -> IoT home-brewing product question
- "FW: Bruce Gist" bodies (4 events) -> Bruce account deactivation
- (stream:smtp OR stream:http) chart-type vocabulary search -> 0 events

### What it means
NOT_FOUND for the visualization type. The artifact chain is complete and verified end-to-end (bing.com image search -> temp-e.net download -> outbound attachment -> on-disk on both endpoints), but the image's content exists only as base64 in MIME and as HTTP response bytes. Every Bud thread body has now been read in full; none describes the image or names a chart. The literal two-word chart vocabulary (line/column/pie/area/bar/scatter chart) returns zero events in mail and web feeds. I did not decode the image and will not guess a chart type. The attachment half of the question is solved (pwned.jpg); the visualization half is not answerable from the indexed text evidence available to me.

## Ruled out
- Second

_[truncated at 400 words]_

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._


## What I'd tell my replacement
- Retired because: This senior is done for now: it proved the attachment chain for pwned.jpg and exhausted mail, HTTP, and endpoint text evidence without recovering the two-word visualization type. The unresolved handoff is narrow and durable: any future work must target a source that can reveal the image contents or an indexed artifact derived from the image itself, because current evidence does not literally establish the chart type.
- Scope I owned: sourcetypes=['ms:o365:management', 'ms:o365:reporting:messagetrace', 'o365:management:activity', 'ms:aad:signin', 'code42:security', 'code42:user', 'code42:computer'] sources=[] fields=['sender', 'recipient', 'subject', 'attachment', 'attachments', 'file_name', 'message_id', 'user', 'operation', 'workload', 'path', 'url']
- Rounds worked: 7/8  (iterations: 63, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 (sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" OR sourcetype=WinHostMon OR sourcetype=osquery:results OR sourcetype=aws:s3:accesslogs OR sourcetype=stream:http) "pwned" | stats count by sourcetype
- index=botsv3 (sourcetype=osquery:results OR sourcetype=symantec:ep:agent:file OR sourcetype=symantec:ep:traffic:file OR sourcetype=symantec:ep:packet:file OR sourcetype=symantec:ep:behavior:file OR sourcetype=code42:security OR sourcetype=code42:user OR sourcetype=o365:management:activity OR sourcetype=stream:http OR sourcetype=stream:smb) "pwned" | stats count by sourcetype
- index=botsv3 (sourcetype=stream:smtp OR sourcetype=stream:http) ("line chart" OR "column chart" OR "pie chart" OR "area chart" OR "bar chart" OR "scatter chart") | stats count by sourcetype
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "PCERF-L" "POWERPNT" | rex field=_raw "EventID\x3E(?<eid>\d+)" | rex field=_raw "Name\x3D\x27TargetFilename\x27\x3E(?<target>[^\x3C]+)" | rex field=_raw "Name\x3D\x27UtcTime\x27\x3E(?<utctime>[^\x3C]+)" | search target=* | stats count values(target) as targets by utctime, eid | sort utctime
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "PCERF-L" "POWERPNT" | rex field=_raw "Name\x3D\x27CommandLine\x27\x3E(?<cmdline>[^\x3C]+)" | rex field=_raw "Name\x3D\x27UtcTime\x27\x3E(?<utctime>[^\x3C]+)" | stats count values(cmdline) as cmdlines by utctime | sort utctime
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "PCERF-L" | rex field=_raw "EventID\x3E(?<eid>\d+)" | rex field=_raw "Name\x3D\x27Image\x27\x3E(?<image>[^\x3C]+)" | stats count values(image) as images by eid | sort -count
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "pwned" | head 1 | eval snippet=substr(_raw,1,1200) | stats values(snippet) as raw_start
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "pwned" | rex field=_raw "(?i)TargetFilename\x22>(?<target>[^<]+)" | rex field=_raw "(?i)Image\x22>(?<image>[^<]+)" | rex field=_raw "(?i)CommandLine\x22>(?<cmdline>[^<]+)" | stats count values(target) as targets values(image) as images values(cmdline) as cmdlines by _time
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "pwned" | rex field=_raw "Computer\x3E(?<computer>[^\x3C]+)" | rex field=_raw "Name\x3D\x27Image\x27\x3E(?<image>[^\x3C]+)" | rex field=_raw "Name\x3D\x27TargetFilename\x27\x3E(?<target>[^\x3C]+)" | rex field=_raw "Name\x3D\x27UtcTime\x27\x3E(?<utctime>[^\x3C]+)" | stats count values(computer) as computers values(image) as images values(target) as targets by utctime | sort utctime
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" Computer="PCERF-L.froth.ly" earliest="08/20/2018:10:25:00" latest="08/20/2018:10:40:00" | rex field=_raw "EventID\x3E(?<eid>\d+)" | rex field=_raw "Name\x3D\x27Image\x27\x3E(?<image>[^\x3C]+)" | stats count values(image) as images by eid | sort -count
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress="btun@froth.ly" | stats count by Subject | sort Subject
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress="btun@froth.ly" | stats count min(DateReceived) as first max(DateReceived) as last by Subject, RecipientAddress | sort first
- index=botsv3 sourcetype=ms:o365:reporting:messagetrace SenderAddress="btun@froth.ly" | stats count values(Size) as sizes by Subject, DateReceived | sort DateReceived
- index=botsv3 sourcetype=o365:management:activity Operation="FilePreviewed" | stats count by ObjectId, UserId, CreationTime | sort CreationTime
- index=botsv3 sourcetype=o365:management:activity Workload=Exchange | stats count by Operation, UserId, CreationTime | sort CreationTime
- index=botsv3 sourcetype=stream:http "pwned" | eval snippet=substr(_raw,1,1500) | stats values(snippet) as raw_start by timestamp
- index=botsv3 sourcetype=stream:http "pwned" | rex field=_raw "(?i)(GET|POST)\s+(?<url>\S+)" | rex field=_raw "(?i)Host:\s*(?<host>[^\x5c\"]+)" | rex field=_raw "(?i)User-Agent:\s*(?<ua>[^\x5c\"]+)" | stats count values(url) as urls values(host) as hosts values(ua) as user_agents values(bytes) as byte_counts by timestamp, src_ip, dest_ip
- index=botsv3 sourcetype=stream:http "pwned" | rex field=_raw "(?i)(GET|POST)\s+(?<url>\S+)" | rex field=_raw "(?i)Host:\s*(?<host>[^\x5c\"]+)" | stats count values(url) as urls values(host) as hosts values(bytes) as byte_counts by timestamp, src_ip
- index=botsv3 sourcetype=stream:http "pwned" | rex field=_raw "(?i)(GET|POST)\s+(?<url>\S+)" | stats count values(url) as urls by timestamp, src_ip, dest_ip
- index=botsv3 sourcetype=stream:http "pwned" | rex field=_raw "(?i)GET\s+(?<url>\S+)" | rex field=_raw "(?i)Host:\s*(?<host>[^\x5c\"]+)" | stats count values(url) as urls values(host) as hosts by timestamp, src_ip
- index=botsv3 sourcetype=stream:http "pwned" | rex field=_raw "content_type\x22:\x5b\x22(?<ctype>[^\x22]+)" | rex field=_raw "status\x22:(?<status>\d+)" | stats count values(ctype) as content_types values(status) as statuses values(bytes) as byte_counts by timestamp
- index=botsv3 sourcetype=stream:http "temp-e.net" | rex field=_raw "(?i)(GET|POST)\s+(?<url>\S+)" | stats count values(url) as urls by timestamp, src_ip
- index=botsv3 sourcetype=stream:http src_ip="192.168.3.130" earliest="08/20/2018:10:15:00" latest="08/20/2018:10:35:00" | rex field=_raw "(?i)(GET|POST)\s+(?<url>\S+)" | stats count values(url) as urls by timestamp, dest_ip | sort timestamp
- index=botsv3 sourcetype=stream:http src_ip="192.168.3.130" earliest=2018-08-20T10:15:00 latest=2018-08-20T10:35:00 | rex field=_raw "(?i)(GET|POST)\s+(?<url>\S+)" | stats count values(url) as urls by timestamp, dest_ip | sort timestamp
- index=botsv3 sourcetype=stream:http src_ip="192.168.3.130" | rex field=_raw "(?i)(GET|POST)\s+(?<url>\S+)" | stats count values(url) as urls by timestamp, dest_ip | sort timestamp
- index=botsv3 sourcetype=stream:smtp "btun@froth.ly" | head 1 | eval snippet=substr(_raw,1,900) | stats values(snippet) as raw_start
- index=botsv3 sourcetype=stream:smtp "btun@froth.ly" | rex field=_raw "(?i)Subject:\s*(?<subj>[^\\]{1,70})" | stats count by subj, timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "btun@froth.ly" | rex field=_raw "(?i)Subject:\s*(?<subj>[^\r\n]+)" | stats count values(subj) as subjects by timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "btun@froth.ly" | rex field=_raw "(?i)Subject:\s*(?<subj>[^\r\n]{1,60})" | stats count by subj, timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "btun@froth.ly" | rex field=_raw "(?i)Subject:\s*(?<subj>[^\x5c]{1,70})" | stats count by subj, timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "coin" | stats count by src_ip, timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "Employee New Hire Dates" | rex field=_raw "(?i)Subject:\s*(?<subj>[^\r\n]+)" | rex field=_raw "(?i)To:\s*(?<to>[^\r\n]+)" | stats count values(subj) as subject values(to) as to by timestamp
- index=botsv3 sourcetype=stream:smtp "Employee New Hire Dates" | rex field=_raw "text/plain;.{0,40}(?<body>.{1,700})" | stats values(body) as body_text by timestamp
- index=botsv3 sourcetype=stream:smtp "filename" | rex field=_raw "(?i)From:\s*[^\r\n<]*<?(?<sender>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)" | rex field=_raw "filename=(?<fname>[^\r\n;\"]+)" | stats count values(fname) as filenames values(sender) as senders by timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "filename" | rex field=_raw "filename=(?<fname>[^\r\n;]+)" | rex field=_raw "(?i)From:\s*(?<sender>[^\r\n]+)" | rex field=_raw "(?i)Subject:\s*(?<subj>[^\r\n]+)" | stats count values(fname) as filenames values(sender) as senders values(subj) as subjects by timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "filename" | rex field=_raw "filename=(?<fname>[^\r\n;]+)" | stats count values(fname) as filenames by src_ip, timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "filename" | stats count by content_type
- index=botsv3 sourcetype=stream:smtp "FW: Bruce Gist" | rex field=_raw "text/plain;.{0,60}(?<body>.{1,1200})" | stats count values(body) as body_texts by timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "IoT brewery stuff" | rex field=_raw "text/plain;.{0,60}(?<body>.{1,1200})" | stats count values(body) as body_texts by timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "Malware Alert Text" | rex field=_raw "text/plain;.{0,60}(?<body>.{1,1200})" | stats values(body) as body_text by timestamp
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | eval has_plain=if(searchmatch("text/plain"),"YES","NO") | eval has_html=if(searchmatch("text/html"),"YES","NO") | stats count values(has_plain) values(has_html) by timestamp
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | rex field=_raw "(?i)Subject:\s*(?<subj>[^\r\n]+)" | rex field=_raw "(?i)To:\s*(?<to>[^\r\n]+)" | stats count values(subj) as subject values(to) as to by timestamp
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | rex field=_raw "text/html;.{0,60}(?<htmlbody>.{1,1500})" | stats values(htmlbody) as html_body by timestamp
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | rex field=_raw "text/plain;.{0,40}(?<body>.{1,700})" | stats values(body) as body_text by timestamp
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | rex field=content "text/plain;.{0,80}(?<body>.{1,600})" | stats values(body) as body_text by timestamp
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | rex field=content "text/plain;[^\x22]{0,60}?\x5cr\x5cn\x5cr\x5cn(?<body>[^\x22]{1,500})" | stats values(body) as body_text by timestamp
- index=botsv3 sourcetype=stream:smtp "Splunk service needs a restart" | rex field=_raw "text/plain;.{0,60}(?<body>.{1,1200})" | stats count values(body) as body_texts by timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp "workstations" | stats count by content_type
- index=botsv3 sourcetype=stream:smtp ("miner" OR "mining" OR "monero" OR "cryptocurrency" OR "bitcoin") | stats count by timestamp
- index=botsv3 sourcetype=stream:smtp attach_filename="*" | stats count by attach_filename, attach_type | sort attach_filename
- index=botsv3 sourcetype=stream:smtp attach_filename=* | rex field=content "(?i)From:[^\x5c]{0,80}?(?<from>[A-Za-z0-9._%+-]+@froth\.ly)" | rex field=content "(?i)Subject:\x5cr\x5cn\s*(?<subj>[^\x5c]{1,80})" | stats count values(attach_filename) as attachments values(attach_type) as types values(subj) as subject values(from) as sender by timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "attach_filename.{0,6}(?<af>[A-Za-z0-9._%+-]+\.[A-Za-z0-9]{2,5})" | search af=* | rex field=_raw "(?i)From:\s*[^\x5c<]*<?(?<sender>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)" | rex field=_raw "(?i)Subject:\x5cr\x5cn\s*(?<subj>[^\x5c]{1,80})" | stats count values(af) as attachments values(sender) as senders values(subj) as subjects by timestamp | sort timestamp
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "attach_filename\x22:\x5b\x22(?<af>[^\x22]+)" | search af=* | rex field=_raw "(?i)From:\s*[^\x5c<]*<?(?<sender>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)" | rex field=_raw "(?i)Subject:\x5cr\x5cn\s*(?<subj>[^\x5c]{1,80})" | stats count values(af) as attachments values(sender) as senders values(subj) as subjects by timestamp | sort timestamp
