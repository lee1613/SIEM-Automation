# s1 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=7_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="stream:smtp" "Subject:" "bstoll@froth.ly" | rex field=_raw "Subject: (?<subject_full>[^\r\n]+)" | eval subject=substr(subject_full,1,60) | stats count, min(_time) as first_time by subject | sort first_time
- index=botsv3 sourcetype="stream:smtp" "Postmortem on our issue with brewertalk" | rex field=_raw "Subject: (?<subject>[^\r\n]+)" | rex field=_raw "From: (?<mail_from>[^\r\n]+)" | rex field=_raw "To: (?<mail_to>[^\r\n]+)" | stats count, values(subject) as subject, values(mail_from) as from, values(mail_to) as to, min(_time) as first_time, max(_time) as last_time
- index=botsv3 sourcetype="stream:smtp" "Postmortem on our issue with brewertalk" | rex field=_raw "From: (?<mail_from>[^\r\n]+)" | rex field=_raw "To: (?<mail_to>[^\r\n]+)" | eval from_short=substr(mail_from,1,40), to_short=substr(mail_to,1,40) | stats count, values(from_short) as from, values(to_short) as first_to, min(_time) as first_time
- index=botsv3 sourcetype="stream:smtp" "Postmortem on our issue with brewertalk" | rex field=_raw "(?s)Content-Type: text/plain;[\s\S]{0,200}(?<body_start>.{0,300})" | stats count, values(body_start) as body
### What it means

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="stream:smtp" "Postmortem on our issue with brewertalk" | rex fiel…` (0 of 1 rows seen). A claim resting on them alone is UNVERIFIED._
