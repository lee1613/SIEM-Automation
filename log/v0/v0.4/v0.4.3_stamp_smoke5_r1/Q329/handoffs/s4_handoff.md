# s4 - Q329 - Round 6
_stamped by runner: rounds_remaining=2 novel_spl=9_
**Scope:** sourcetype=stream:smtp | fields=_raw read via substr windows, attachment names via rex
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: literal "taedonggang"/"taedong" absent in o365/smtp; O365 FileUploaded = 7 Frothly-user uploads to own OneDrive.
- R2: code42 UPLOAD set enumerated via mvzip (ba_advertising_code_overview.pdf, frothly_gabf_deck-2018-mk.pptx, frothly_html_memcached.tar.gz); SMTP attachment names listed.
- R3: filename absent from web logs (field-name errors); critic flagged a pivot to unrelated POST traffic.
- R4: upload channel found — 3 anonymous S3 PUTs to frothlywebcode (tarball twice, OPEN_BUCKET_PLEASE_FIX.txt); no content carrier in web feeds.
- R5: downstream traced — EC2 instances pulled the tarball 13:33:34 (defacement live on brewertalk.com), bstoll restored 14:19:19; pwned.jpg email located.

## This round
### What I ran
- Field-filter attempts (attach_filename=, quoted phrases, mvindex(content)) -> all 0; only rex on _raw works on this feed.
- substr windows on the pwned.jpg raw event (offsets 1300–12500, read to the base64 boundary) -> full readable text: btun→pcerf "RE: meeting with F"; the ONLY body text is Peat Cerf's quoted joke about Fyodor's Russian accent and "shrimpchips"; then "Content-Type: image/jpeg; name=\"pwned.jpg\"... base64" and pure image data. No defacement wording.
- substr windows on the "Malware Alert Text.txt" email -> bgist→bstoll/fyodor/ghoppy/abungstein, "Draft Financial Plan for Brewery FY2019", body: "Here is a financial model we can use for FY2019 planning. For the worksheet to operate properly, you will need to enable macros." — the macro lure; attachment is base64 beyond.

### What it means
The two most promising mail artifacts are read to their content boundaries and neither carries the defaced page's wording: pwned.jpg is a bare image with an empty covering message, and the Malware Alert Text.txt attachment is the macro lure document. No feed I could reach exposes the tarball's HTML, and per SH's explicit instruction I do not infer the word from common defacement vocabulary. The word cannot be stated from evidence I hold; the mail path in my scope is exhausted, and the remaining unsearched feeds (messagetrace, endpoint, cloudtrail, two unread emails) are outside what I could still query.

## Ruled out
- pwned.jpg email as a textual source — read in full; only the Fyodor joke, then base64 image.
- "Malware Alert Text.txt" email — macro lure from compromised bgist, not a Taedonggang S3 upload; content base64.
- stream:http / aws:elb:accesslogs / access_combined / aws:s3:accesslogs as content carriers (R4–R5).
- OPEN_BUCKET_PLEASE_FIX.txt — plain text, no font sizing.
- attach_filename / content as search-time fields on stream:smtp — all such filters return 0; rex on _raw is required.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p3 - amend or settle that one. The text you sent was discarded: "The mail-content path for the defacement word is exhausted: the pwned.jpg email "


