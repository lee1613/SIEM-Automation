# s2 - Q314 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=1_
**Scope:** sourcetype=stream:http (dest_ip=45.77.53.176, dest_port=3333) | fields: http_method, status, http_comment, http_content_length, http_content_type, bytes_in, bytes_out, src_ip, dest_port, uri_path, http_user_agent

**Insight:** FOUND
**Candidate:** 3333   **Confidence:** 97

## Prior rounds
- Round 1: established the only stream:http retrieval to 45.77.53.176 is a single GET on dest_port 3333 (5.5MB, PowerShell UA); tied via Sysmon EC3/EC11 ProcessGuid {EBF7A186-C442-5B58-0000-00109914D901} to FYODOR-L tool drops; ruled out 443 (693 recurring connections, no retrieval record); settled p1 and p2 VERIFIED.
- Round 2 (this round): re-ran the raw retrieval event and settled p3 VERIFIED with literal field quotes.

## This round
### What I ran
- `index=botsv3 sourcetype=stream:http dest_ip=45.77.53.176 dest_port=3333 | stats count values(...) ...` -> 1 event total, 1 returned, every literal field extracted: http_method=GET, status=200, http_comment="HTTP/1.1 200 OK", http_content_length=5782482, http_content_type=image/png, bytes_in=177, bytes_out=5542140, src_ip=192.168.70.186, src_port=64104, dest_ip=45.77.53.176, dest_port=3333, uri_path=/images/logos.png, UA WindowsPowerShell/5.1.17134.112, site=45.77.53.176:3333, event_time=1534762036.891.

### What it means
p3 is settled from exact stream:http output. The literal fields show the act is a download: GET is a client-initiated request; status 200 / "HTTP/1.1 200 OK" is a successful full response; http_content_length 5,782,482 (image/png) is the response body's declared size; bytes_in=177 (request) vs bytes_out=5,542,140 (response) shows the bulk moved server-to-client, from 45.77.53.176:3333 to src_ip 192.168.70.186 — FYODOR-L's address, confirmed by Sysmon EC3 (DestinationPort=3333, SourceIp=192.168.70.186, ProcessGuid {EBF7A186-C442-5B58-0000-00109914D901}). The PowerShell UA shows the adversary's process drove the retrieval, and that same ProcessGuid created hdoor.exe and unziped\lsof-master\iexeplorer.exe/powershell.exe at 1534762061, ~35s after the 3333 connection at 1534762026 — the downloaded payload is the attack tools. Port unchanged: **3333**.

## Ruled out
- Port 443 as the tool-download port - zero stream:http retrieval records to 45.77.53.176 on 443; Sysmon shows only 693 recurring connections over ~67 min from the same ProcessGuid (beacon-like, non-HTTP retrieval).
- Upload interpretation of the 3333 record - refuted by the literal fields: GET + status 200 + bytes_out 5,542,140 vs bytes_in 177 is server-to-client transfer.