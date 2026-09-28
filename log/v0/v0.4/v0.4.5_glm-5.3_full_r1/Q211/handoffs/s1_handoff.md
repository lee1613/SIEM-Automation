# s1 - Q211 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=6_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:tcp dest_ip="45.77.53.176" | stats count, dc(src_ip) as srcs, values(src_ip) as src_ips, values(dest_port) as ports, min(_time) as first, max(_time) as last
- index=botsv3 sourcetype=stream:dns (src_ip="192.168.24.128" OR src_ip="192.168.70.186" OR src_ip="192.168.9.30") | stats count, values(host_addr) as resolved_ips by query | sort -count
- index=botsv3 sourcetype=stream:dns query="splunk.froth.ly" | stats count, values(host_addr) as resolved_ips, dc(src_ip) as src_count
- index=botsv3 sourcetype=stream:tcp dest_ip="45.77.53.176" | stats count by src_ip, dest_port | sort -count
### What it means
Intention: The bulk is TLS on 443 (4955 events) plus one stratum-port connection on 3333. I need to identify what 45.77.53.176 is — checking whether any DNS query from these endpoints resolved to it, and what the 3333 connection actually was.

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=stream:dns (src_ip="192.168.24.128" OR src_ip="192.168.70.186" OR …` (50 of 1479 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['stream:dns', 'stream:tcp', 'stream:http', 'stream:ip', 'XmlWinEventLog:Microsoft-Windows-Sysmon/Operational'] sources=[] fields=['host', 'query', 'src_ip', 'dest_ip', 'DestinationIp', 'dest_port', 'DestinationPort', 'bytes_in', 'bytes_out', '_time']
- Rounds worked: 3/3  (iterations: 24, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 coinhive* | stats count by sourcetype, source | sort -count
- index=botsv3 sourcetype=stream:dns (minergate OR nanopool OR stratum OR monero OR xmr OR xmrig OR cryptonight OR minexmr OR supportxmr OR dwarfpool OR nicehash OR hashvault OR miningpoolhub OR moneropool OR coinpot OR prohashing OR zpool OR f2pool OR antpool OR cryptoloot OR jsecoin OR coinhive OR deepminer OR coinerra OR ethermine OR authedmine OR webminepool OR minero) | stats count by query, src_ip | sort -count
- index=botsv3 sourcetype=stream:dns (src_ip="192.168.24.128" OR src_ip="192.168.70.186" OR src_ip="192.168.9.30") | stats count, values(host_addr) as resolved_ips by query | sort -count
- index=botsv3 sourcetype=stream:dns coinhive* | stats count by sourcetype, source
- index=botsv3 sourcetype=stream:dns coinhive* | stats dc(query) as distinct_queries, dc(host_addr) as distinct_ips, values(query) as queries by src_ip
- index=botsv3 sourcetype=stream:dns host_addr="45.77.53.176" | stats count, values(query) as queries, values(src_ip) as src_ips, min(_time) as first_seen, max(_time) as last_seen
- index=botsv3 sourcetype=stream:dns query="splunk.froth.ly" | stats count, values(host_addr) as resolved_ips, dc(src_ip) as src_count
- index=botsv3 sourcetype=stream:http (dest_ip="37.187.167.47" OR dest_ip="37.187.167.21" OR dest_ip="37.187.166.108" OR dest_ip="37.187.165.41" OR dest_ip="217.182.164.14" OR dest_ip="104.20.209.59" OR dest_ip="104.20.208.59") | stats count by dest_ip, src_ip, url | sort -count
- index=botsv3 sourcetype=stream:http (minergate OR nanopool OR stratum OR monero OR xmr OR xmrig OR cryptonight OR minexmr OR supportxmr OR dwarfpool OR nicehash OR hashvault OR miningpoolhub OR moneropool OR coinpot OR prohashing OR zpool OR f2pool OR antpool OR cryptoloot OR jsecoin OR coinhive OR deepminer OR coinerra OR ethermine OR authedmine OR webminepool OR minero) | stats count by url, src_ip | sort -count
- index=botsv3 sourcetype=stream:tcp (dest_ip="37.187.167.47" OR dest_ip="37.187.167.21" OR dest_ip="37.187.166.108" OR dest_ip="37.187.165.41" OR dest_ip="217.182.164.14" OR dest_ip="104.20.209.59" OR dest_ip="104.20.208.59") | stats count, dc(src_ip) as distinct_sources, values(src_ip) as srcs, values(dest_ip) as dests, values(dest_port) as ports by sourcetype, source
- index=botsv3 sourcetype=stream:tcp (dest_port=3333 OR dest_port=4444 OR dest_port=5555 OR dest_port=7777 OR dest_port=14444 OR dest_port=14433 OR dest_port=45560 OR dest_port=14433) | stats count, dc(src_ip) as srcs, values(src_ip) as src_ips by dest_ip, dest_port | sort -count
- index=botsv3 sourcetype=stream:tcp dest_ip="45.77.53.176" | stats count by src_ip, dest_port | sort -count
- index=botsv3 sourcetype=stream:tcp dest_ip="45.77.53.176" | stats count, dc(src_ip) as srcs, values(src_ip) as src_ips, values(dest_port) as ports, min(_time) as first, max(_time) as last
