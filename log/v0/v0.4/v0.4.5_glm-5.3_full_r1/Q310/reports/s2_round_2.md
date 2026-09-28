# s2 - Q310 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="ms:o365:reporting:messagetrace" "Wild Birthday Extravaganza" | stats count min(_time) as first max(_time) as last values(Subject) as subjects by SenderAddress
### What it means
Intention: bgist@froth.ly sent the original 11 emails at 17:58:40 (+08:00), one minute after the .lnk upload and 38s after the anonymous link was created. Now read the raw message-trace event to see the email body and confirm it carried the anonymous link to the .lnk file.
