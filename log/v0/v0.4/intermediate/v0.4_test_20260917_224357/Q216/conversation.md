# Q216 — SH <-> Senior conversation

### 22:44:22 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['_time', 'src_ip', 'dest_ip', 'dest_port', 'protocol', 'bytes', 'packets', 'duration', 'app', 'url', 'domain']
**Technique:** hunter
**Reason:** The question names Cisco NVM flow logs explicitly, and this feed is present under sourcetype=syslog with source=cisconvmflowdata, so a single scoped senior can answer it without parallel work.

Using Cisco NVM flow logs in source cisconvmflowdata within index=botsv3, establish which endpoint is generating Monero cryptocurrency traffic and determine for how many seconds that activity persists, rounded to the nearest second.

