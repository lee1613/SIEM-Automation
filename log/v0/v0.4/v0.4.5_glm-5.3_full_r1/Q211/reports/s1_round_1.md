# s1 - Q211 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Scope:** sourcetype=stream:dns, stream:tcp | source=stream:dns, stream:Splunk_DNSIntegrity, stream:Splunk_DNSRequestResponse, stream:tcp | fields query, host_addr, src_ip, dest_ip, dest_port

**Insight:** FOUND  **Candidate:** 6  **Confidence:** 70

## Prior rounds
- None — this is round 1.

## This round
### What I ran
- search_keyword coinhive / mining -> 0 field-name matches (manifest has no mining-named field).
- `index=botsv3 sourcetype=stream:dns coinhive* | stats count by sourcetype, source` -> 3 sources, 28 events (DNSIntegrity 7, DNSRequestResponse 7, stream:dns 14).
- get_raw_events stream:dns coinhive (20/20 read) -> 6 distinct hostnames, 7 resolved IPs, all queries from src 192.168.247.131.
- `... | stats dc(query), values(query) by src_ip` -> 1 endpoint (192.168.247.131), dc(query)=6: coinhive.com, ws001/ws005/ws011/ws014/ws019.coinhive.com.
- `index=botsv3 sourcetype=stream:tcp (dest_ip=<each of the 7 resolved IPs>) | stats count, dc(src_ip), values(dest_ip), values(dest_port)` -> 12 events, 1 source (192.168.247.131), 6 distinct dest IPs, all port 443.

### What it means
The mining destinations are Coinhive: one endpoint (192.168.247.131, BSTOLL-L) queried 6 distinct mining hostnames and made 12 outbound TLS connections on port 443 to 6 distinct resolved mining IPs. Both defensible units of "destination" agree on 6 — 6 hostnames visited, 6 IPs actually contacted. A 7th IP (104.20.209.59, an A record for coinhive.com) was resolved in DNS but never connected to, so it is not "visited".

## Ruled out
- Other Frothly endpoints as miners: only 192.168.247.131 appears in both the coinhive DNS queries and TCP connections to the resolved IPs.
- 104.20.209.59 as a visited destination: resolved but absent from the stream:tcp result for all 7 IPs.
- 7-IP "resolved" reading: contradicted by "visited" — TCP shows contact to only 6.

## Ruled out (residual, unverified)
- Non-Coinhive mining domains and stream:http were not searched before tools were withdrawn; if other mining families exist in the data the count could be higher.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