## What I'd tell my replacement
- Retired because: This senior has now shown that its only plausible content-bearing path in scope does not contain the defacement wording, while the upload/deployment chain alone cannot answer the question. With no spawn slots left and no remaining evidence path inside this scope, further rounds would repeat dead-end checks rather than recover the word.
- Scope I owned: sourcetypes=['code42:security', 'code42:file', 'code42:api', 'code42:user', 'ms:o365:reporting:messagetrace', 'o365:management:activity', 'access_combined', 'stream:http'] sources=[] fields=['file', 'filename', 'object', 'url', 'uri_path', 'attachment', 'title', 'subject', 'user', 'email', '_raw']
- Rounds worked: 6/8  (iterations: 63, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "taedonggang" | stats count by sourcetype, source
- index=botsv3 sourcetype=access_combined "ba_advertising" | stats count by file, clientip, status
- index=botsv3 sourcetype=access_combined clientip="54.241.141.120" OR clientip="52.66.146.128" OR clientip="35.182.246.222" | stats count by file, method, status
- index=botsv3 sourcetype=access_combined method=POST | stats count by file, clientip, status
- index=botsv3 sourcetype=aws:elb:accesslogs earliest=08/20/2018:13:33:00 latest=08/20/2018:14:20:00 | stats count by request_url, elb_status_code
- index=botsv3 sourcetype=aws:s3:accesslogs "ba_advertising" | stats count by Operation, bucket, key
- index=botsv3 sourcetype=aws:s3:accesslogs http_method=PUT requester="-" | stats count by key, bucket_name, remote_ip, http_user_agent
- index=botsv3 sourcetype=aws:s3:accesslogs http_method=PUT | stats count by key, bucket_name, remote_ip, requester
- index=botsv3 sourcetype=aws:s3:accesslogs http_method=PUT | stats count by key, requester, remote_ip
- index=botsv3 sourcetype=aws:s3:accesslogs key="*frothly_html_memcached*" OR key="OPEN_BUCKET_PLEASE_FIX.txt" | stats count, min(request_time) as first_seen, max(request_time) as last_seen by key, http_method, remote_ip, requester
- index=botsv3 sourcetype=aws:s3:accesslogs | stats count by Operation, bucket
- index=botsv3 sourcetype=code42:security files{}.fileEventType=UPLOAD | stats count by files{}.fileName, files{}.fullPath, files{}.mimeType, files{}.length, processOwner, deviceGuid, formattedTimestamp
- index=botsv3 sourcetype=code42:security | eval z=mvzip('files{}.fileName', 'files{}.fileEventType') | mvexpand z | eval fn=mvindex(split(z, ","), 0), ft=mvindex(split(z, ","), 1) | where ft="UPLOAD" | stats count by fn, processOwner
- index=botsv3 sourcetype=o365:management:activity "taedonggang" | stats count by Operation, ObjectId
- index=botsv3 sourcetype=o365:management:activity (Operation=FileSyncUploadedFull OR Operation=FilePreviewed OR Operation=FileModified OR Operation=FileDownloaded) | stats count by Operation, UserId, SourceFileName
- index=botsv3 sourcetype=o365:management:activity Operation="*upload*" OR Operation="*Upload*" | stats count by Operation, ObjectType
- index=botsv3 sourcetype=o365:management:activity Operation=FileUploaded | stats count by UserId, SourceFileName, ObjectId, SiteUrl
- index=botsv3 sourcetype=o365:management:activity UserId=mkraeusen@froth.ly | stats count by Operation, ClientIP, UserAgent, Workload
- index=botsv3 sourcetype=o365:management:activity | stats count by Operation
- index=botsv3 sourcetype=stream:http "ba_advertising" | stats count by http_method, uri, src_ip, dest_ip
- index=botsv3 sourcetype=stream:http "brewertalk" | stats count by uri, http_method
- index=botsv3 sourcetype=stream:http "font-size" | stats count by uri, dest_ip
- index=botsv3 sourcetype=stream:http "frothly_html_memcached" | stats count by uri, http_method, dest_ip
- index=botsv3 sourcetype=stream:http "mallorykraeusen" | stats count by http_method, uri, dest_ip
- index=botsv3 sourcetype=stream:http source=stream:Splunk_HTTPURI "ba_advertising" | stats count by http_method, uri, dest_ip
- index=botsv3 sourcetype=stream:http | top limit=25 uri
- index=botsv3 sourcetype=stream:smtp "ba_advertising" OR "frothly_html_memcached" | stats count by src_user, dest, subject
- index=botsv3 sourcetype=stream:smtp "hacked" OR "defaced" OR "brewertalk" | stats count by subject, from, to
- index=botsv3 sourcetype=stream:smtp "hacked" | stats count by subject, from, to
- index=botsv3 sourcetype=stream:smtp "pwned.jpg" | eval c=mvindex(content,0) | eval w1=substr(c,1200,1200) | eval w2=substr(c,2400,1200) | eval w3=substr(c,3600,1200) | stats first(w1) as w1, first(w2) as w2, first(w3) as w3
- index=botsv3 sourcetype=stream:smtp "taedong" | stats count by src_user, dest
- index=botsv3 sourcetype=stream:smtp ("Employee New Hire Dates" OR "pwned.jpg" OR "Malware Alert Text") | rex field=_raw "(?i)filename=(?<attname>[^\r\n;]+)" | rex field=_raw "(?im)^From: (?<from>[^\r\n]+)" | rex field=_raw "(?im)^To: (?<to>[^\r\n]+)" | rex field=_raw "(?im)^Subject: (?<subj>[^\r\n]+)" | stats count by attname, from, to, subj
- index=botsv3 sourcetype=stream:smtp attach_filename="pwned.jpg" | eval c=mvindex(content,0) | eval w1=substr(c,1200,1200) | eval w2=substr(c,2400,1200) | eval w3=substr(c,3600,1200) | stats first(w1) as w1, first(w2) as w2, first(w3) as w3
- index=botsv3 sourcetype=stream:smtp attach_filename=pwned.jpg | stats count by subject, from, to
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "(?i)filename=(?<attname>[^\r\n;]+)" | search attname="*Malware*" | eval w1=substr(_raw,1300,1400) | eval w2=substr(_raw,2700,1400) | eval w3=substr(_raw,4100,1400) | stats first(w1) as w1, first(w2) as w2, first(w3) as w3
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "(?i)filename=(?<attname>[^\r\n;]+)" | search attname="*pwned*" | eval c=mvindex(content,0) | eval w1=substr(c,1200,1200) | eval w2=substr(c,2400,1200) | eval w3=substr(c,3600,1200) | stats first(w1) as w1, first(w2) as w2, first(w3) as w3
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "(?i)filename=(?<attname>[^\r\n;]+)" | search attname="*pwned*" | eval w1=substr(_raw,1300,1400) | eval w2=substr(_raw,2700,1400) | eval w3=substr(_raw,4100,1400) | stats first(w1) as w1, first(w2) as w2, first(w3) as w3
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "(?i)filename=(?<attname>[^\r\n;]+)" | search attname="*pwned*" | eval w4=substr(_raw,5500,1400) | eval w5=substr(_raw,6900,1400) | eval w6=substr(_raw,8300,1400) | stats first(w4) as w4, first(w5) as w5, first(w6) as w6
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "(?i)filename=(?<attname>[^\r\n;]+)" | search attname="*pwned*" | eval w7=substr(_raw,9700,1400) | eval w8=substr(_raw,11100,1400) | stats first(w7) as w7, first(w8) as w8
- index=botsv3 sourcetype=stream:smtp | rex field=_raw "(?i)filename=(?<attname>[^\r\n;]+)" | stats count by attname
- index=botsv3 sourcetype=stream:smtp | stats count by attach_filename
- index=botsv3 sourcetytype=aws:s3:accesslogs http_method=PUT | stats count by key, requester, remote_ip
