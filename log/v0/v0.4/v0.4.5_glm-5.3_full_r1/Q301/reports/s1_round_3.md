# s1 - Q301 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="ms:aad:signin" expired | stats count by userPrincipalName, ipAddress, status.failureReason, resultDescription
- index=botsv3 sourcetype="ms:aad:signin" | stats count by status.failureReason
- index=botsv3 sourcetype="ms:aad:signin" | stats count by failureReason, signinErrorCode
- index=botsv3 sourcetype="ms:aad:signin" signinErrorCode=50055 | stats count by userPrincipalName, ipAddress, loginStatus, appDisplayName
### What it means
Intention: Check whether klagerfield@froth.ly has any successful sign-in (loginStatus=Success) in ms:aad:signin, and from which IP.
