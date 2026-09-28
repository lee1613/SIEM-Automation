# s2 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=10_
**Scope:** sourcetype=stream:dns, stream:tcp | fields query, src_ip, dest, connection, duration, flow_id, _time
**Insight:** NOT_FOUND (endpoint + session verified; single duration metric unresolved)
**Candidate:** none   **Confidence:** 18

## Prior rounds
- R1: Coinhive DNS only from BSTOLL-L (192.168.247.131); stream:tcp carries duration/flow_id; no number computed.
- R2: verified Coinhive resolved IPs and 12 TCP flows; adjudicated 45.77.53.176 (C2 beaconing on 443, not mining); computed 2219/2777/1603 but could not close the metric choice.

## This round
### What I ran
- get_raw_events coinhive -> resolved IPs: coinhive.com 104.20.208.59/.209.59; ws001 217.182.164.14; ws005 37.187.165.41; ws011 37.187.166.108; ws014 37.187.167.21; ws019 37.187.167.47.
- stream:tcp src_ip=192.168.247.131 dest IN (7 IPs) -> 12 flows, all :443 ssl; two long flows to ws019: 1603196352 µs and 1173833444 µs.
- get_raw_events 37.187.167.47 -> both ws019 flows use src_port 49844 (same 4-tuple), overlap 13:45:47.310–13:55:04.904 (~557.6 s) → ONE continuous connection; µs unit verified (duration = timestamp→endtime span exactly).
- stream:tcp dest=45.77.53.176 -> 4 rows COMPLETE: ABUNGST-L 1071 flows :443; FYODOR-L 3884 :443 (max 57.7 s) + 1 :3333 (111.786 s); hoth 2 :8088 (466.136, 924.237 s).
- dest=45.77.53.176 dur_s>60 -> 3 rows COMPLETE: only :3333 and :8088; NO :443 flow >60 s to that IP.
- stream:dns host_addr=45.77.53.176 -> 0 events (no DNS resolution).
- stream:tcp src_ip=192.168.247.131 by dest -> 344 rows: BSTOLL-L never contacts 45.77.53.176 (confirmed by the complete dest= query).

### What it means
NOT_FOUND for one number. The Monero-generating endpoint in stream telemetry is BSTOLL-L: sole Coinhive resolver, TCP-verified to all six mining-server IPs. Its mining is ONE continuous connection to ws019.coinhive.com (37.187.167.47:443, 4-tuple :49844), 13:28:21.707Z→14:05:21.057Z = 2219.35 s; stream:tcp splits it into two overlapping records (1603.196 + 1173.833 = 2777.03 s, overlap ~557.6 s). Metric unresolved: 2219 (covered) vs 2777 (summed) vs 1603 (longest record) — my scope cannot see NVM's records to close it. The competing suspicion is resolved: 45.77.53.176:443 is C2 beaconing (4955 short flows, max 57.7 s, no flow >60 s, no DNS resolution), not a mining session; long flows to it exist only on :3333 (FYODOR-L, 111.786 s) and :8088 (hoth, 466.136 + 924.237 s).

## Assumptions
- Coverage: stream:dns query/host_addr — Coinhive found (BSTOLL-L only), 45.77.53.176 reverse lookup 0 events - VERIFIED. stream:tcp duration/flow_id/src_port — Coinhive IPs (12 flows) and dest=45.77.53.176 (complete) - VERIFIED. Long flows from 192.168.x srcs to OTHER dests: >100 s listing truncated (50 of 1545 read, only 172.16.x srcs) - UNVERIFIED, but all Monero-indicative destinations were covered by complete targeted queries.
- Selection: BSTOLL-L = only Coinhive resolver - VERIFIED. FYODOR-L:3333 and hoth:8088 remain unadjudicated alternates tied to 45.77.53.176 (what hoth is, and whether 8088 is mining vs C2) - UNVERIFIED.
- Premise: Coinhive = Monero generation (external knowledge, well-established).
- Premise: two ws019 records = one connection (identical 4-tuple; a host cannot hold two simultaneous connections on one 4-tuple) - VERIFIED by raw events.
- Premise: duration is microseconds - VERIFIED (1603196352 µs = exact timestamp→endtime span).

## Ruled out
- 45.77.53.176:443 as a long mining session — 4955 flows, all short (max 57.7 s), beaconing pattern; no flow >60 s (complete query).
- ABUNGST-L as miner — 1071 short beacons, no long flow, no Coinhive DNS.
- DNS-window-as-duration (66 s) — resolution, not generation.

## Open questions for SH
- Does the retired NVM senior's flow tie Monero to 45.77.53.176:443 or to a Coinhive IP (37.187.167.47)? My evidence says the 443 stream is C2 beaconing; a ~1368 s NVM flow there would be an NVM-side aggregation with no single-flow counterpart in stream:tcp.
- Is hoth (192.168.9.30) an in-scope endpoint, and is its :8088 traffic to 45.77.53.176 mining or C2?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:tcp | eval dur_s=duration/1000000 | where dur_s>100 | stats…` (50 of 1545 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:tcp src_ip=192.168.247.131 | stats count dc(flow_id) as flo…` (50 of 344 rows seen). A claim resting on them alone is UNVERIFIED._
