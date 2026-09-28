# s2 - Q328 - Round 1
_stamped by runner: rounds_remaining=5 novel_spl=5_
**Scope:** sourcetype=stream:http | source=stream:http | fields=form_data, uri_path, http_content_length, status, site
**Insight:** FOUND
**Candidate:** ` * Ubuntu 16.04.4 kernel priv esc`   **Confidence:** 90

## Prior rounds
- Round 1: keyword manifest has no "colonel" field; get_source_types enumerated 102 sourcetypes; stream:http identified as the content-bearing Struts2 delivery feed.
- Round 1: get_raw_events stream:http "colonel" -> 4 events, all POSTs to 192.168.9.30:8080 /frothlyinventory/integration/saveGangster.action (hoth) from 192.168.8.103, UA python-requests/2.18.4, Struts2 OGNL RCE in form_data.
- Round 1: bash_history "colonel" -> 0 events (attacker used RPI, not an interactive shell).

## This round
### What I ran
- `index=botsv3 sourcetype=stream:http "colonel" | rex field=form_data "#cmd='(?<cmd>[^']+)'" | stats count by cmd, http_content_length, status` -> 4 events: `echo <base64> >> /tmp/colonel`; `base64 --decode /tmp/colonel > /tmp/colonel.c`; `cat /tmp/colonel.c` (content_length 5775); `md5sum /tmp/colonel.c` (content_length 49).
- `index=botsv3 sourcetype=stream:http "Ubuntu 16.04.4"` -> 0 events (no plaintext copy in the feed; response bodies are not stored as fields).
- `index=botsv3 sourcetype=osquery:results "colonel" | stats count by host, name` -> hoth: pack_fim_file_events (6), pack_process-monitoring_proc_events (5) — corroborates artifact and execution chain.

### What it means
FOUND. The base64 blob in the `echo` command is the staged file; `base64 --decode` wrote it to /tmp/colonel.c, so decoding it recovers the exact file contents (the 5775-byte `cat` response is the same text). Manual decode of the header yields: L1 `/*`, L2 ` * Ubuntu 16.04.4 kernel priv esc`, L3 ` *`, L4 ` * all credits to @bleidl`, L5 ` * - vnik`. The body is vnik's CVE-2017-16995 eBPF privilege-escalation exploit (PHYS_OFFSET 0xffff880000000000, BPF_PROG_LOAD, bpf_create_map, cred overwrite via __get_fp/pwn), run by tomcat8 to reach root. Line 2 = ` * Ubuntu 16.04.4 kernel priv esc` (leading space included).

## Ruled out
- bash_history - no colonel reference; delivery was via Struts2 RPI, not shell.
- stream:http response-body field - no such field exists; plaintext "Ubuntu 16.04.4" absent from the feed, so content must come from the staged base64.

## Open questions for SH
- None blocking; if SH wants byte-level certainty beyond my manual decode, the 5775-byte cat response body would need pcap-level extraction, which stream:http does not retain.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['stream:http', 'access_combined', 'syslog'] sources=['out-3', 'localhost-5', '/var/log/httpd/access_log', '/var/log/apache2/access.log', '/var/log/syslog', 'stream:http', 'stream:Splunk_HTTPURI', 'stream:Splunk_HTTPClient', 'stream:Splunk_HTTPStatus'] fields=['_raw', 'uri', 'uri_path', 'http_method', 'src', 'dest', 'request', 'response', 'useragent', 'host']
- Rounds worked: 1/6  (iterations: 6, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "Ubuntu 16.04.4" | stats count by sourcetype, source
- index=botsv3 sourcetype=osquery:results "colonel" | stats count by host, name
- index=botsv3 sourcetype=osquery:results "colonel" | stats count by host, name, columns.cmdline
- index=botsv3 sourcetype=stream:http "colonel" | rex field=form_data "#cmd='(?<cmd>[^']+)'" | stats count by cmd, http_content_length, status
- index=botsv3 sourcetype=stream:http "Ubuntu 16.04.4" | stats count by source, uri_path, http_content_length
