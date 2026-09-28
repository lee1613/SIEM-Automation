# s1 - Q210 - Round 4
_stamped by runner: rounds_remaining=1 novel_spl=1_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | fields: host, EventCode, DestinationIp, DestinationPort, Image
**Insight:** FOUND
**Candidate:** BSTOLL-L   **Confidence:** 95

## Prior rounds
- Round 1: keyword searches for monero/miner/xmr found no field-name matches; took full sourcetype inventory (102 types).
- Round 2: found BSTOLL-L's coinhive.com + ws001-ws019 DNS queries and TCP connections to the resolved mining IPs; all-hosts DNS search showed only BSTOLL-L; submitted BSTOLL-L.
- Round 3: verified coverage (stream:dns covers all 7 primary endpoints; BGIST-L has no network-stream telemetry, only WinHostMon with 0 miner indicators) and connection detail (times, byte counts); answer unchanged.
- Round 4 (this round): read all 12 of BGIST-L's Sysmon EventCode=3 events in full — all Dropbox update traffic; BGIST-L ruled out; answer unchanged.

## This round
### What I ran
- Sysmon host=BGIST-L EventCode=3 | stats by DestinationIp, DestinationPort, Image -> 7 rows returned of 7 total (all 12 events read in full): every connection is DropboxUpdate.exe or the DropboxClient installer reaching 162.125.3.3:443, 162.125.8.3:443 (x5), 162.125.33.7:443 (Dropbox's own IP block), and AWS endpoints 34.200.67.44:443, 52.7.182.237:443 (x2), 52.84.17.45:443, 72.21.91.29:80.

### What it means
FOUND, and the last rival is resolved. BGIST-L's complete network-connection evidence is exclusively Dropbox update/install traffic — no connection to any Coinhive IP (37.187.167.47, 104.20.208.59, 104.20.209.59), no browser process making any connection, no mining-shaped destination. Combined with its only other feed (WinHostMon, 14,410 events, zero miner process names or command lines) and its absence from all network-stream telemetry, BGIST-L shows no mining evidence of any kind. Explicit comparison: BSTOLL-L holds the full mining chain — Coinhive DNS queries (coinhive.com + five ws### mining endpoints, 2018-08-20 13:37-13:39 UTC) resolving to the mining servers, actual TCP connections to those resolved IPs on 443 with substantial bidirectional byte counts (37.187.167.47: 28170B in/56768B out; 104.20.208.59: 2654B in/156054B out), and browser processes at 100% CPU in the same window. BGIST-L holds none of these. Every Frothly endpoint is now either positively cleared (BGIST-L) or covered-and-empty (BTUN-L, PCERF-L, MKRAEUS-L, JWORTOS-L, ABUNGST-L, FYODOR-L — 5k-16k DNS events each, zero mining queries, zero Coinhive connections). BSTOLL-L remains the only Frothly endpoint that actually mined Monero. Short hostname, unchanged: BSTOLL-L.

## Ruled out
- BGIST-L — all 12 Sysmon EventCode=3 events read in full: only Dropbox updater/installer connections to Dropbox's own IP block (162.125.x.x) and AWS endpoints; no Coinhive IP, no browser connections, no miner processes in WinHostMon, no DNS telemetry exists for it.
- Other Frothly endpoints (BTUN-L, PCERF-L, MKRAEUS-L, JWORTOS-L, ABUNGST-L, FYODOR-L) — covered by stream:dns (5k-16k events each) and Sysmon EC=3; zero mining-domain queries, zero connections to Coinhive IPs.
- Sysmon EventCode=3 as the connection feed for BSTOLL-L's mining act — it captured only Defender/PuTTY connections there and missed the browser TLS sessions; stream:tcp carries them.
- stream:http for Coinhive evidence — 0 events; the mining traffic is TLS-encrypted on 443.
- Standalone miner binaries (xmrig/minerd/cpuminer/cgminer/stratum/cryptonight) — 0 events across endpoint telemetry; the mining was browser-based via Coinhive.