# s2 - Q208 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=7_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BSTOLL-L (coinhive OR cryptonight OR stratum OR xmrig OR cpuminer OR minergate OR monero OR miner) | stats count by EventCode
- index=botsv3 sourcetype=stream:http src=10.0.0.0/8 OR src=192.168.0.0/16 (coinhive OR cryptonight OR stratum OR xmrig OR minergate OR monero OR miner OR pool) | stats count by sourcetype
- index=botsv3 sourcetype=stream:http (coinhive OR cryptonight OR stratum OR xmrig OR minergate OR monero OR miner OR pool) | stats count min(_time) as first_t max(_time) as last_t values(src) as src values(dest) as dest values(url) as url by host
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BSTOLL-L EventCode=3 Image="*chrome.exe" | stats count min(_time) as first_t max(_time) as last_t values(DestinationIp) as dest_ips values(DestinationHostname) as dest_hosts by ProcessId
### What it means
Intention: No Sysmon network events for chrome.exe. Let me check all Sysmon EventCode=3 network connections on BSTOLL-L to see what destinations were contacted.
