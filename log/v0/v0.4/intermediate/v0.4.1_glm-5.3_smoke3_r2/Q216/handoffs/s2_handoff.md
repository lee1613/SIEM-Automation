# s2 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=0_
**Scope:** sourcetype=stream:dns, stream:tcp | fields query, src_ip, dest, connection, duration, flow_id, _time, src_port
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 30

## Prior rounds
- R1: Coinhive DNS only from BSTOLL-L (192.168.247.131); stream:tcp carries duration/flow_id; no number computed.
- R2: verified Coinhive resolved IPs + 12 TCP flows from BSTOLL-L; ws019 = one continuous connection (two overlapping records, same 4-tuple); 45.77.53.176:443 = C2 beaconing (complete query, no flow >60 s); metrics 2219/2777/1603 computed, choice unresolved.
- R3: recovery round, no new queries; answered SH's three asks from held evidence.

## This round
### What I ran
_[trimmed by the runner to fit the word cap]_

### What it means
NOT_FOUND. SH's three asks, from held evidence:
1. **hoth (192.168.9.30): UNCLASSIFIED.** 20 flows total in stream:tcp; only long flows are 2 to 45.77.53.176:8088 (466.136 s, 924.237 s; union 1211.94 s, sum 1390.37 s). Its DNS was never queried; port 8088 is not a standard Stratum port; duration alone cannot distinguish mining from C2/service. Still in scope, not ruled out.
2. **BSTOLL-L vs the question's endpoint: separate host AND separate activity** from 192.168.70.186 — Coinhive browser mining 13:27–14:05 UTC vs FYODOR-L's :3333 flow at 11:28:57 UTC (both Aug 20). If the question's endpoint is 192.168.70.186, BSTOLL-L's Coinhive is not the answer; but it is the only activity in my scope positively named Monero, so I cannot rule it out as the question's referent either — the question names no host.
3. **Monero by 192.168.70.186 from my feed alone:** only the single :3333 flow to 45.77.53.176, 111.786232 s → 112. Port 3333 is the Stratum default — indicative, not proof: no DNS for 45.77.53.176 (hardcoded), no Coinhive, no other mining indicator on FYODOR-L. Its :443 stream to the same IP is eliminated as mining (3884 flows, max 57.7 s, none >60 s — beaconing).

Duration candidates my scope produced: FYODOR-L :3333 = 112; BSTOLL-L Coinhive = 2219 (covered) / 2777 (summed) / 1603 (longest record); hoth :8088
_[trimmed by the runner to fit the word cap]_

## Assumptions
- Coverage: stream:dns query/host_addr — Coinhive found (BSTOLL-L only); 45.77.53.176 reverse lookup 0 events - VERIFIED. stream:tcp duration/flow_id/src_port — Coinhive IPs (12 flows) and dest=45.77.53.176 (4 rows, complete) - VERIFIED. hoth's DNS and its other 18 flows - NOT SEARCHED (UNVERIFIED).
- Selection: BSTOLL-L = only Coinhive resolver - VERIFIED. FYODOR-L :3333 = only mining-indicative flow for that host - VERIFIED. hoth - UNVERIFIED.
- Premise: Coinhive = Monero generation (external, well-established). Port 3333 = Stratum default (external; indicative only). Two ws019 records = one connection (identical 4-tuple) - VERIFIED. duration in µs - VERIFIED.
- UNVERIFIED recollection (R1, not from any query): a ~1367.875 s NVM answer for a 45.77.53.176:443 flow — matches none of my stream:tcp numbers; if accurate, it is NVM-side sessionization my feed cannot reproduce, and it would include C2 beaconing time my evidence eliminates as mining.

## Ruled out
- 45.77.53.176:443 as mining — complete query: 4955 flows (ABUNGST-L 1071, FYODOR-L 3884), all short, max 57.7 s, none >60 s; no DNS resolution for the IP.
- ABUNGST-L as miner — beacons only, no long flow, no Coinhive DNS.
- DNS-resolution window (66 s) as duration — lookups, not generation.

