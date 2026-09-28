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

