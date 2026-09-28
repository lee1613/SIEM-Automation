# Q216 — SH <-> Senior conversation

### 14:42:05 - runner   [NOTE]
RECALL Q210 summary

### 14:42:05 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src', 'dest', 'src_ip', 'dest_ip', 'dest_port', 'bytes', 'duration', 'starttime', 'endtime', 'hostname', 'host', 'application', 'url', 'domain']
**Technique:** metrics
**Reason:** The question explicitly names Cisco NVM flow logs as the measurement feed, which in this dataset are reachable via sourcetype=syslog source=cisconvmflowdata. Prior work already established BSTOLL-L as the only endpoint that actually mined Monero and identified Coinhive-related destinations, so the senior should test those entities directly in the NVM flow records and compute the duration numerically.

Using Cisco NVM flow logs only, determine for how many seconds BSTOLL-L generated Monero cryptocurrency traffic. Start from the established mining endpoint BSTOLL-L and the already-known Coinhive/Monero destination set, identify the flow records in cisconvmflowdata that correspond to that mining activity, and compute the total time span or duration in seconds that the endpoint was generating cryptocurrency traffic according to that feed.

### 14:46:19 - s1 -> SH   [REPORT - round 1 - FOUND]
> The measured record set is the 6 Coinhive flows, all from BSTOLL-L, all chrome.exe on 443, spanning 1534772253-1534773920 (13:37:33-14:05:20 UTC, Aug 20 2018). The union of the six flow intervals is continuous: the five short flows (coinhive.com auth plus ws001/ws005/ws011/ws014 pool handshakes) all
_full: reports/s1_round_1.md_

### 14:46:29 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] Treat 1667 as a candidate only until you verify coverage inside cisconvmflowdata: establish that the complete Monero-generating set for BSTOLL-L in this feed is exactly the six Coinhive-tagged chrome.exe:443 flows, and that no additional mining flows for BSTOLL-L in Cisco NVM sit outside the hostname-matched set.

**continue** — This round found a concrete duration candidate in the named Cisco NVM flow feed and correctly avoided double-counting overlaps, but the chain still depends on an unverified coverage premise and a cut-off report. The next round must prove that the identified flows are the full mining interval in this feed, not just the first hostname-matched subset.

Using Cisco NVM flow logs for BSTOLL-L only, verify the complete set of Monero-generating flows in cisconvmflowdata. Establish whether all mining-related flows are exactly the six chrome.exe port-443 flows tied to the known Coinhive destinations, including any that might lack a hostname field but share the same destination IPs or timing. Then show the earliest flow start and latest flow end for that complete set from result output, and restate the duration in seconds if unchanged.

### 14:49:25 - s1 -> SH   [REPORT - round 2 - FOUND]
> Duration unchanged at 1667 s; coverage now verified, so the candidate is confirmed. The six flows are one mining session: identical chrome.exe process hash, parent explorer.exe, user AzureAD\BudStoll, all dp=443, all sa=192.168.247.131. The negative gaps prove the union of active intervals is contin
_full: reports/s1_round_2.md_

### 14:49:36 - SH -> s1   [COMMAND]
**continue** — The correct feed, entity, and candidate value are now established, and p1 can support coverage if stamped true. The remaining work is to settle the measurement premise explicitly: why 'for how many seconds does the endpoint generate Monero cryptocurrency' in Cisco NVM means the continuous union/span of the mining flows rather than the summed flow durations or only the longest flow.
**New scope:** sourcetypes=[] sources=[] fields=['sa', 'da', 'dh', 'fss', 'fes', 'pn', 'dp', 'ph', 'ppn']

Settle the selection/measurement premise from Cisco NVM result output. Show the six mining flows in time order with fss and fes, and establish from those rows why the endpoint's generating time is the continuous interval from earliest fss to latest fes because every later flow begins before the prior active set ends. Explicitly rule out the rival readings of summing all per-flow durations (1758) and using only the longest single flow (1603), then restate the duration in seconds if unchanged.

### 14:50:25 - s1 -> SH   [REPORT - round 3 - FOUND]
> Duration unchanged at 1667 s; premise p2 settled from NVM result output. The six flows in time order (fss->fes): coinhive.com 1534772253-1534772377 (124 s); ws014 1534772254-1534772267 (13 s); ws001 1534772269-1534772273 (4 s); ws011 1534772283-1534772285 (2 s); ws005 1534772286-1534772298 (12 s); w
_full: reports/s1_round_3.md_

### 14:50:33 - SH -> s1   [ANSWER]
**1667** (count) from s1

In Cisco NVM flow logs (source=cisconvmflowdata), s1 established the complete Monero-generating set for BSTOLL-L as six chrome.exe:443 Coinhive flows and then showed, in time order, that each later flow starts before the prior active set ends. That makes the endpoint's generating time the continuous interval from first_start=1534772253 to last_end=1534773920, which the report gives literally as span_seconds=1667; the rival readings 1758 (sum of overlapping durations) and 1603 (longest single flow only) are explicitly ruled out by the same output.

**Premises it rests on:** p1, p2

### 14:50:33 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

