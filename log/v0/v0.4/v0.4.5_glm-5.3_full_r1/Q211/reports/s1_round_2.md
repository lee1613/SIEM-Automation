# s1 - Q211 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=3_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:dns (minergate OR nanopool OR stratum OR monero OR xmr OR xmrig OR cryptonight OR minexmr OR supportxmr OR dwarfpool OR nicehash OR hashvault OR miningpoolhub OR moneropool OR coinpot OR prohashing OR zpool OR f2pool OR antpool OR cryptoloot OR jsecoin OR coinhive OR deepminer OR coinerra OR ethermine OR authedmine OR webminepool OR minero) | stats count by query, src_ip | sort -count
- index=botsv3 sourcetype=stream:dns (minergate OR nanopool OR stratum OR monero OR xmr OR xmrig OR cryptonight OR minexmr OR supportxmr OR dwarfpool OR nicehash OR hashvault OR miningpoolhub OR moneropool OR coinpot OR prohashing OR zpool OR f2pool OR antpool OR cryptoloot OR jsecoin OR coinhive OR deepminer OR coinerra OR ethermine OR authedmine OR webminepool OR minero) | stats count by query, src_ip | sort -count
- index=botsv3 sourcetype=stream:http (minergate OR nanopool OR stratum OR monero OR xmr OR xmrig OR cryptonight OR minexmr OR supportxmr OR dwarfpool OR nicehash OR hashvault OR miningpoolhub OR moneropool OR coinpot OR prohashing OR zpool OR f2pool OR antpool OR cryptoloot OR jsecoin OR coinhive OR deepminer OR coinerra OR ethermine OR authedmine OR webminepool OR minero) | stats count by url, src_ip | sort -count
- index=botsv3 sourcetype=stream:http (dest_ip="37.187.167.47" OR dest_ip="37.187.167.21" OR dest_ip="37.187.166.108" OR dest_ip="37.187.165.41" OR dest_ip="217.182.164.14" OR dest_ip="104.20.209.59" OR dest_ip="104.20.208.59") | stats count by dest_ip, src_ip, url | sort -count
### What it means
Intention: No HTTP contact with the mining IPs. Now check TCP for stratum-style ports (3333, 4444, 5555, 7777, 8080, 14444, 14433) to any external destination, which would indicate pool mining beyond Coinhive.
