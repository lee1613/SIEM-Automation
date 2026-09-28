# s1 - Q323 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=0_
**Scope:** sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational | sourcetype=stream:tcp | sourcetype=stream:ip | fields=host, DestinationIp, EventCode, src_ip, dest_ip
**Insight:** FOUND
**Candidate:** ABUNGST-L,FYODOR-L   **Confidence:** 93

## Prior rounds
- R1: Sysmon "45.77.53.176" | stats count by host, DestinationIp, EventCode -> complete 2-of-2: ABUNGST-L (1070), FYODOR-L (3850), all EventCode=3. Complete 4-of-4 stream:tcp and stream:ip sets corroborated (192.168.70.186 = 3885/4486 flows, 192.168.24.128 = 1071/1698; 192.168.9.30 only 2/4). 192.168.9.30 ruled out as server-role on a partial 50-of-420 listing.
- R2 (clarify, no tools): confirmed the decisive sets were complete and fully read; host↔stream-IP pairing is count-based inference, not a field join; 192.168.9.30's identity not fully attributed.

## This round
### What I ran
- No new queries — settled p1 and p2 from round-1 word-for-word output, per instruction.

### What it means
**p1 VERIFIED.** The complete Sysmon aggregation for 45.77.53.176 (quoted verbatim in premise_updates) returned 2 of 2 rows — total_event_count=2, returned=2, nothing truncated — and every row is an EventCode=3 network-connection event with DestinationIp=45.77.53.176 carrying a host name. That is the host-attributed act the question asks about, and within the host-attributed telemetry searched (Sysmon) this complete set names every monitored endpoint host that performed it: ABUNGST-L and FYODOR-L, and no others.

**p2 VERIFIED.** The same complete result names exactly those two hosts; 192.168.9.30 appears as no host in it. Stream rows are corroboration only, never the selection basis: the complete 4-of-4 stream:tcp set shows 192.168.24.128→C2 count=1071 and 192.168.70.186→C2 count=3885 against 192.168.9.30→C2 count=2, and the partial role listing showed 192.168.9.30 receiving inbound 80/8080 — server behavior, not endpoint beaconing. The question's "at least two" is satisfied by the two hosts whose own records show the act.

**Why these hostnames.** ABUNGST-L and FYODOR-L are the only hosts whose own telemetry records the act named by the question (a process on the host initiating a connection to the adversary C2 45.77.53.176). No third candidate remains live: 192.168.9.30 is absent from the complete Sysmon host set and shows server-role behavior; 192.168.8.103 contacted 192.168.9.30, not the C2. Alphabetical order gives the submit-ready value: ABUNGST-L,FYODOR-L.

## Ruled out
- 192.168.9.30 as a third endpoint - absent from the complete Sysmon host set for the C2 IP; only 2 stream:tcp flows to it; receives inbound 80/8080 (server role).
- 192.168.8.103 - contacted 192.168.9.30, not the C2 IP.

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['XmlWinEventLog:Microsoft-Windows-Sysmon/Operational', 'stream:dns', 'stream:tcp', 'stream:http'] sources=[] fields=['host', 'src_ip', 'dest_ip', 'DestinationIp', 'query', 'dest_port', 'DestinationPort', 'ProcessGuid', 'Image']
- Rounds worked: 2/5  (iterations: 12, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsl3 sourcetype=stream:ip "45.77.53.176" | stats count by src_ip, dest_ip
- index=botsv3 "45.77.53.176" | stats count by sourcetype, source
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" "45.77.53.176" | stats count by host, DestinationIp, EventCode
- index=botsv3 sourcetype=stream:http "45.77.53.176" | stats count by src_ip, dest_ip, http_user_agent
- index=botsv3 sourcetype=stream:http "45.77.53.176" | stats count by src_ip, uri, url
- index=botsv3 sourcetype=stream:ip "45.77.53.176" | stats count by src_ip, dest_ip
- index=botsv3 sourcetype=stream:tcp "45.77.53.176" | stats count by src_ip, dest_ip
- index=botsv3 sourcetype=stream:tcp src_ip=192.168.9.30 OR dest_ip=192.168.9.30 | stats count by src_ip, dest_ip, src_port, dest_port
