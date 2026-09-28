# Q216 — SH <-> Senior conversation

### 16:30:48 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'bytes', 'packets', 'duration', 'app', 'url', 'flow direction', '_time']
**Technique:** metrics
**Reason:** The question names Cisco NVM flow logs explicitly, and this duration must be computed from that feed rather than inferred from adjacent network data.

Within Cisco NVM flow logs from source cisconvmflowdata, determine for how many seconds the endpoint generates Monero cryptocurrency. First establish what specific endpoint and flows in this feed correspond to Monero mining activity, then determine the exact time span or summed duration required by the question and compute the final duration rounded to the nearest second.

### 16:39:17 - s1 -> SH   [REPORT - round 1 - FOUND]
> Candidate: 112 = fes-fss of the ONLY flow on dp=3333 (Monero Stratum default port) in the entire feed: powershell.exe, 192.168.70.186 (FyodorMalteskesko) -> 45.77.53.176, fss=1534762025, fes=1534762137 (10:47:05-10:48:57). Arithmetic (2137-2025=112) done mentally, NOT in SPL - iteration cap hit befo
_full: reports/s1_round_1.md_

### 16:39:23 - SH -> s1   [COMMAND]
SH's answers to your open questions:
1. Do not count the 4,829 :443 flows unless you can establish from this feed that they are the mining traffic the question means; first decide whether the mining act in Cisco NVM is uniquely evidenced by the 3333 Stratum session or whether the same destination over 443 also carries mining, and if the latter, resolve endpoint selection explicitly between 192.168.24.128 and 192.168.70.186.
2. Nothing in the case file here confirms 45.77.53.176 as a Monero pool. What would settle it for this question is evidence from Cisco NVM flow behavior itself that ties the mining act to that destination, and then whether only one endpoint performs that act.

**continue** — The round stayed in the right feed and produced the leading candidate, but the case still lacks a verified definition of which Cisco NVM flows constitute 'generates Monero.' We need the endpoint and duration to survive the possibility that the 443 traffic, not just the single 3333 flow, is the mining activity.
**New scope:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['pn', 'sa', 'da', 'dp', 'sp', 'fss', 'fes', 'liuid']

Within source=cisconvmflowdata, establish what records in this feed can legitimately represent Monero generation for 45.77.53.176 and which endpoint performs that act. Compare the lone 3333 session with the powershell-to-45.77.53.176 traffic on 443 by host and by flow timing/duration: determine whether the 443 flows are short beacon/C2-like connections or sustained mining sessions, and whether only 192.168.70.186 shows the mining pattern or both 192.168.70.186 and 192.168.24.128 do. Then compute the duration using the definition supported by those results, using SPL arithmetic/stats rather than mental subtraction, and report the exact value that matches the question's wording.

### 16:42:57 - s1 -> SH   [REPORT - round 2 - FOUND]
> The mining act in Cisco NVM flow logs is uniquely evidenced by the single dp=3333 (Monero Stratum default port) flow: powershell.exe on 192.168.70.186 (FyodorMalteskesko) -> 45.77.53.176, fss=1534762025 to fes=1534762137, duration 112s computed in SPL. The 4,829 powershell->45.77.53.176:443 flows ar
_full: reports/s1_round_2.md_

### 16:43:07 - SH -> (new)   [ANSWER]
SH's answers to your open questions:
1. Noted; the 443-beacon span is not the better fit because the report shows those flows are numerous short-lived 443 sessions from two hosts, while only one endpoint has a single 3333 Stratum session whose duration was computed directly.

**112** (count) from s1

s1 stayed within the required Cisco NVM flow feed (sourcetype=syslog, source=cisconvmflowdata), verified the full destination-port coverage, showed exactly one dp=3333 flow in the feed, identified only one endpoint performing that Stratum session (192.168.70.186), and computed the session duration in SPL as sum(dur)=112 from fes-fss on that event. The alternative 443 traffic was tested and shown to be many short beacon-like connections from two hosts rather than the mining act the question asks about.

**Premise audit (SH):**
- premise="Coverage: 'endpoint generates Monero cryptocurrency' in Cisco NVM flow logs could appear as a miner/Stratum session on canonical mining ports, or as mining traffic to the same pool over another port such as 443, or under another suspicious process contacting the pool IP. Searches covered canonical port usage fully (full dp listing, unique 3333 event), covered the same destination 45.77.53.176 across hosts/processes/ports with complete stats rows, and covered the named suspicious processes iexeoler.exe and hdoor.exe; no uncovered in-feed representation remains that competes with the chosen 3333 session for this destination." status='VERIFIED' evidence='Round 2 shows full dp listing 22/22 with only one 3333 flow; stats by sa,pn,dp for da=45.77.53.176 returned 4 rows; pn=powershell.exe stats by sa,da,dp returned 7 complete rows; pn IN (iexeoler.exe,hdoor.exe) returned 7 internal-only flows.'
- premise="The question's singular 'the endpoint' refers to a unique endpoint in this feed, not multiple hosts." status='VERIFIED' evidence='Round 2 reports only 192.168.70.186 has the dp=3333 Stratum session; 192.168.24.128 only has short 443 flows to the same destination.'
- premise='The 443 traffic to 45.77.53.176 is not the Monero-generation activity being asked for.' status='VERIFIED' evidence='Round 2 stats by sa,pn,dp for da=45.77.53.176 show 1,015 and 3,814 flows on 443 with avg durations 1.25s and 0.91s, maxima 12s and 31s, versus a single 112s flow on 3333; the report explicitly compares this behavior and rules the 443 pattern out as beacon/C2-like rather than a mining session.'
- premise="The measured duration should be taken from the mining session's flow duration, not from a broader span or hand calculation." status='VERIFIED' evidence='Round 2 computed `dur=fes-fss` and then `stats sum(dur)` over dp=3333, yielding 112 in SPL; this directly matches the asked-for seconds.'
- premise='No rival Cisco NVM flow candidate matches Monero generation better than the chosen event.' status='VERIFIED' evidence='Round 2 states keyword search confirms exactly one event in the feed has dp=3333, and the only alternative traffic to the same IP is the short-lived 443 set from two hosts already behavior-tested and excluded.'

### 16:43:07 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

