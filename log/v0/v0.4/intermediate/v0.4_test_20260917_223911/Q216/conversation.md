# Q216 — SH <-> Senior conversation

### 22:39:42 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['_time', 'src_ip', 'dest_ip', 'dest_port', 'protocol', 'bytes', 'packets', 'flow_duration', 'app', 'url', 'domain']
**Technique:** hunter
**Reason:** The question is explicitly anchored to Cisco NVM flow logs, and this feed is available under the source axis rather than by a distinct sourcetype name; a tightly scoped senior can determine the mining interval from that dataset without needing broader coverage.

Using only the Cisco NVM flow feed at source="cisconvmflowdata" within index=botsv3, identify the endpoint traffic that corresponds to Monero cryptocurrency generation and establish for how many total seconds that endpoint is generating Monero. The result must be a single rounded whole-number duration in seconds.

