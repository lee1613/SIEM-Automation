# s1 - Q217 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=8_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="stream:smtp" "image002.jpg" | rex field=_raw "(?s).{0,200}name=\"image002.jpg\"(?<after>.{0,400})" | stats count, values(after) as after_context, min(_time) as first_time
- index=botsv3 sourcetype="stream:smtp" "image002.jpg" | rex field=_raw "(?s)name=\"image002.jpg\"(?<after>.{0,150})" | stats count, values(after) as after_context, min(_time) as first_time, max(_time) as last_time
- index=botsv3 sourcetype="stream:smtp" "image002.jpg" | rex field=_raw "(?s)Subject: (?<subject>[^\r\n]{0,50})" | rex field=_raw "(?s)From: (?<mail_from>[^\r\n]{0,40})" | rex field=_raw "(?s)To: (?<mail_to>[^\r\n]{0,40})" | stats count, values(subject) as subjects, values(mail_from) as froms, values(mail_to) as tos, min(_time) as first_time, max(_time) as last_time
- index=botsv3 sourceteype="stream:smtp" "image002.jpg" | rex field=_raw "(?s)Subject: (?<subject>[^\r\n]{0,50})" | rex field=_raw "(?s)Date: (?<mail_date>[^\r\n]{0,40})" | stats count, values(subject) as subjects, values(mail_date) as dates, min(_time) _time, max(_time) as last_time
### What it means



