# s2 - Q328 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=7_
**Scope:** sourcetype=osquery:results, stream:http, out-3 | host=hoth | fields=columns.cmdline, columns.target_path, form_data, http_content_length
**Insight:** partial   **Candidate:** " * Ubuntu 16.04.4 kernel priv esc"   **Confidence:** 78

## Prior rounds
- R1 (mine): colonelnew runs as tomcat8 PID 9456 on hoth only (ps, 114 events, no args); linux_audit has 0 gcc records; catalina.out visible heads are Struts2 stack traces only.
- s1 R1-2: tomcat8 keyword route in auth/audit feeds exhausted; hoth / colonelnew / gcc-5 / ld.bfd / collect2 / chmod chain established.

## This round
### What I ran
- `osquery:results colonelnew | stats count by host, name` -> hoth: fim_file_events 5, process-monitoring 6.
- get_raw_events osquery:results colonelnew -> 11 rows, all read: `"gcc" "colonel.c" "-o" "colonelnew"` (gcc-5, pid 8609, tomcat8), cc1/collect2/ld.bfd, `"chmod" "+x" "colonelnew"`, `"./colonelnew"`.
- `osquery:results colonel.c | stats count by name, action, target_path` -> /tmp/colonel.c CREATED (0 bytes) then UPDATED (5775 bytes, md5 a38e52b8...).
- `out-3 colonel` -> 0 events (catalina.out holds no colonel text).
- `stream:http host=hoth (colonel OR gcc)` -> 4 POSTs to /frothlyinventory/integration/saveGangster.action.
- get_raw_events stream:http colonel -> 4 rows: 19:08:37 `echo <base64> > /tmp/colonel`; 19:10:56 `base64 --decode /tmp/colonel > /tmp/colonel.c`; 19:11:27 `cat /tmp/colonel.c` (http_content_length 5775 = FIM size); 19:11:47 `md5sum /tmp/colonel.c`.
- `stream:http "Ubuntu 16.04.4"` / `"kernel priv esc"` -> 0 events (cat response body not searchable text).

### What it means
The escalation file is /tmp/colonel.c — the sole gcc input in the verified compile chain. Its content arrived as base64 in the 19:08:37 echo command; the visible prefix decodes to `/*` / ` * Ubuntu 16.04.4 kernel priv esc` / ` * all credits to @bleidl` / ` * - vnik` / ` */`. Line 2 = " * Ubuntu 16.04.4 kernel priv esc". Caveat: the decode is manual (event clipped at 1500 chars, ~7741 unread); it is coherent, matches the known vnik doubleput.c header, and the cat response's 5775-byte content_length equals the FIM size of colonel.c — but no query-side decode confirmation was possible before the cap.

## Ruled out
- catalina.out (out-3) as content source — 0 "colonel" matches in all 15 events.
- cat-response body as searchable plaintext — "Ubuntu 16.04.4"/"kernel priv esc" return 0 in stream:http.
- /tmp/colonel — base64 transport artifact, not the gcc input.
- /tmp/colonelnew — compiled binary, not a text file.

## Next
Rex-extract the full base64 from the 19:08:37 echo event and decode query-side, or retrieve the response body for flow 5b903a0c-1396-4fec-ba0d-2b03b83611be, to confirm line 2 verbatim.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p3 - amend or settle that one. The text you sent was discarded: "The line-2 text of the escalation file is recoverable from the webshell command "
