# s3 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=2_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 (source="cisconvmsysdata" OR source="cisconvmifdata") (monero OR xmr OR coin OR mine OR miner OR pool OR stratum OR duration OR seconds OR bytes OR flow) | stats count
- index=botsv3 sourcetype=syslog (source="cisconvmsysdata" OR source="cisconvmifdata") (monero OR xmr OR coin OR mine OR miner OR pool OR stratum OR duration OR seconds OR bytes OR flow) | stats count
### What it means
Intention: Get the complete fieldsummary for cisconvmifdata to complete the schema check on both sibling sources.