## What I'd tell my replacement
- Retired because: Retiring under anti-thrash: two consecutive rounds failed to produce a usable report, but its handoff is still valuable. Carry forward that Bud is bstoll@froth.ly; stream:smtp contains attachment indicators via name= rather than filename=; confirmed attachment names include image002.jpg, Malware Alert Text.txt, 1534778082419.png, and winmail.dat; and image002.jpg appears in Bud-related brewertalk/coinminer emails including 'Postmortem on our issue with brewertalk' and 'RE: Improved brewertalk.com - check it out!'.
- Scope I owned: sourcetypes=['ms:o365:reporting:messagetrace', 'o365:management:activity', 'ms:o365:management'] sources=['ms_o365_message_trace'] fields=['SenderAddress', 'RecipientAddress', 'Subject', 'Attachment*', 'Message*', 'NetworkMessageId', 'CreationTime', 'Operation', 'UserId', 'Parameters']
- Rounds worked: 5/8  (iterations: 57, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourceteype="stream:smtp" "image002.jpg" | rex field=_raw "(?s)Subject: (?<subject>[^\r\n]{0,50})" | rex field=_raw "(?s)Date: (?<mail_date>[^\r\n]{0,40})" | stats count, values(subject) as subjects, values(mail_date) as dates, min(_time) _time, max(_time) as last_time
- index=botsv3 sourceteype="stream:smtp" "name=" | rex field=_raw "(?s).{0,40}name=(?<ctx>.{0,60})" | stats count, values(ctx) as context, min(_time) as first_time by ctx | sort first_time
- index=botsv3 sourceteype="stream:smtp" "Subject:" "btun@froth.py" | rex field=_raw "Subject: (?<subject>[^\r\n]+)" | table subject | dedup subject
- index=botsv3 sourcetype="ms:o365:management" "bstoll@froth.ly" (Operation="FileAccessed" OR Operation="SharingSet" OR Operation="AnonymousLinkUsed" OR Operation="PageViewed" OR Operation="AddedToGroup") | stats count by Operation, ObjectId, SourceFileName
- index=botsv3 sourcetype="ms:o365:management" "bstoll@froth.ly" | stats count by Operation, Workload
- index=botsv3 sourcetype="ms:o365:management" "btun@froth.ly" Operation="SearchExported" OR Operation="PreviewItemRendered" OR Operation="PreviewItemListed" | stats count by Operation, _time
- index=botsv3 sourcetype="ms:o365:management" "btun@froth.ly" | stats count by Operation, Workload
- index=botsv3 sourcetype="ms:o365:management" Operation="SearchExported" | stats count by ObjectId, Parameters
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" SenderAddress="bstoll@froth.ly" | stats count, min(_time) as first_time by Subject | sort first_time
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" SenderAddress="btun@froth.ly" | stats count, min(_time) as first_seen, values(Subject) as subjects by RecipientAddress | sort first_seen
- index=botsv3 sourcetype="o365:management:activity" "btun@froth.ly" | stats count by Operation, Workload
- index=botsv3 sourcetype="stream:smtp" "Content-Disposition" | stats count
- index=botsv3 sourcetype="stream:smtp" "filename=" | rex field=_raw "filename=(\"(?<fname>[^\"]+)|(?<fname2>[^;\r\n]+))" | stats count, min(_time) as first_time by fname, fname2
- index=botsv3 sourcetype="stream:smtp" "image002.jpg" | rex field=_raw "(?s).{0,200}name=\"image002.jpg\"(?<after>.{0,400})" | stats count, values(after) as after_context, min(_time) as first_time
- index=botsv3 sourcetype="stream:smtp" "image002.jpg" | rex field=_raw "(?s)name=\"image002.jpg\"(?<after>.{0,150})" | stats count, values(after) as after_context, min(_time) as first_time, max(_time) as last_time
- index=botsv3 sourcetype="stream:smtp" "image002.jpg" | rex field=_raw "(?s)Subject: (?<subject>[^\r\n]{0,50})" | rex field=_raw "(?s)From: (?<mail_from>[^\r\n]{0,40})" | rex field=_raw "(?s)To: (?<mail_to>[^\r\n]{0,40})" | stats count, values(subject) as subjects, values(mail_from) as froms, values(mail_to) as tos, min(_time) as first_time, max(_time) as last_time
- index=botsv3 sourcetype="stream:smtp" "name=" | rex field=_raw "(?s).{0,40}name=(?<ctx>.{0,60})" | stats count, min(_time) as first_time by ctx | sort first_time
- index=botsv3 sourcetype="stream:smtp" "name=" | rex field=_raw "name=(\"(?<fname>[^\"]+)\"|(?<fname2>[^;\r\n]+))" | stats count, min(_time) as first_time by fname, fname2 | sort first_time
- index=botsv3 sourcetype="stream:smtp" "name=" | stats count
- index=botsv3 sourcetype="stream:smtp" "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: text/plain;[\s\S]{0,200}(?<body_start>.{0,300})" | stats count, values(body_start) as body
- index=botsv3 sourcetype="stream:smtp" "Postmortem on our issue with brewertalk" | rex field=_raw "From: (?<mail_from>[^\r\n]+)" | rex field=_raw "To: (?<mail_to>[^\r\n]+)" | eval from_short=substr(mail_from,1,40), to_short=substr(mail_to,1,40) | stats count, values(from_short) as from, values(to_short) as first_to, min(_time) as first_time
- index=botsv3 sourcetype="stream:smtp" "Postmortem on our issue with brewertalk" | rex field=_raw "Subject: (?<subject>[^\r\n]+)" | rex field=_raw "From: (?<mail_from>[^\r\n]+)" | rex field=_raw "To: (?<mail_to>[^\r\n]+)" | stats count, values(subject) as subject, values(mail_from) as from, values(mail_to) as to, min(_time) as first_time, max(_time) as last_time
- index=botsv3 sourcetype="stream:smtp" "Subject:" "bstoll@froth.ly" | rex field=_raw "Subject: (?<subject_full>[^\r\n]+)" | eval subject=substr(subject_full,1,60) | stats count, min(_time) as first_time by subject | sort first_time
- index=botsv3 sourcetype="stream:smtp" "Subject:" "btun@froth.ly" | rex field=_raw "Subject: (?<subject>[^\r\n]+)" | stats count by subject
- index=botsv3 sourcetype="stream:smtp" "Subject:" "btun@froth.ly" | rex field=_raw "Subject: (?<subject>[^\r\n]+)" | stats count, min(_time) as first_time by subject | sort first_time
- index=botsv3 sourcetype="stream:smtp" "Subject:" "btun@froth.ly" | rex field=_raw "Subject: (?<subject_full>[^\r\n]+)" | eval subject=substr(subject_full,1,60) | stats count, min(_time) as first_time by subject | sort first_time
- index=botsv3 sourcetype="stream:smtp" "Subject:" | rex field=_raw "Subject: (?<subject>[^\r\n]+)" | rex field=_raw "From: (?<mail_from>[^\r\n]+)" | rex field=_raw "To: (?<mail_to>[^\r\n]+)" | stats count, min(_time) as first_time by subject, mail_from, mail_to | sort first_time
- index=botsv3 sourcetype="stream:smtp" "Subject:" | stats count
- index=botsv3 sourcetype="stream:smtp" content_type="multipart/mixed*" | stats count by content_type
- index=botsv3 sourcetype="stream:smtp" content_type=* | head 1 | stats list(_raw) as raw
- index=botsv3 sourcetype="stream:smtp" content_type=* | rex field=_raw "\"from\":\"(?<mail_from>[^\"]+)\"" | rex field=_raw "\"to\":\"(?<mail_to>[^\"]+)\"" | stats count, min(_time) as first_time, max(_time) as last_time by mail_from, mail_to
- index=botsv3 sourcetype="stream:smtp" content_type=* | stats count by sourcetype, source
- index=botsv3 sourcetype="stream:smtp" | stats count by content_type
- index=bpl stream:smtp "Subject:" | stats count
