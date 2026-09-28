# s2 - Q328 - Round 4
_stamped by runner: rounds_remaining=4 novel_spl=7_
**Scope:** sourcetype=stream:http (flow 911b5d8b) | fields=form_data, _raw, http_content_length
**Insight:** FOUND   **Candidate:** " * Ubuntu 16.04.4 kernel priv esc"   **Confidence:** 95

## Prior rounds
- R1: colonelnew runs as tomcat8 PID 9456 on hoth only (ps); linux_audit 0 gcc events; catalina.out heads are Struts2 traces.
- R2: osquery gave the verified chain — gcc colonel.c -o colonelnew, chmod +x, ./colonelnew; FIM /tmp/colonel.c 5775 bytes; stream:http gave echo base64 > /tmp/colonel, base64 --decode, cat (5775-byte response), md5sum.
- R3: rex-extracted the base64 query-side (480+240 chars); ruled out response-body fields and stream:tcp payload; manual decode produced the line-2 candidate.
- R4 (this): full payload proven complete by arithmetic; line 2 decoded by pure SPL.

## This round
### What I ran
- rex full payload | eval b64len=len(b64), declen=b64len*3/4 -> b64len=7700, declen=5775 — exactly FIM's size for /tmp/colonel.c and the cat response content_length.
- fieldsummary (full 57-field list) -> no response_body field in stream:http; cat event _raw ends 32-42 chars after http_user_agent (body definitively absent).
- rex on form_data for all 14 attacker commands -> full command list incl. the complete echo payload, useradd tomcat7, mknod backpipe.
- web_lookup for the public exploit header -> no snippets (not needed).
- Pure-SPL base64 decoder (mvfind alphabet + byte arithmetic + urldecode) on the first 16 groups -> **"/*<LF> * Ubuntu 16.04.4 kernel priv esc<LF> *<LF> * all c"** — the file's opening, decoded by the query itself.

### What it means
FOUND. The escalation file is /tmp/colonel.c (sole gcc input: `gcc colonel.c -o colonelnew`, run as tomcat8). Its content arrived as a 7700-char base64 payload in the 19:08:37 echo command; 7700 chars → exactly 5775 bytes = FIM's recorded size = the cat response content_length, proving the payload is the complete file. The query-side decode returns line 1 "/*", line 2 " * Ubuntu 16.04.4 kernel priv esc", line 3 " *", line 4 " * all c…". No manual decoding remains anywhere in the chain.

## Ruled out
- stream:http response body as a field — none exists; cat event _raw ends right after http_user_agent.
- stream:tcp payload — flow 5b903a0c events carry metadata only.
- base64_decode eval — unsupported (FATAL), replaced by the pure-SPL decoder.
- /tmp/colonel (base64 transport), /tmp/colonelnew (compiled binary) — not the text file.