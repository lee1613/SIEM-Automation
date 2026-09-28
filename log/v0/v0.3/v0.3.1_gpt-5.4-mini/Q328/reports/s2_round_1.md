# s2 - Q328 - Round 1
_stamped by runner: rounds_remaining=3 novel_spl=0_
**Scope:** sourcetype=osquery:results,bash_history | source=osquery_725_bstollfix.txt | fields=host,hostIdentifier,decorations.username,name,columns.path,columns.action,columns.md5,columns.sha1,columns.sha256
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
1. Bash history and linux audit/ps/osquery FIM had already established the likely file path on hoth.
2. I confirmed hoth exists in osquery:results and that this feed carries scheduled tasks and file-hash metadata.
3. Broad keyword searches for hoth and the target filename returned nothing directly.
4. A raw bash_history sample showed file-transfer behavior via python s3-upload.py, indicating preservation/copy artifacts may exist elsewhere.
5. I did not yet locate any artifact that preserves /tmp/definitelydontinvestigatethisfile.sh contents.
6. No verified line-2 text was recovered this round.

## This round
### What I ran
- `get_source_types()` -> confirmed alternative Linux/server telemetry exists: osquery:results, bash_history, linux_audit, cron, package, syslog, stream:* and others.
- `get_sourcetype_fields(sourcetype="osquery:results", index="botsv3", min_count=1)` -> returned 57 field rows; host=hoth present and source osquery_725_bstollfix.txt identified.
- `get_sourcetype_fields(sourcetype="osquery:results", index="botsv3", source="osquery_725_bstollfix.txt", min_count=1)` -> returned file/task-related fields including columns.path, columns.sha1/sha256, columns.md5, columns.action, columns.name.
- `search_keyword(keyword="definitelydontinvestigatethisfile")` -> no results.
- `sample_events(sourcetype="bash_history", index="botsv3", count=5)` -> showed shell commands including python s3-upload.py transfer activity.
- `get_raw_events(sourcetype="bash_history", index="botsv3", keyword="definitelydont", limit=20)` -> no results.
### What it means
NOT_FOUND: I verified the likely host and that relevant telemetry exists, but I did not reach any artifact preserving the script body or line 2. The evidence points to possible transfer/upload activity, but not the target file itself.

## Ruled out
- Direct keyword presence in Splunk manifests for the exact filename - no hit.
- bash_history as the recovery source - sampled events did not contain the target script.
- osquery:results as directly queried here for line 2 - useful metadata, but no verified content-bearing record recovered in this round.

## Open questions for SH
- Which additional host artifact scope should be prioritized next if a follow-up round is allowed: Linux audit, syslog, cron, package/install logs, or a specific transfer/application feed?

_Iteration cap reached: 8/8 iterations used this round — cut off, not finished._
