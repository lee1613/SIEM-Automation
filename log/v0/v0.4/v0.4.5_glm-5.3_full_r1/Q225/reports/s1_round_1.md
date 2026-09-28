# s1 - Q225 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:tcp "memcache" | stats count by source
- index=botsv3 sourcetype=stream:udp "memcache" | stats count by source
- index=botsv3 sourcetype=bash_history "Taedonggang" OR "taedonggang" | stats count by host, user
- index=botsv3 sourcetype=stream:http "Taedonggang" | stats count by source
### What it means
Intention: No hex "jpeg" in stream:tcp. Check stream:udp for hex-encoded "jpeg" (6a706567) — memcached amplification attacks use UDP.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