## Open questions for SH
- Does the NVM feed's Monero-tied record show the :3333 flow from 192.168.70.186, and what duration does NVM print for it? (stream:tcp says 111.786232 s for the same 5-tuple.)
- Is the question's endpoint fixed by the NVM line (192.168.70.186), or should the positively-Monero Coinhive host BSTOLL-L override it?
- Can an NVM-side check confirm whether a ~1367.875 s record exists and which 5-tuple it belongs to?

## What I'd tell my replacement
- Retired because: This senior independently ruled out 45.77.53.176:443 as mining and exposed BSTOLL-L Coinhive as separate activity, but it cannot settle a Cisco NVM-only duration question and this round made no new progress. Retire it and hand back the narrowed issue: in Cisco NVM, verify that the only Monero-generating record for 192.168.70.186 is the :3333 flow and compute its duration directly from NVM.
- Scope I owned: sourcetypes=['stream:tcp', 'stream:ip', 'stream:http', 'stream:dns', 'stream:udp'] sources=[] fields=['src', 'dest', 'src_ip', 'dest_ip', 'src_port', 'dest_port', 'app', 'duration', 'bytes', 'host', 'uri', 'query']
- Rounds worked: 3/8  (iterations: 27, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=osquery:results | stats count by name
- index=botsv3 sourcetype=stream:dns (query="*pool*" OR query="*xmr*" OR query="*monero*" OR query="*nanopool*" OR query="*supportxmr*" OR query="*minexmr*" OR query="*coin*" OR query="*hash*") | stats count by query
- index=botsv3 sourcetype=stream:dns host_addr="45.77.53.176" | stats count values(query) as queries values(src_ip) as clients min(_time) as first max(_time) as last
- index=botsv3 sourcetype=stream:dns query="*coinhive*" | stats count min(_time) as first_time max(_time) as last_time by src_ip, query
- index=botsv3 sourcetype=stream:dns query="*coinhive*" | stats values(host_addr) as resolved_ips count by query
- index=botsv3 sourcetype=stream:dns record."DNSQuestionRecord".Name="*pool*" OR record."DNSQuestionRecord".Name="*xmr*" OR record."DNSQuestionRecord".Name="*monero*" OR record."DNSQuestionRecord".Name="*minexmr*" | stats count by record."DNSQuestionRecord".Name
- index=botsv3 sourcetype=stream:dns src_ip=192.168.247.131 | stats count min(_time) as first max(_time) as last by query | sort - count
- index=botsv3 sourcetype=stream:tcp (src_ip=192.168.70.186 OR src_ip=192.168.24.128 OR src_ip=192.168.9.30) | stats count dc(flow_id) as flows by host, src_ip
- index=botsv3 sourcetype=stream:tcp dest=45.77.53.176 | eval dur_s=duration/1000000 | where dur_s > 60 | stats count values(dur_s) as dur_s values(_time) as times values(src_port) as ports by src_ip, dest_port, flow_id
- index=botsv3 sourcetype=stream:tcp dest=45.77.53.176 | stats count dc(flow_id) as flows min(_time) as first max(_time) as last by src_ip, dest_port
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.247.131 (dest="104.20.208.59" OR dest="104.20.209.59" OR dest="217.182.164.14" OR dest="37.187.165.41" OR dest="37.187.166.108" OR dest="37.187.167.21" OR dest="37.187.167.47") | stats count dc(flow_id) as flows min(_time) as first max(_time) as last sum(duration) as total_duration max(duration) as max_duration by dest, dest_port
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.247.131 (dest="104.20.208.59" OR dest="217.182.164.14" OR dest="37.187.165.41" OR dest="37.187.166.108" OR dest="37.187.167.21" OR dest="37.187.167.47") | stats count values(_time) as times values(endtime) as endtimes values(duration) as durations values(src_port) as ports by flow_id, dest | sort dest
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.247.131 | stats count dc(flow_id) as flows sum(duration) as sum_dur by dest, dest_port | sort - count
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.70.186 dest=45.77.53.176 | stats count dc(flow_id) as flows min(_time) as first max(_time) as last sum(duration) as sum_dur max(duration) as max_dur by dest_port
- index=botsv3 sourcetype=stream:tcp | eval dur_s=duration/1000000 | where dur_s>100 | stats count values(host) as hosts values(app) as apps values(dur_s) as durations by src_ip, dest, dest_port
