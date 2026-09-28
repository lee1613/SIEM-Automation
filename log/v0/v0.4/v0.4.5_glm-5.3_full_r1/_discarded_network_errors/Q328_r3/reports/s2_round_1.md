# s2 - Q328 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=7_
**Scope:** sourcetype=osquery:results, out-3, localhost-5, syslog, linux_secure, linux_audit | source=/var/log/osquery/osqueryd.results.log | fields=source, host, count
**Insight:** partial
**Candidate:** none   **Confidence:** 0

## Prior rounds
- Retired senior (rounds 1-3): isolated /tmp/colonel.c as the escalation source (gcc colonel.c -o colonelnew), /tmp/colonel as base64 transport, colonelnew as compiled binary; no dataset-readable artifact of colonel.c's contents found via stream:http decoding.
- This is my round 1 on the replacement scope (output-bearing host logs).

## This round
### What I ran
- get_source_types -> 102 sourcetypes; confirmed out-3, localhost-5, syslog, linux_secure, linux_audit, osquery:results, bash_history, stream:http all exist.
- index=botsv3 sourcetype=out-3 "colonel" | stats count by source, host -> 0 events
- index=botsv3 sourcetype=localhost-5 "colonel" | stats count by source, host -> 0 events
- index=botsv3 sourcetype=syslog "colonel" | stats count by source, host -> 0 events
- index=botsv3 sourcetype=linux_secure "colonel" | stats count by source, host -> 0 events
- index=botsv3 sourcetype=linux_audit "colonel" | stats count by source, host -> 0 events
- index=botsv3 sourcetype=osquery:results "colonel" | stats count by source, host -> 1 row: source=/var/log/osquery/osqueryd.results.log, host=hoth, count=11

### What it means
No value yet, but a live lead that changes the picture: of every output-bearing feed SH named, only osquery:results carries the name "colonel" — 11 events on hoth. I ran out of iterations before reading a single one, so I cannot state line 2's text and will not guess. Next round, in order: (1) read all 11 osquery events and determine whether any is content-bearing (yara/file query result with literal text) versus path/hash/process metadata only; (2) search hoth feeds for C-source tokens (unistd.h, setuid, setgid) — the file's own text need not contain "colonel", so a name-only search can miss it; (3) p1 branch (b), stream:http payloads, is still unsearched by me. p1 is now VERIFIED (osquery:results branch live); p2 (colonel.c as source file) untested this round.

## Ruled out
- out-3 (catalina/tomcat output) - 0 "colonel" events
- localhost-5 (tomcat localhost log) - 0 "colonel" events
- syslog - 0 "colonel" events
- linux_secure (auth.log sudo records) - 0 "colonel" events
- linux_audit (execve records) - 0 "colonel" events

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
