# s2 - Q202 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=top | stats count by host
### What it means
Intention: `top` covers gacrux.i-0920036c8ca91e501 (23,917 events) — Unix TA top output can carry a CPU-model header. I'll search that host's top and ps events for a processor string (Xeon/Intel), and sample raw top events to see the header structure.
