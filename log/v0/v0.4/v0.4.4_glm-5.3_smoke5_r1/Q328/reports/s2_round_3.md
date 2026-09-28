# s2 - Q328 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=7_
**Scope:** sourcetype=stream:http (flow 911b5d8b / 5b903a0c) | fields=form_data, _raw, http_content_length
**Insight:** partial   **Candidate:** " * Ubuntu 16.04.4 kernel priv esc"   **Confidence:** 85

## Prior rounds
- R1: colonelnew runs as tomcat8 PID 9456 on hoth only (ps, no args); linux_audit 0 gcc events; catalina.out heads are Struts2 traces.
- R2: osquery gave the verified chain — gcc colonel.c -o colonelnew, chmod +x, ./colonelnew; FIM /tmp/colonel.c 5775 bytes; stream:http gave echo base64 > /tmp/colonel, base64 --decode, cat (5775-byte response), md5sum. Manual decode of visible prefix → line 2 candidate.
- R3 (this): query-side rex extraction of the base64; response-body routes ruled out.

## This round
### What I ran
- get_sourcetype_fields stream:http + search_keyword "body" -> no response_body field anywhere in stream:http (body fields exist only in stream:smtp / symantec:ep:scm_system:file).
- `stream:http "cat /tmp/colonel.c"` -> 0 (tokenization); `"colonel.c"` -> 3 events.
- `stream:http "5b903a0c…" | rex …` -> 0; flow_id must be quoted whole.
- base64_decode eval -> FATAL: function unsupported in this Splunk.
- get_raw_events stream:tcp 5b903a0c -> 2 events, flow metadata only, no payload bytes.
- `stream:http "911b5d8b…" | rex "echo\s+(?<b64>[A-Za-z0-9+/=]{480})"` -> 1 row: the payload's first 480 base64 chars, returned as a query result.
- Same event, next 240 chars -> coherent continuation ("de <linux/bpf.h>\n#include <linux/unistd.h>…").

### What it means
The base64 now rests on query-returned text, not a clipped display. Decoded group-by-group, the file opens: `/*` / ` * Ubuntu 16.04.4 kernel priv esc` / ` *` / ` * all credits to @bleidl` / ` * - vnik` / ` */` / blank / `// Tested on:` / `// 4.4.0-116-generic…` / `// if different kernel adjust CRED offset…` / `#include <stdio.h>`… Line 2 = " * Ubuntu 16.04.4 kernel priv esc". Integrity: cat response content_length 5775 == FIM size of /tmp/colonel.c; gcc colonel.c -o colonelnew confirmed in osquery. The decode itself remains manual — base64_decode is unsupported here — but it is deterministic and both extracted chunks decode to contiguous, coherent C source matching the public vnik doubleput.c.

## Ruled out
- stream:http response body as a field — no response_body field exists; plaintext searches return 0.
- stream:tcp for the cat response — flow 5b903a0c events carry metadata only, no payload.
- Query-side base64_decode — function unsupported (FATAL).
- catalina.out — 0 "colonel" matches.
- /tmp/colonel (base64 transport), /tmp/colonelnew (compiled binary) — not the text file.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:http"}` (28 of 57 rows seen). A claim resting on them alone is UNVERIFIED._
