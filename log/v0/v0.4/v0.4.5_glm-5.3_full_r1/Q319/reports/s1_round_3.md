# s1 - Q319 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=0_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="o365:management:activity" | stats count by Operation
- index=botsv3 sourcetype="ms:o365:management" | stats count by Operation
### What it means
Intention: Re-fetch the raw New-TransportRule event from ms:o365:management to quote its literal Parameters and confirm the identical Id.
