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