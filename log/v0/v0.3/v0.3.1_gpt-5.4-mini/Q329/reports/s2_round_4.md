# s2 - Q329 - Round 4
_stamped by runner: rounds_remaining=3 novel_spl=3_
**Scope:** sourcetype=code42:security,osquery:results | source=code42://frothly_code42_input,/var/log/osquery/osqueryd.results.log | fields=processOwner,deviceGuid,files{}.fileName,files{}.fullPath,files{}.fileEventType,columns.command,columns.path,columns.target_path,host,hostIdentifier,name
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 30

## Prior rounds
Code42 confirmed BudStoll transferred frothly_html_memcached.tar.gz and established the transfer window and deviceGuid.
osquery:results was identified as the needed telemetry family for extraction and browsing evidence.
A raw osquery sample exposed mars.i-08e52f8b5a034012d and a python s3-upload.py command with the target archive name.
The current round mapped the host set and reinforced that the archive was staged under mars, not yet rendered or opened.
No internal filename or large-font word has been verified yet.

## This round
### What I ran
- `run_splunk_search(index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log (hostIdentifier=mars.i-08e52f8b5a034012d OR hostIdentifier=hoth OR hostIdentifier=gacrux.i-0920036c8ca91e501) | stats count by host hostIdentifier name)` -> host map showing hoth, mars.i-08e52f8b5a034012d, and gacrux.i-0920036c8ca91e501.
- `sample_events(sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log keyword=frothly_html_memcached count=10)` -> raw proc-events on mars with `s3-upload.py` cmdlines and target `frothly_html_memcached.tar.gz`, plus typoed source names.
- `run_splunk_search(...)` exact-match on the sampled command string -> no result returned.
### What it means
The osquery evidence points strongly to mars.i-08e52f8b5a034012d as the staging host related to the archive. However, I still lack the post-staging artifact that would show extraction, listing, open, or rendering of an internal HTML file. The oversized word remains unconfirmed.

## Ruled out
- hoth as the only relevant host - it is an osquery endpoint, but the archive-specific raw sample came from mars.
- Code42 as sufficient for content - it only provides file transfer metadata.

## Open questions for SH
- Should I keep the next pass focused on mars.i-08e52f8b5a034012d and exact shell-history/file-event commands there?
- If you know whether the tarball was unpacked into HTML or text content, I can target that file class next.