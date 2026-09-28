# s1 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" SenderAddress="bstoll@froth.ly" | stats count by Subject, DateReceived, Size
- index=botsv3 sourcetype=code42:api | stats count by user
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" Subject="*Splunk*" | stats count by Subject, SenderAddress, DateReceived, Size
- index=botsv3 sourcetype="ms:o365:reporting:" (Subject="*restart*" OR Subject="*workstation*") | stats count by Subject, SenderAddress, DateReceived, Size
### What it means

