# s1 - Q210 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=8_
**Scope:** sourcetype=stream:dns, stream:tcp, stream:http, stream:ip, PerfmonMk:Process | fields: host, query, src_ip, dest_ip, dest_port, process_name, %_Processor_Time, _time
**Insight:** FOUND
**Candidate:** BSTOLL-L   **Confidence:** 90

## Prior rounds
- Round 1: keyword searches for "monero"/"miner"/"xmr" found no field-name matches; sourcetype inventory taken (102 types).
- Round 2 (this round): established full mining evidence chain on BSTOLL-L and tested the "only" qualifier across all endpoints.

## This round
### What I ran
- PerfmonMk:Process host=BSTOLL-L | stats max CPU by process -> chrome#4/#5 and MicrosoftEdgeCP#2 at 100% CPU; chrome window 1534769680-1534778279 (50 of 277 rows read; top rows suffice for the max-CPU finding).
- stream:dns + stream:http mining-domain search (coinhive/monero/minergate/nanopool/supportxmr/cryptonight/deepminr/coinweb/minero) -> 6 rows, ALL host=BSTOLL-L: coinhive.com and ws001/ws005/ws011/ws014/ws019.coinhive.com.
- get_raw_events stream:dns "coinhive" -> full events: BSTOLL-L (192.168.247.131) queries resolved to 37.187.167.47 (ws019) and 104.20.208.59/104.20.209.59 (coinhive.com), 2018-08-20 13:37-13:39 UTC.
- stream:tcp/http/ip for those resolved IPs -> 2 rows: BSTOLL-L connected to 37.187.167.47:443 and 104.20.208.59:443 — actual connections to Coinhive mining servers.
- stream:dns all-hosts mining-domain search -> only BSTOLL-L, no other host.
- stream:dns | stats by host -> 16 hosts covered, including all 7 Frothly endpoints (BSTOLL-L, BTUN-L, PCERF-L, MKRAEUS-L, JWORTOS-L, ABUNGST-L, FYODOR-L), so the "no other host" result is meaningful coverage, not absence of data.

### What it means
FOUND: BSTOLL-L is the only Frothly endpoint that actually mined Monero. The chain: browser processes at 100% CPU (chrome#4/#5, MicrosoftEdgeCP#2) during a window that fully contains DNS queries to coinhive.com and five of its websocket mining endpoints (ws001-ws019.coinhive.com), followed by real TCP connections to the resolved mining servers (37.187.167.47:443, 104.20.208.59:443). Coinhive is a browser-based Monero/CryptoNight miner — the browser-process CPU spike plus connections to its mining servers is mining behavior, not generic high CPU. No other endpoint in the DNS feed (which covers all seven Frothly endpoints) queried any mining domain, and no other endpoint connected to the coinhive IPs. Taskmgr appearing at 1534772341, mid-mining-window, corroborates a user noticing the slowdown.

## Ruled out
- Other Frothly endpoints (BTUN-L, PCERF-L, MKRAEUS-L, JWORTOS-L, ABUNGST-L, FYODOR-L) — all covered by stream:dns with thousands of events each; zero mining-domain queries and zero connections to coinhive IPs.
- Generic high-CPU-only interpretation — BSTOLL-L's high CPU is tied to browser processes plus confirmed coinhive connections, i.e., actual mining, not just load.
- Miner-name process search (xmrig, minerd, cpuminer, cgminer, stratum, cryptonight) across WinHostMon/PerfmonMk/osquery/ps — 0 events; the mining is browser-based (Coinhive), not a standalone miner binary.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="PerfmonMk:Process" host=BSTOLL-L | stats max("%_Processor_Time") …` (50 of 277 rows seen). A claim resting on them alone is UNVERIFIED._
