# s1 - Q225 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=9_
**Scope:** sourcetype=stream:udp, stream:http, access_combined, aws:s3:accesslogs, aws:cloudtrail | fields=src_ip, dest_ip, dest_port, _raw, uri_path, object
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 15

## Prior rounds
- Round 1: Searched for "memcache"/"Taedonggang" text across stream:http, stream:tcp, stream:udp, bash_history — all 0 events; hex search for "jpeg" in stream:tcp — 0 events.

## This round
### What I ran
- `sourcetype=stream:udp dest_port=11211 | stats count by src_ip, dest_ip` -> 1 pair: 13.125.33.130 -> 172.16.0.178, 17 events
- `get_raw_events` on those events -> memcached "set injected" commands with payloads "CRYP70KOL5CH-OWNS-YOU" (105 B) and "6HOUL@G3RpwnzFrothyl4Life" (50000 B); server replies STORED / VALUE injected
- `stream:udp dest_port=11211 | rex "set\s+(?<mkey>...)" | stats count by mkey, mlen` -> only key "injected", lengths 105 and 50000
- `stream:udp dest_port=11211 "jpeg" OR "jpg" OR "Taedonggang"` -> 0 events
- `stream:http "6HOUL"` / `"CRYP70KOL"` -> 0 events; `access_combined ".jpeg" OR ".jpg"` -> 0; `aws:s3:accesslogs ".jpeg" OR ".jpg"` -> 0

### What it means
The memcached attack is identified and its payload data extracted, but no .jpeg filename appears in the payload itself or in any web/S3 feed in scope. The payload string "6HOUL@G3RpwnzFrothyl4Life" looks like a credential; the .jpeg filename likely surfaces where that payload is reused (aws:cloudtrail is in scope and unsearched for it).

## Ruled out
- Payload-embedded filename — memcached events contain no jpeg/jpg/Taedonggang text
- stream:http, access_combined, aws:s3:accesslogs — no .jpeg/.jpg references, no payload-string reuse
- Other memcached conversations — only 13.125.33.130 -> 172.16.0.178 exists; no TCP 11211 traffic

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
