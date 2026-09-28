# Q210 — SH <-> Senior conversation

### 13:54:14 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['PerfmonMk:Process', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'stream:http', 'stream:tcp', 'stream:dns'] sources=- fields=['host', 'process_name', 'instance', '%_Processor_Time', 'ID_Process', 'Image', 'CommandLine', 'DestinationIp', 'DestinationHostname', 'url', 'query', 'dest', 'src']
**Technique:** senior
**Reason:** The question is stricter than Q208: it asks for actual Monero mining, not just suspicious CPU behavior. The right scope is endpoint process telemetry plus adjacent host/network evidence that can reveal mining-specific behavior or destinations, while carrying forward BSTOLL-L as a proven lead rather than assuming it is the answer.

Determine which Frothly endpoint actually mined Monero cryptocurrency. Start from the established suspicious high-CPU endpoint BSTOLL-L, but test whether the available endpoint and network evidence shows real Monero-mining activity and whether any other endpoint also fits. Return the short hostname of the only endpoint that truly mined Monero, not merely a host with generic high CPU.

### 13:56:44 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> 
_full: reports/s1_round_1.md_

### 13:56:50 - SH -> s1   [COMMAND]
**retry** — The scope is still relevant, but the approach was too blunt: a negative keyword sweep does not decide actual Monero mining. The case already has BSTOLL-L as a suspicious lead from Q208, and the question requires proof of mining activity plus uniqueness across endpoints.
**New scope:** sourcetypes=['PerfmonMk:Process', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'stream:http', 'stream:dns', 'stream:tcp', 'stream:ip'] sources=[] fields=['host', 'process_name', 'instance', '%_Processor_Time', 'Image', 'ProcessId', 'CommandLine', 'DestinationIp', 'DestinationHostname', 'dest', 'src', 'url', 'query', 'uri_path', 'http_user_agent', '_time']

Establish actual Monero-mining activity first, not miner-name strings. On BSTOLL-L, examine endpoint and network evidence for mining-shaped outbound activity, browser- or process-linked connections, or artifacts referencing Monero pools/protocol behavior during the high-CPU window from Q208. Then check whether any other endpoint shows the same kind of mining evidence so the 'only' qualifier is tested. If BSTOLL-L is not supported, say what endpoint is supported instead and from which feed.

### 13:58:18 - s1 -> SH   [REPORT - round 2 - FOUND]
> Evidence chain: (1) BSTOLL-L (192.168.247.131) issued DNS queries for coinhive.com and five of its websocket mining endpoints (ws001/ws005/ws011/ws014/ws019.coinhive.com) on 2018-08-20 ~13:37-13:39 UTC (epoch 1534772253-1534772360), resolving to 37.187.167.47 and 104.20.208.59/104.20.209.59. (2) BST
_full: reports/s1_round_2.md_

### 13:58:25 - SH -> s1   [COMMAND]
**continue** — This round materially advanced the case by establishing mining-specific network evidence on BSTOLL-L and checking other Frothly endpoints for the same indicators. The answer is still blocked because the report ended at the iteration cap and the load-bearing coverage and selection premises have not yet been formalized and verified.

Settle the answer from result output in two steps. First, verify coverage: show that actual Monero mining on Frothly endpoints would appear in the searched feeds through Coinhive-related DNS and subsequent network connections, and show which endpoints are covered by that endpoint-to-network evidence. Second, verify selection: list the mining-domain queries and matching outbound connections for BSTOLL-L with times and resolved IPs, and show that no other covered endpoint has the same evidence. Then restate the short hostname literally if unchanged.

### 14:00:48 - s1 -> SH   [REPORT - round 3 - FOUND]
> Both load-bearing premises settled this round. p1 (coverage): stream:dns covers all 7 primary Frothly Windows endpoints with 5k-16k events each (BSTOLL-L 15784, BTUN-L 12475, PCERF-L 11662, MKRAEUS-L 9448, JWORTOS-L 9338, ABUNGST-L 8851, FYODOR-L 7415), so mining-service DNS from any of them would a
_full: reports/s1_round_3.md_

### 14:00:56 - runner   [NOTE]
TURN REJECTED:
- [REFERENCE: GATES] ANSWER is blocked: s1's last round was cut off at the iteration cap — CLARIFY it (costs no round; its reply clears this block) or COMMAND one more round before answering from it → re-read REFERENCE: GATES.

