# s1 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=3_
**Scope:** sourcetype=stream:http, osquery:results | source=stream:http, /var/log/osquery/osqueryd.results.log | fields=form_data, uri_path, host, name, columns.cmdline, _raw
**Insight:** FOUND
**Candidate:** ` * Ubuntu 16.04.4 kernel priv esc`   **Confidence:** 95

## Prior rounds
- Round 1: Mapped 102 sourcetypes; eliminated bash_history (only benign splunk admin + 2 "sudo bash"); identified 17 sources mentioning tomcat8.
- Round 2: Found Struts2 RCE channel on hoth via stream:http saveGangster.action; extracted all 15 exploit commands; identified /tmp/colonel.c as the escalation file; decoded base64 header manually.
- Round 3 (this round): Read full osquery FIM/process events for the colonel chain; proved base64 blob completeness by byte-count arithmetic (7700/4×3=5775); verified line 2 by group-by-group base64 decoding.

## This round
### What I ran
- `get_raw_events osquery:results keyword=colonel` (10 events) -> full FIM + process chain as tomcat8 (uid 111): /tmp/colonel UPDATED 7701 bytes; /tmp/colonel.c CREATED 0 bytes then UPDATED 5775 bytes; `"gcc" "colonel.c" "-o" "colonelnew"`; `"cat" "/tmp/colonel.c"`; `"base64" "--decode" "/tmp/colonel"`; `"md5sum" "/tmp/colonel.c"`.
- `... form_data="*echo*" | rex ... | stats count by b64len, tail` -> 2 echo commands: 7700-char base64 with ` >> /tmp/colonel` redirect; 8169-char JPEG blob with no redirect (irrelevant).
- `... form_data="*LyoK*" | rex ... | eval md5(...)` -> extracted base64 is exactly 7700 chars.
- Manual group-by-group base64 decoding of `LyoKICogVWJ1bnR1IDE2LjA0LjQga2VybmVsIHByaXYgZXNjCiAq` -> `/*\n * Ubuntu 16.04.4 kernel priv esc\n *` — line 2 confirmed byte-by-byte.

### What it means
FOUND: The adversary used Struts2 RCE (running as tomcat8, uid 111) to echo a 7700-char base64 blob to /tmp/colonel, decode it to /tmp/colonel.c (5775 bytes), and compile it to colonelnew — a kernel privilege escalation exploit. The base64 blob in the echo command IS the file's complete contents, proven by byte-count arithmetic: 7700 base64 chars ÷ 4 × 3 = 5775 bytes, exactly matching the osquery FIM-recorded size of /tmp/colonel.c. Line 2 of the decoded file is ` * Ubuntu 16.04.4 kernel priv esc`.

## Ruled out
- bash_history (klagerfield/ec2-user) - no file-creation or escalation commands; only "sudo bash" x2.
- /tmp/colonel (base64 transport file, 7701 bytes) - has only 1 line (7700 chars + newline); not the escalation file itself.
- colonelnew (compiled binary) - a binary has no readable "lines"; the question asks for displayed text on line 2, which only the C source file colonel.c has.
- 8169-char JPEG echo command - no file redirect; unrelated to the escalation chain.

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: "The complete contents of /tmp/colonel.c are recoverable from the stream:http for"
- p1 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
