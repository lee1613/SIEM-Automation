# s2 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=3_
**Scope:** sourcetype=stream:tcp, stream:http, stream:dns, cisco:asa, aws:cloudwatchlogs:vpcflow | fields=src_ip, dest_ip, dest_port, time_taken, bytes_in/out, data_packets_in/out, timestamp, endtime
**Insight:** FOUND   **Candidate:** 112   **Confidence:** 95

## Prior rounds
- R1 (this worker): stream:tcp shows exactly one 192.168.70.186→45.77.53.176:3333 flow, time_taken 111,786,232 µs (111.786 s), epoch 1534762025.54–1534762137.32, 5.76MB out/39KB in, 3993:1 data-packet ratio; 3,884 port-443 flows to same IP ruled out as C2/beacon; stream:http corroborates session + Struts2 reverse shell to 45.77.53.176:8088; DNS has no pool hostname (raw-IP connection). cisco:asa and vpcflow left UNVERIFIED.
- s1 (NVM scope): narrowed NVM candidate to a single 112-second 3333 flow.

## This round
### What I ran
- get_sourcetype_fields cisco:asa -> src_ip/dest_ip/dest_port/action fields, 80,192 events, source udp:514.
- `cisco:asa (src_ip=192.168.70.186 OR dest_ip=192.168.70.186 OR src_ip=45.77.53.176 OR dest_ip=45.77.53.176) | stats ... by src_ip dest_ip dest_port transport` -> 2 rows, ZERO involving 192.168.70.186 or port 3333; only 192.168.9.30→45.77.53.176:8088 (reverse shell, allowed, 1534763637–1534764841) and its teardown.
- get_sourcetype_fields aws:cloudwatchlogs:vpcflow -> src_ip/dest_ip/dest_port/start_time/end_time, 97,448 events, AWS ENIs only.
- `aws:cloudwatchlogs:vpcflow (src_ip=192.168.70.186 OR dest_ip=192.168.70.186 OR src_ip=45.77.53.176 OR dest_ip=45.77.53.176) | stats ...` -> 0 events.
- `stream:tcp src_ip=192.168.70.186 dest_port=3333 | stats ...` -> exactly 1 flow, dest 45.77.53.176, sum(time_taken)=111,786,232 µs.

### What it means
FOUND: both previously-unverified feeds are now tested and SILENT for this host/destination pair — cisco:asa has no 192.168.70.186 record at all (its only 45.77.53.176 traffic is the 192.168.9.30 reverse shell on 8088, after the mining window), and vpcflow has zero records for either IP (AWS-internal ENIs only). Neither adds a mining session nor contradicts the measurement. The completeness check confirms the lone 3333 session is the host's only port-3333 flow anywhere in stream:tcp. Packet-level duration: time_taken 111,786,232 µs = 111.786232 s, cross-checked by endtime−timestamp (10:48:57.322257Z − 10:47:05.536706Z = 111.7856 s) → **112 seconds**. The 3333 session, not the 443 beacons, is the Monero-generation act: 5.76MB sustained outbound upload with 3,993 data packets out vs 1 in on the canonical Stratum pool port, versus the 443 set's failed/refused ~824B SSL handshakes (C2 profile, ruled out per SH's confirmation). Answer is submission-ready and matches s1's NVM candidate.

## Assumptions
- Coverage: cisco:asa — queried for both IPs, all ports: silent on 192.168.70.186, no 3333 records — VERIFIED. aws:cloudwatchlogs:vpcflow — queried for both IPs: 0 events — VERIFIED. stream:tcp/http/dns — queried in R1 — VERIFIED. No other feed in scope.
- Selection: the single 3333 flow is the host's only 3333 flow in all of stream:tcp (query above, 1 row) — VERIFIED. 443 flows excluded as C2/beacon (R1 stats + raw events; SH confirmed) — VERIFIED.
- Premise: time_taken is microseconds — VERIFIED (endtime−timestamp = 111.7856 s matches time_taken/1e6).
- Premise: 45.77.53.176:3333 is Monero/pool-related — VERIFIED behaviourally (share-submission profile) and by attacker-infra linkage (Struts2 shell to 45.77.53.176:8088); no explicit "monero" string exists in non-NVM feeds, which is the strongest available external evidence.

## Ruled out
- cisco:asa as a source of additional/contradictory mining sessions — no 192.168.70.186 records at all; only the 192.168.9.30:8088 reverse shell.
- aws:cloudwatchlogs:vpcflow — zero records for either IP; AWS-internal ENI traffic only.
- Port-443 flows to 45.77.53.176 (3,884) — C2/beacon profile, not mining.
- Any second 3333 session/pool — none exists for this host.

## Open questions for SH
- None. The external-verification premise is closed; 112 is ready for submission.

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "cisco:asa"}` (52 of 105 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: You have done your job as the non-overlapping corroboration senior: you independently confirmed the single 3333 session and closed the uncovered-feed premise. This question's final answer must now come from the Cisco NVM senior because the measurement is explicitly 'According to the Cisco NVM flow logs'.
- Scope I owned: sourcetypes=['stream:tcp', 'stream:ip', 'stream:http', 'stream:dns'] sources=[] fields=['src_ip', 'dest_ip', 'src_port', 'dest_port', 'bytes_in', 'bytes_out', 'duration', 'query', 'answer', 'uri', 'time']
- Rounds worked: 2/8  (iterations: 17, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=aws:cloudwatchlogs:vpcflow (src_ip=192.168.70.186 OR dest_ip=192.168.70.186 OR src_ip=45.77.53.176 OR dest_ip=45.77.53.176) | stats count values(dest_port) as dports min(start_time) as first_t max(end_time) as last_t by src_ip dest_ip
- index=botsv3 sourcetype=cisco:asa (src_ip=192.168.70.186 OR dest_ip=192.168.70.186 OR src_ip=45.77.53.176 OR dest_ip=45.77.53.176) | stats count values(action) as actions values(dest_port) as dports values(src_port) as sports min(_time) as first_t max(_time) as last_t by src_ip dest_ip dest_port transport
- index=botsv3 sourcetype=stream:dns 45.77.53.176 | stats count values(record_type) as rectypes values(answer) as answers values(query) as queries by src_ip | head 20
- index=botsv3 sourcetype=stream:dns src_ip=192.168.70.186 earliest=1534759000 latest=1534763000 | stats count values(answer) as answers by query | sort - count | head 30
- index=botsv3 sourcetype=stream:dns src_ip=192.168.70.186 query="176.53.77.45.in-addr.arpa" | stats count values(answer) as answers values(record_type) as rt min(_time) as first_t max(_time) as last_t
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.70.186 dest_ip=45.77.53.176 | stats count dc(flow_id) as flows min(_time) as first_t max(_time) as last_t sum(bytes) as bytes_total sum(bytes_in) as bytes_in sum(bytes_out) as bytes_out sum(duration) as dur_total by dest_port
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.70.186 dest_ip=45.77.53.176 | stats count dc(flow_id) as flows min(_time) as first_t max(_time) as last_t values(dest_port) as ports sum(bytes) as bytes_total sum(bytes_in) as bytes_in sum(bytes_out) as bytes_out
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.70.186 dest_port=3333 | stats count dc(flow_id) as flows values(dest_ip) as dests sum(time_taken) as total_us min(_time) as first_t max(_time) as last_t
