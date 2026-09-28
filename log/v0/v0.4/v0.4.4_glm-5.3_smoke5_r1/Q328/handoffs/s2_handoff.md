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

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['osquery:results', 'bash_history', 'ps', 'out-3', 'localhost-5'] sources=[] fields=['host', 'name', 'action', 'columns.path', 'columns.cmdline', 'COMMAND', '_raw', 'source']
- Rounds worked: 4/8  (iterations: 42, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 colonelnew | stats count by sourcetype, source | sort - count
- index=botsv3 sourcetype=linux_audit source="/var/log/audit/audit.log" host=hoth gcc | stats count by _raw
- index=botsv3 sourcetype=osquery:results colonel.c | stats count by name, columns.action, columns.target_path
- index=botsv3 sourcetype=osquery:results colonelnew | stats count by host, name, source
- index=botsv3 sourcetype=out-3 colonel | stats count
- index=botsv3 sourcetype=ps colonelnew | stats count by host, source
- index=botsv3 sourcetype=ps host=hoth colonelnew gcc | stats count by _raw
- index=botsv3 sourcetype=ps host=hoth colonelnew | top limit=20 _raw
- index=botsv3 sourcetype=stream:http "192.168.8.103" | stats count by host, src_ip, dest_ip
- index=botsv3 sourcetype=stream:http "5b903a0c-1396-4fec-ba0d-2b03b83611be" | rex field=_raw "http_user_agent\":\"[^\"]*\"(?<tail>.*)" | eval taillen=len(tail) | stats count by taillen
- index=botsv3 sourcetype=stream:http "5b903a0c-1396-4fec-ba0d-2b03b83611be" | rex field=_raw "http_user_agent\":\"[^\"]*\",\"(?<chunk1>.{1400})" | stats count by chunk1
- index=botsv3 sourcetype=stream:http "5b903a0c-1396-4fec-ba0d-2b03b83611be" | stats count by _time, http_method, http_content_length, bytes_out
- index=botsv3 sourcetype=stream:http "911b5d8b-dacf-4fdf-a08a-72e9fc6b1d55" | rex field=_raw "echo\s+(?:[A-Za-z0-9+/=]{480})(?<b64>[A-Za-z0-9+/=]{240})" | stats count by b64
- index=botsv3 sourcetype=stream:http "911b5d8b-dacf-4fdf-a08a-72e9fc6b1d55" | rex field=_raw "echo\s+(?<b64>[A-Za-z0-9+/=]+)" | eval alphabet=mvappend("A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","0","1","2","3","4","5","6","7","8","9","+","/") | eval idx=mvrange(0,16) | mvexpand idx | eval g=substr(b64,idx*4+1,4) | eval v1=mvfind(alphabet,"^".substr(g,1,1)."$"), v2=mvfind(alphabet,"^".substr(g,2,1)."$"), v3=mvfind(alphabet,"^".substr(g,3,1)."$"), v4=mvfind(alphabet,"^".substr(g,4,1)."$") | eval b1=v1*4+floor(v2/16), b2=(v2%16)*16+floor(v3/4), b3=(v3%4)*64+v4 | eval h1=if(b1<16,"0".substr(tostring(b1,"hex"),3,1),substr(tostring(b1,"hex"),3,2)), h2=if(b2<16,"0".substr(tostring(b2,"hex"),3,1),substr(tostring(b2,"hex"),3,2)), h3=if(b3<16,"0".substr(tostring(b3,"hex"),3,1),substr(tostring(b3,"hex"),3,2)) | eval dec=urldecode("%".h1."%".h2."%".h3) | stats list(dec) as parts | eval decoded=mvjoin(parts,""), n=mvcount(parts) | eval flat=replace(decoded,"\n","<LF>") | stats count by flat, n
- index=botsv3 sourcetype=stream:http "911b5d8b-dacf-4fdf-a08a-72e9fc6b1d55" | rex field=_raw "echo\s+(?<b64>[A-Za-z0-9+/=]+)" | eval alphabet=mvappend("A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","0","1","2","3","4","5","6","7","8","9","+","/") | eval idx=mvrange(0,16) | mvexpand idx | eval g=substr(b64,idx*4+1,4) | eval v1=mvfind(alphabet,"^".substr(g,1,1)."$"), v2=mvfind(alphabet,"^".substr(g,2,1)."$"), v3=mvfind(alphabet,"^".substr(g,3,1)."$"), v4=mvfind(alphabet,"^".substr(g,4,1)."$") | eval b1=v1*4+floor(v2/16), b2=(v2%16)*16+floor(v3/4), b3=(v3%4)*64+v4 | eval h1=if(b1<16,"0".tostring(b1,"hex"),tostring(b1,"hex")), h2=if(b2<16,"0".tostring(b2,"hex"),tostring(b2,"hex")), h3=if(b3<16,"0".tostring(b3,"hex"),tostring(b3,"hex")) | eval dec=urldecode("%".h1."%".h2."%".h3) | stats list(dec) as parts | eval decoded=mvjoin(parts,""), n=mvcount(parts) | eval flat=replace(decoded,"\n","<LF>") | stats count by flat, n
- index=botsv3 sourcetype=stream:http "911b5d8b-dacf-4fdf-a08a-72e9fc6b1d55" | rex field=_raw "echo\s+(?<b64>[A-Za-z0-9+/=]+)" | eval b64len=len(b64) | eval declen=b64len*3/4 | stats count by b64len, declen
- index=botsv3 sourcetype=stream:http "911b5d8b-dacf-4fdf-a08a-72e9fc6b1d55" | rex field=_raw "echo\s+(?<b64>[A-Za-z0-9+/=]+)" | eval dec=base64_decode(b64) | eval filemd5=md5(dec) | rex field=dec "^[^\n]*\n(?<line2>[^\n]*)" | stats count by line2, filemd5
- index=botsv3 sourcetype=stream:http "911b5d8b-dacf-4fdf-a08a-72e9fc6b1d55" | rex field=_raw "echo\s+(?<b64>[A-Za-z0-9+/=]{480})" | stats count by b64
- index=botsv3 sourcetype=stream:http "cat /tmp/colonel.c" | rex field=_raw "http_user_agent\":\"[^\"]*\",\"(?<chunk1>.{1400})" | stats count by chunk1
- index=botsv3 sourcetype=stream:http "colonel.c" | stats count
- index=botsv3 sourcetype=stream:http "kernel priv esc" | stats count by _time, src_ip, http_content_length
- index=botsv3 sourcetype=stream:http "Ubuntu 16.04.4" | stats count by _time, http_content_length
- index=botsv3 sourcetype=stream:http 5b903a0c | rex field=_raw "http_user_agent\":\"[^\"]*\",\"(?<chunk1>.{1400})" | stats count by chunk1
- index=botsv3 sourcetype=stream:http host=hoth (colonel OR gcc) | stats count by http_method, uri_path
- index=botsv3 sourcetype=stream:http src_ip="192.168.8.103" | rex field=form_data "#cmd='(?<cmd>[^']*)'" | stats count by cmd, http_content_length | sort - http_content_length
- index=botsv3 sourcetype=stream:http | fieldsummary | stats values(field) as all_fields
