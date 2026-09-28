# s1 - Q328 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=3_
**Scope:** sourcetypes stream:http, osquery:results, ps; host hoth; fields _raw/uri_path/form_data/bytes_in/bytes_out/cmdline/path/pid.
**Insight:** FOUND
**Candidate:** ` * Ubuntu 16.04.4 kernel priv esc`   **Confidence:** 90

## Prior rounds
- R1: 102 sourcetypes enumerated; linux_audit/bash_history carry no tomcat8 escalation; tomcat runs on hoth.
- R2: tomcat8 PID 1313 verified on hoth; osquery process+FIM prove /tmp/colonel → colonel.c (5775B) → gcc → colonelnew → chmod +x → executed 2x as uid 111, then uid-0 rm; no file text in osquery packs.
- R3: proved Struts2 OGNL RCE (saveGangster.action) as tomcat8 + reverse shell to 45.77.53.176:8088; located the 11:08:37 upload (bytes_in=9200) and 11:11:27 cat response (bytes_out=5880); mistakenly reported stream:http "colonel" as 0 (bad field names in group-by).

## This round
### What I ran
- `stream:http "colonel" | stats count` -> 4 events (R3's zero was a group-by artifact on non-existent fields).
- get_raw_events keyword=colonel -> 11:11:27 POST with #cmd='cat /tmp/colonel.c', http_content_length=5775, bytes_out=5880.
- rex over all 17 saveGangster requests -> full command sequence as tomcat8: whoami/id/groups, cat /etc/passwd, useradd -ou 0 -g 0 tomcat7, `echo <base64> >> /tmp/colonel` (11:08:37, bytes_in=9200), `base64 --decode /tmp/colonel > /tmp/colonel.c`, `cat /tmp/colonel.c`, `md5sum`, mknod+nc reverse shell.
- rex full command for bytes_in>5000 -> cmdlen=7721 = "echo " + 7700 base64 chars + " >> /tmp/colonel"; head/tail captured.

### What it means
The uploaded base64 IS the file: 7700 base64 chars decode to exactly 5775 bytes — the FIM-reported size of /tmp/colonel.c and the cat response's http_content_length. Decoding the captured prefix gives: line 1 `/*`, line 2 ` * Ubuntu 16.04.4 kernel priv esc`, then ` *`, ` * all credits to @bleidl`, ` * - vnik`, ` *`, blank, `// Te...`. The execution chain (upload → decode → cat → gcc → chmod +x → ./colonelnew as uid 111 → uid-0 rm) proves /tmp/colonel.c is the file used to escalate tomcat8 to root; /tmp/colonel is single-line base64 transport (no line 2), colonelnew the compiled binary.

## Assumptions
- Coverage: file text carriers — (a) stream:http form_data of the 11:08:37 upload: READ, contains the full base64 - VERIFIED; (b) stream:http 11:11:27 cat response: content_length=5775 confirms the body carried the file, body itself not stored in the event - VERIFIED as to size; (c) osquery packs, shell histories, stream:tcp/smtp, config_file: eliminated in R2-R3 - VERIFIED empty.
- Selection: /tmp/colonel.c is the escalation file — it is the source compiled into colonelnew which tomcat8 executed before uid-0 activity; /tmp/colonel is one echo line (no line 2 exists); colonelnew is a binary - VERIFIED by the command sequence and FIM sizes.
- Premise: base64 prefix decodes to the file's first lines — hand-decoded `LyoKICogVWJ1bnR1IDE2LjA0LjQga2VybmVsIHByaXYgZXNjCiAqCiAqIGFsbCBjcmVkaXRzIHRvIEBibGVpZGwKICogLSB2bmlrCiAqLwoK` = "/*\n * Ubuntu 16.04.4 kernel priv esc\n *\n * all credits to @bleidl\n * - vnik\n *\n\n" - VERIFIED by deterministic decode; size math (7700 chars → 5775 bytes) ties the payload to colonel.c.
- Premise: line 2 includes the leading " * " — the decoded bytes are 0x20 0x2A 0x20 before "Ubuntu" - VERIFIED.

## Ruled out
- /tmp/colonel as the question's file — single-line base64 transport written by one echo; no line 2 exists.
- /tmp/colonelnew — compiled ELF binary, not line-oriented text.
- Response-body storage in stream:http events — the 11:11:27 event stores only content_length (5775), not the body; the upload's form_data carries the text instead.

## Open questions for SH
- None material; the value is telemetry-derived and size-verified. If SH wants belt-and-braces confirmation, the full 7700-char base64 can be re-extracted and decoded end-to-end, but lines 1-2 are already fully covered by the captured prefix.

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_raw_events: {"keyword": "colonel", "limit": 10, "sourcetype": "stream:http"}` (2 of 4 rows seen). A claim resting on them alone is UNVERIFIED._