### 14:01:04 - SH -> s1   [CLARIFY]
**suspect**
1. From the evidence you already hold, does any Frothly endpoint other than BSTOLL-L have either a Coinhive-related DNS query or a matching TCP connection to the resolved Coinhive IPs?
2. For BGIST-L specifically, do your held results leave any in-scope network artifact unexamined that could still show mining, or does your held evidence already show that BGIST-L lacks network telemetry and only has WinHostMon with no miner indicators?
3. Does your held evidence already support the 'only Frothly endpoint' claim without needing any additional searches, or is there a named unresolved rival host you would still need to test?

### 14:01:19 - s1 -> SH   [CLARIFY REPLY]
**1.** No. The all-hosts mining-domain DNS search (coinhive/monero/minergate/nanopool/supportxmr/cryptonight/deepminr/coinweb/minero across stream:dns) returned 6 rows, all host=BSTOLL-L. The all-hosts TCP search for the resolved Coinhive IPs (37.187.167.47, 104.20.208.59, 104.20.209.59) returned exactly 2 rows, both from src_ip=192.168.247.131 (BSTOLL-L). No other endpoint appears in either result.

**2.** One in-scope artifact is unexamined. My held results show BGIST-L has zero events in stream:dns, stream:tcp, stream:http, and stream:ip (no network-stream telemetry at all), and its only feed, WinHostMon (14,410 events), returned 0 hits for coinhive/miner/xmrig/monero in Name and CommandLine. However, the Sysmon EventCode=3 host listing showed BGIST-L has **12 network-connection events to 7 distinct destination IPs that I never read**. I did verify none of those 12 go to the three known Coinhive IPs (the DestinationIp IN (...) Sysmon search returned 0 events across all hosts), but I have not seen what the other destinations actually are — and Coinhive's other ws### endpoints could resolve to IPs I never enumerated, since I only observed resolutions for ws019 and coinhive.com its

### 14:01:26 - runner   [NOTE]
TURN REJECTED:
- [C3] p1 was stamped in an earlier turn - a stamp is recorded once, when the verification is first claimed → re-read C3.
- [C3] p2 was stamped in an earlier turn - a stamp is recorded once, when the verification is first claimed → re-read C3.

### 14:01:31 - SH -> s1   [COMMAND]
**continue** — The case is narrowed to a single unresolved rival host. Resolving BGIST-L's unread Sysmon network connections is necessary to make the uniqueness claim sound.
**New scope:** sourcetypes=[] sources=[] fields=['DestinationIp', 'DestinationPort', 'Image', 'host', 'EventCode']

Resolve BGIST-L as the only remaining rival. Read all Sysmon EventCode=3 network-connection events for BGIST-L, identify their destination IPs, ports, and process images, and determine whether any are consistent with Coinhive or Monero mining connectivity. Then restate whether BSTOLL-L remains the only endpoint that actually mined Monero, explicitly comparing BGIST-L's connection evidence to BSTOLL-L's Coinhive DNS-plus-TCP chain.

### 14:01:53 - s1 -> SH   [REPORT - round 4 - FOUND]
> BGIST-L resolved as the last rival. Its complete Sysmon EventCode=3 evidence (all 12 events, 7 destination IPs, read in full) shows only Dropbox update traffic: every connection is from DropboxUpdate.exe or the DropboxClient installer to Dropbox infrastructure (162.125.3.3, 162.125.8.3, 162.125.33.7
_full: reports/s1_round_4.md_

### 14:01:57 - SH -> s1   [ANSWER]
**BSTOLL-L** (hostname) from s1

s1 established actual Monero mining on BSTOLL-L through Coinhive DNS queries, matching outbound TCP connections to the resolved Coinhive IPs on 443, and concurrent browser 100% CPU activity. In the follow-up round, s1 read all 12 BGIST-L Sysmon EventCode=3 connections and showed they were Dropbox update/install traffic only, clearing the last named rival; the other Frothly endpoints were already covered-and-empty for mining DNS and Coinhive connections. The answer is therefore the literal short hostname BSTOLL-L.

**Premises it rests on:** p1, p2

### 14:01:57 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

