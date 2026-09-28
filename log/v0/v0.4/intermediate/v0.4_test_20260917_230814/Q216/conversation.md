# Q216 — SH <-> Senior conversation

### 23:08:40 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['_time', 'src_ip', 'dest_ip', 'dest_port', 'app', 'url', 'domain', 'bytes', 'packets', 'duration']
**Technique:** hunter
**Reason:** This question is explicitly anchored to Cisco NVM flow logs, and the source-axis mapping in the case file identifies cisconvmflowdata as the relevant feed under sourcetype syslog.

Using only the Cisco NVM flow logs in source cisconvmflowdata, identify the endpoint that is generating Monero cryptocurrency traffic and determine the total time span, in seconds, during which that endpoint is generating Monero-related network activity. Establish the specific flow indicators that justify treating the traffic as Monero mining/generation, then derive the rounded duration from the first to last relevant activity.

