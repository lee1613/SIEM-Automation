# s2 - Q329 - Round 3
_stamped by runner: rounds_remaining=4 novel_spl=5_
**Scope:** sourcetype=code42:security,osquery:results | source=code42://frothly_code42_input,/var/log/osquery/osqueryd.results.log | fields=processOwner,deviceGuid,files{}.fileName,files{}.fullPath,files{}.fileEventType,columns.command,columns.path,columns.target_path,host,hostIdentifier,name
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 28

## Prior rounds
Code42 confirmed frothly_html_memcached.tar.gz was downloaded to BudStoll's Downloads and uploaded from BudStoll's Desktop via chrome.exe.
access_combined was mapped, but no archive-name hit or extracted HTML path was found there.
osquery:results contains file/command telemetry and was identified as the right family for extraction/browsing evidence.
The previous round did not yield a concrete extraction/open event, but it narrowed the needed artifact to exact command/path history.
This round added the endpoint GUID and transfer window, plus a related osquery sample pointing to a likely staging host and target archive name.

## This round
### What I ran
- `run_splunk_search(index=botsv3 sourcetype=code42:security source=code42://frothly_code42_input processOwner=BudStoll | stats min(timestamp) ... )` -> one BudStoll row with deviceGuid 858528515276632730, remoteAddr 12.196.122.127, min_ts 1534756409, max_ts 1534774757.
- `sample_events(sourcetype=osquery:results, source=/var/log/osquery/osqueryd.results.log, keyword=frothly_html_memcached, count=5)` -> raw osquery proc-events showing s3-upload.py cmdlines with target `frothly_html_memcached.tar.gz` and related typoed filenames.
- Exact-match SPL attempts on osquery host/path tokens returned no usable extraction/open result.
### What it means
We now have the archive transfer window and a staging/context clue, but not the file that visibly rendered the oversized word. The remaining step is to bind the archive to a specific command or opened file on the right host, then inspect that file’s content or filename clues.

## Ruled out
- Code42 as end-state evidence - confirms upload/download but not content.
- access_combined - not enough archive-linked activity found.
- hostIdentifier=hoth as the only osquery target - no matching archive activity returned.

## Open questions for SH
- Should I prioritize the mars.i-08e52f8b5a034012d host hinted by osquery raw cmdline, or keep focusing on BudStoll’s endpoint timeline?
- Is there a known extracted filename family from the tarball to target directly?