# s3 - Q217 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" | top limit=30 target_path
- index=botsv3 sourcetype=osquery:results name="pack_fim_file_events" | stats count by hostIdentifier, columns.category
- index=botsv3 sourcetype=osquery:results | stats count by hostIdentifier
- index=botsv3 sourcetype=osquery:results hostIdentifier=MKRAEUS-L | stats count by name
### What it means
Intention: MKRAEUS-L runs only heartbeat, windows-hardening, and scheduled_tasks queries — no file-path queries. Let me check BSTOLL-L the same way to complete the Windows coverage picture.
