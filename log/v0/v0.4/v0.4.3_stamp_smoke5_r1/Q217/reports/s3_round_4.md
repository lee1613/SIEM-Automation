# s3 - Q217 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=2_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 (sourcetype=stream:http OR sourcetype=osquery:results OR sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" OR sourcetype=WinEventLog) | stats min(_time) AS earliest max(_time) AS latest count BY sourcetype
- index=botsv3 sourcetype=stream:http ("Splunk chart" OR "metrics store" OR "check it out" OR "allhands" OR "bstoll" OR "Bud Stoll") | stats count by site, uri_path
### What it means
Intention: Check the endpoint feeds (osquery, Sysmon, WinEventLog) for any trace of the thread identifiers (brewertalk, allhands, bstoll, Bud Stoll) — a temp file, cache object, or process command line tied to the thread would appear there.
