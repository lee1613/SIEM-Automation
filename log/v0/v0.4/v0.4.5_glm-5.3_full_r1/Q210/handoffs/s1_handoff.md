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

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['PerfmonMk:Process', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'stream:http', 'stream:tcp', 'stream:dns'] sources=[] fields=['host', 'process_name', 'instance', '%_Processor_Time', 'ID_Process', 'Image', 'CommandLine', 'DestinationIp', 'DestinationHostname', 'url', 'query', 'dest', 'src']
- Rounds worked: 4/5  (iterations: 32, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 (sourcetype=stream:dns OR sourcetype=stream:http) (coinhive* OR coin-hive* OR minero* OR *monero* OR cryptonight* OR nanopool* OR supportxmr* OR minergate* OR deepminr* OR coinweb* OR *miner*) | stats count by sourcetype, host, query | sort - count
- index=botsv3 (sourcetype=stream:dns OR sourcetype=stream:http) (coinhive* OR coin-hive* OR minero* OR monero* OR cryptonight* OR nanopool* OR supportxmr* OR minergate* OR deepminr* OR coinweb* OR miner*) | stats count by sourcetype, host, query | sort - count
- index=botsv3 (sourcetype=stream:http OR sourcetype=stream:tcp OR sourcetype=stream:ip) (dest_ip IN (45.63.68.160,45.63.68.161,45.63.68.162,45.63.68.163,45.63.68.164,45.63.68.165,45.63.68.166,45.63.68.167,45.63.68.168,45.63.68.169,45.63.68.170,45.63.68.171,45.63.68.172,45.63.68.173,45.63.68.174,45.63.68.175,45.63.68.176,45.63.68.177,45.63.68.178,45.63.68.179,45.63.68.180,45.63.68.181,45.63.68.182,45.63.68.183,45.63.68.184,45.63.68.185,45.63.68.186,45.63.68.187,45.63.68.188,45.63.68.189,45.63.68.190,45.63.68.191) OR dest="*coinhive*") | stats count by sourcetype, host, dest_ip, dest | sort - count
- index=botsv3 (sourcetype=stream:tcp OR sourcetype=stream:http OR sourcetype=stream:ip) (dest_ip IN (37.187.167.47,104.20.209.59,104.20.208.59) OR src_ip IN (37.187.167.47,104.20.209.59,104.20.208.59)) | stats count by sourcetype, src_ip, dest_ip, dest_port | sort - count
- index=botsv3 (sourcetype=stream:tcp OR sourcetype=stream:http OR sourcetype=stream:ip) host=BGIST-L | stats count, dc(dest_ip) as distinct_dests, min(_time) as first, max(_time) as last by sourcetype
- index=botsv3 (sourcetype=WinHostMon OR sourcetype=PerfmonMk:Process OR sourcetype="osquery:results" OR sourcetype=ps) (xmrig* OR minerd OR cpuminer OR cgminer OR stratum OR cryptonight) | stats count by sourcetype, host
- index=botsv3 host=BGIST-L | stats count by sourcetype | sort - count
- index=botsv3 sourcetype="PerfmonMk:Process" host=BSTOLL-L | stats max("%_Processor_Time") as max_cpu, min(_time) as first_seen, max(_time) as last_seen, values(instance) as instances by process_name | sort - max_cpu
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" DestinationIp IN (37.187.167.47,104.20.208.59,104.20.209.59) | stats count, min(_time) as first, max(_time) as last by host, EventCode, Image, ProcessId, DestinationIp, DestinationPort
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=3 | stats count, dc(DestinationIp) as distinct_dests by host
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BGIST-L EventCode=3 | stats count, min(_time) as first, max(_time) as last by DestinationIp, DestinationPort, Image | sort DestinationIp
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BSTOLL-L EventCode=3 | stats count, min(_time) as first, max(_time) as last by DestinationIp, DestinationPort, Image
- index=botsv3 sourcetype=* host=BGIST-L | stats count by sourcetype | sort - count
- index=botsv3 sourcetype=stream:dns (query="*coinhive*" OR query="*monero*" OR query="*minergate*" OR query="*nanopool*" OR query="*supportxmr*" OR query="*cryptonight*" OR query="*deepminr*" OR query="*coinweb*" OR query="*minero*") | stats count by host, query | sort - count
- index=botsv3 sourcetype=stream:dns host=BSTOLL-L query="*coinhive*" | stats min(_time) as first, max(_time) as last, values(query) as queries, values(dest) as dests, values(src) as srcs
- index=botsv3 sourcetype=stream:dns | stats dc(query) as distinct_queries, count as events by host | sort - events
- index=botsv3 sourcetype=stream:http (url="*coinhive*" OR dest="*coinhive*" OR http_user_agent="*coinhive*" OR uri_path="*coinhive*") | stats count, min(_time) as first, max(_time) as last by host, src_ip, url, dest
- index=botsv3 sourcetype=stream:tcp (dest_ip IN (37.187.167.47,104.20.208.59,104.20.209.59) OR src_ip IN (37.187.167.47,104.20.208.59,104.20.209.59)) | stats count, min(_time) as first, max(_time) as last, sum(bytes_in) as bytes_in, sum(bytes_out) as bytes_out by src_ip, dest_ip, dest_port
- index=botsv3 sourcetype=WinHostMon host=BGIST-L (Name="*coinhive*" OR CommandLine="*coinhive*" OR Name="*miner*" OR CommandLine="*miner*" OR Name="*xmrig*" OR CommandLine="*xmrig*" OR Name="*monero*" OR CommandLine="*monero*") | stats count by Name, CommandLine
- index=botsv3 sourcetype=WinHostMon host=BGIST-L | stats count by host, sourcetype
