# s2 - Q329 - Round 5
_stamped by runner: rounds_remaining=2 novel_spl=2_
**Scope:** sourcetype=code42:security,osquery:results | source=code42://frothly_code42_input,/var/log/osquery/osqueryd.results.log | fields=host,hostIdentifier,name,columns.command,columns.path,columns.target_path,files{}.fileName,files{}.fullPath,processOwner,deviceGuid
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 32

## Prior rounds
Code42 fixed the BudStoll archive transfer window and deviceGuid, proving frothly_html_memcached.tar.gz was downloaded and uploaded.
osquery:results was identified as the needed telemetry family for extraction and browsing evidence.
A raw osquery sample exposed mars.i-08e52f8b5a034012d and s3-upload.py cmdline text tied to the target archive.
Host correlation in osquery confirmed mars as the staging host for the archive-linked activity.
No internal filename or rendered-content word has yet been confirmed.

## This round
### What I ran
- `run_splunk_search(index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log (hostIdentifier=mars.i-08e52f8b5a034012d OR hostIdentifier=hoth OR hostIdentifier=gacrux.i-0920036c8ca91e501) | stats count by host hostIdentifier name)` -> host map with mars/hoth/gacrux counts.
- `sample_events(sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log keyword=mars.i-08e52f8b5a034012d count=5)` -> generic process events on mars; no archive path.
- `run_splunk_search(...)` exact archive-token filters on mars -> no results.
### What it means
Mars remains the best-supported staging host, but the archive’s downstream unpack/list/open artifact is still missing. The current scope therefore cannot yet yield the large-font word.

## Ruled out
- hoth as the primary archive host - archive-linked raw sample came from mars.
- Code42 as content evidence - only transfer metadata.
- Exact-match archive token searches on mars - no confirmed extraction/open path returned.

## Open questions for SH
- Can I target a known extracted extension family from the tarball, or should I stay with mars and broaden to nearby file-open/list events?
- Is there a specific user account on mars associated with the upload staging activity?