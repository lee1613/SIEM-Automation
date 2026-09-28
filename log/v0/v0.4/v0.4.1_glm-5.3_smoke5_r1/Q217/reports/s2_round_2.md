# s2 - Q217 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=11_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="osquery:results" "192.168.8.117" | stats count by host, source
- index=botsv3 sourcetype="stream:http" "192.168.9.25" | stats count min(_time) as first, max(_time) as last by uri_path, src
- index=botsv3 sourcetype="stream:http" ".png" | stats count by uri_path, src, dest
- index=botsv3 sourcetype="bash_history" ("png" OR "scrot" OR "screenshot" OR "import " OR "gnome-screenshot" OR "spectacle") | stats count by host, source
### What it means

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="stream:http" ".png" | stats count by uri_path, src, dest` (50 of 764 rows seen). A claim resting on them alone is UNVERIFIED._
