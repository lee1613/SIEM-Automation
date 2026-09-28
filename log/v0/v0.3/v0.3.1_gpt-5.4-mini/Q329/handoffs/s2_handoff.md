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

## What I'd tell my replacement
- Retired because: This senior established the likely uploaded archive and staging host context but did not recover any internal filename or content-bearing artifact for the oversized word after repeated pivots across Code42, osquery, lsof, and stream:http. Handoff: preserve `frothly_html_memcached.tar.gz`, BudStoll, deviceGuid 858528515276632730, transfer window 1534756409–1534774757, and host mars.i-08e52f8b5a034012d as the best-grounded leads.
- Scope I owned: sourcetypes=['osquery:results', 'access_combined', 'ms:o365:management', 'o365:management:activity', 'aws:s3:accesslogs'] sources=[] fields=['path', 'filename', 'target_path', 'command', 'url', 'uri', 'object', 'key', 'fileName', 'Message']
- Rounds worked: 6/7  (iterations: 36, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=access_combined (uri=*frothly_html_memcached* OR uri_path=*frothly_html_memcached* OR referer=*frothly_html_memcached* OR file=*frothly_html_memcached*) | stats count by host source clientip method uri uri_path file status referer | sort -count
- index=botsv3 sourcetype=access_combined frothly_html_memcached | stats count by host source clientip method uri uri_path file status referer | sort -count
- index=botsv3 sourcetype=code42:security source=code42://frothly_code42_input processOwner=BudStoll | stats min(timestamp) as min_ts max(timestamp) as max_ts values(deviceGuid) as deviceGuids values(deviceRemoteAddress) as remoteAddrs values(processName) as processes values(files{}.fileEventType) as eventTypes values(files{}.fullPath) as paths by processOwner | sort -min_ts
- index=botsv3 sourcetype=lsof source=lsof host=mars.i-08e52f8b5a034012d (NAME="*frothly*" OR NAME="*html*" OR NAME="*memcached*" OR NAME="*memcaced*") | stats count by host COMMAND USER PID FD TYPE NAME | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log (columns.command="tar" OR columns.command="ls" OR columns.command="pwd" OR columns.command="cd ..") | stats count by host hostIdentifier name columns.command columns.path columns.target_path columns.cwd columns.filename | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log (columns.path=*frothly_html_memcached* OR columns.target_path=*frothly_html_memcached* OR columns.command=*frothly_html_memcached* OR columns.command=*tar* OR columns.command=*html*) | stats count by host hostIdentifier name columns.command columns.path columns.target_path columns.filename columns.cwd columns.arg0 columns.arg1 columns.arg2 | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log (host=hoth OR hostIdentifier=hoth) | stats count by host hostIdentifier name columns.command columns.path columns.target_path columns.filename | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log (hostIdentifier=mars.i-08e52f8b5a034012d OR hostIdentifier=hoth OR hostIdentifier=gacrux.i-0920036c8ca91e501) | stats count by host hostIdentifier name | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log host=hoth (name="pack_incident-response_shell_history" OR name="pack_fim_file_events") | stats count by name columns.command columns.path columns.target_path columns.filename host hostIdentifier | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log hostIdentifier=hoth (columns.command="tar" OR columns.command="unzip" OR columns.command="ls" OR columns.command="cat" OR columns.command="find") | stats count by host hostIdentifier name columns.command columns.path columns.target_path columns.cwd columns.filename | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log hostIdentifier=mars.i-08e52f8b5a034012d (columns.cmdline="\"python\" \"/home/ec2-user/tools/s3-upload.py\" \"--bucket\" \"frothlywebcode\" \"--file\" \"frothly_web_memcaced.tar.gz\" \"--folder\" E28098E28099 \"--target\" \"frothly_html_memcached.tar.gz\"" OR columns.cmdline="\"python\" \"/home/ec2-user/tools/s3-upload.py\" \"--bucket\" \"frothlywebcode\" \"--file\" \"frothly_html_memcaced.tar.gz\" \"--folder\" E28098E28099 \"--target\" \"frothly_html_memcached.tar.gz\"") | stats count by host hostIdentifier name columns.cmdline columns.path columns.target_path columns.cwd | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log hostIdentifier=mars.i-08e52f8b5a034012d (columns.cmdline=*frothly_html_memcached.tar.gz OR columns.cmdline=*frothly_web_memcaced.tar.gz OR columns.path=*frothly_html_memcached.tar.gz OR columns.path=*frothly_web_memcaced.tar.gz) | stats count by host hostIdentifier name columns.cmdline columns.path columns.target_path columns.cwd | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log hostIdentifier=mars.i-08e52f8b5a034012d (columns.command="*frothly_html_memcached.tar.gz*" OR columns.path="*frothly_html_memcached.tar.gz*" OR columns.target_path="*frothly_html_memcached.tar.gz*") | stats count by host hostIdentifier name columns.command columns.path columns.target_path | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log hostIdentifier=mars.i-08e52f8b5a034012d (columns.command="frothly_html_memcached.tar.gz" OR columns.command="frothly_html_memcaced.tar.gz" OR columns.command="frothly_web_memcaced.tar.gz" OR columns.path="frothly_html_memcached.tar.gz" OR columns.target_path="frothly_html_memcached.tar.gz") | stats count by host hostIdentifier name columns.command columns.path columns.target_path | sort -count
- index=botsv3 sourcetype=osquery:results source=/var/log/osquery/osqueryd.results.log hostIdentifier=mars.i-08e52f8b5a034012d columns.cmdline="python" | stats count by host hostIdentifier name columns.cmdline columns.path columns.target_path columns.cwd | sort -count
- index=botsv3 sourcetype=stream:http source=stream:http host=mars.i-08e52f8b5a034012d (uri=*frothly* OR url=*frothly* OR uri=*html* OR url=*html* OR http_user_agent=*Chrome* ) | stats count by host src dest uri url http_user_agent protocol_stack | sort -count
