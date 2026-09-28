# s2 - Q329 - Round 6
_stamped by runner: rounds_remaining=1 novel_spl=2_
**Scope:** sourcetype=code42:security,osquery:results,lsof,stream:http | source=code42://frothly_code42_input,/var/log/osquery/osqueryd.results.log,lsof,stream:http | fields=host,hostIdentifier,name,columns.path,columns.target_path,columns.command,file,path,process,uri,url,http_user_agent,files{}.fileName,files{}.fullPath,processOwner,deviceGuid
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 25

## Prior rounds
Code42 fixed the BudStoll transfer window and deviceGuid for frothly_html_memcached.tar.gz.
osquery raw samples pointed to mars.i-08e52f8b5a034012d as the staging host and showed s3-upload.py command text.
Host correlation in osquery confirmed mars as the archive-linked activity host.
The current round broadened to lsof and stream:http, but no extracted filename or rendered page was confirmed.
The oversized-font word remains unverified.

## This round
### What I ran
- `get_sourcetype_fields(sourcetype="lsof", source="lsof", index="botsv3")` -> confirmed NAME/COMMAND/USER/PID fields.
- `run_splunk_search(index=botsv3 sourcetype=lsof source=lsof host=mars.i-08e52f8b5a034012d (NAME="*frothly*" OR NAME="*html*" OR NAME="*memcached*" OR NAME="*memcaced*"))` -> no results.
- `get_sourcetype_fields(sourcetype="stream:http", source="stream:http", index="botsv3")` -> confirmed src/dest/uri/url/http_user_agent fields.
- An attempted stream:http search with wildcarded URI/url terms was rejected before a narrower query could be formed.
### What it means
The evidence family is correct, but the specific content-bearing artifact is still missing. I have not yet seen a filename or browser request that would expose the large-font word.

## Ruled out
- lsof NAME search on mars with archive keywords - no direct match returned.
- Code42 as end-state evidence - no contents, only transfer metadata.
- Generic osquery process history - already insufficient in prior rounds.

## Open questions for SH
- Should I target a specific internal file type next: html, txt, or image?
- Is there a known user/browser on mars that should be paired with the archive window?