# s2 - Q329 - Round 2
_stamped by runner: rounds_remaining=5 novel_spl=2_
**Scope:** sourcetype=code42:security,osquery:results | source=code42://frothly_code42_input,/var/log/osquery/osqueryd.results.log | fields=files{}.fileName,files{}.fullPath,files{}.fileEventType,files{}.md5,processOwner,deviceGuid,columns.path,columns.target_path,columns.command,host,hostIdentifier,name
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 25

## Prior rounds
Code42 confirmed frothly_html_memcached.tar.gz was both downloaded and uploaded by BudStoll via chrome.exe.
The archive’s internal content was still unavailable, so the oversized word required downstream file/render evidence.
access_combined field inventory was obtained, but no confirmed archive-name hit or extracted HTML path was found.
osquery:results was identified as a promising file/command telemetry source with columns.command and host metadata.
The current round did not yet yield a concrete extraction or rendered-page artifact tied to the tarball.

## This round
### What I ran
- `get_sources(source="code42://frothly_code42_input")` -> confirmed related high-volume sources including `/var/log/osquery/osqueryd.results.log`.
- `get_sourcetype_fields(sourcetype="osquery:results", source="/var/log/osquery/osqueryd.results.log")` -> showed fields including `columns.command`, `columns.path`, `columns.target_path`, `host`, `hostIdentifier`, `name`.
- `get_field_values(field="columns.command", sourcetype="osquery:results", source="/var/log/osquery/osqueryd.results.log")` -> common commands such as `ls`, `cd ..`, `pwd`, `sudo su`, `ls -latrh`.
- An exact-match SPL attempt on osquery commands returned no results before I could pivot deeper.
### What it means
I confirmed the telemetry family that should reveal extraction or browsing, but I still do not have the file path or HTML artifact needed to recover the oversized word. This scope remains open and needs a narrower exact command/path pivot or browser access evidence.

## Ruled out
- Code42 as sufficient evidence - no file contents, only transfer metadata.
- Generic access_combined search on the archive name - not yet tied to BudStoll content rendering.

## Open questions for SH
- Is BudStoll’s extraction expected to appear in osquery shell history or in browser-access logs next?
- Should I prioritize a specific time window after the upload/download event for the next search?