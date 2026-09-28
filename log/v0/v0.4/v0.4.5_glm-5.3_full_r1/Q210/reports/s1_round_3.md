# s1 - Q210 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=10_
**Scope:** sourcetype=stream:dns, stream:tcp, stream:http, stream:ip, XmlWinEventLog:Microsoft-Windows-Sysmon/Operational, PerfmonMk:Process, WinHostMon | fields: host, query, src_ip, dest_ip, dest_port, bytes_in, bytes_out, EventCode, Image, DestinationIp, process_name, %_Processor_Time, _time
**Insight:** FOUND
**Candidate:** BSTOLL-L   **Confidence:** 92

## Prior rounds
- Round 1: keyword searches for monero/miner/xmr found no field-name matches; took full sourcetype inventory (102 types).
- Round 2: found BSTOLL-L's coinhive.com + ws001-ws019 DNS queries and TCP connections to the resolved mining IPs; all-hosts DNS search showed only BSTOLL-L; submitted BSTOLL-L.
- Round 3 (this round): verified coverage (DNS/Sysmon host lists, BGIST-L's only feed) and connection detail (times, byte counts); answer unchanged.

## This round
### What I ran
- Sysmon DestinationIp IN (37.187.167.47,104.20.208.59,104.20.209.59) -> 0 events; Sysmon EventCode=3 | stats by host -> 8 hosts covered (ABUNGST-L 1073, BGIST-L 12, BSTOLL-L 16, BTUN-L 31, FYODOR-L 3931, JWORTOS-L 3, MKRAEUS-L 1, PCERF-L 5). BSTOLL-L's own EC=3 events are Defender/PuTTY only — Sysmon missed the browser TLS sessions, so stream:tcp is the feed carrying the connection evidence.
- stream:tcp for the coinhive IPs -> 2 rows, both from BSTOLL-L (192.168.247.131): to 104.20.208.59:443 (2 flows, 1534771760-1534772377, 2654B in / 156054B out) and to 37.187.167.47:443 (2 flows, 1534773304-1534773921, 28170B in / 56768B out).
- stream:http for coinhive URLs/UA/hosts -> 0 events (mining traffic is TLS on 443, so it lives in stream:tcp, not http).
- BGIST-L coverage: 0 stream:tcp/http/ip events; only WinHostMon (14,410 events); WinHostMon search for coinhive/miner/xmrig/monero in Name and CommandLine -> 0 events.

### What it means
FOUND, and both load-bearing premises are now settled. Coverage (p1): stream:dns covers all 7 primary Frothly endpoints with 5k-16k events each, so mining-service DNS from any of them would appear; the 8th endpoint, BGIST-L, has no network telemetry at all and its only feed (WinHostMon process data) shows no miner indicators — no existing feed could hide mining on it. Selection (p2): BSTOLL-L alone has mining-domain DNS (coinhive.com and ws001/ws005/ws011/ws014/ws019.coinhive.com, 2018-08-20 13:37-13:39 UTC, resolving to 37.187.167.47 and 104.20.208.59/104.20.209.59) and matching outbound TCP connections to those resolved mining-server IPs on 443 with substantial bidirectional byte counts. Browser processes (chrome#4, chrome#5, MicrosoftEdgeCP#2) at 100% CPU in the same window confirm the mining load; Taskmgr appearing at 1534772341 corroborates a user noticing. No other covered endpoint has either the DNS or the connections. Short hostname, unchanged: BSTOLL-L.

## Ruled out
- Other Frothly endpoints (BTUN-L, PCERF-L, MKRAEUS-L, JWORTOS-L, ABUNGST-L, FYODOR-L) — covered by stream:dns (5k-16k events each) and Sysmon EC=3; zero mining-domain queries, zero connections to coinhive IPs.
- BGIST-L — no network-stream telemetry exists for it; its only feed (WinHostMon, 14,410 events) shows no miner process names or command lines.
- Sysmon EventCode=3 as the connection feed for this act — it captured only Defender/PuTTY connections on BSTOLL-L and missed the browser TLS mining sessions; stream:tcp carries them.
- stream:http for coinhive evidence — 0 events; the mining traffic is TLS-encrypted on 443.
- Standalone miner binaries (xmrig/minerd/cpuminer/cgminer/stratum/cryptonight) — 0 events across endpoint telemetry; the mining was browser-based via Coinhive.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
