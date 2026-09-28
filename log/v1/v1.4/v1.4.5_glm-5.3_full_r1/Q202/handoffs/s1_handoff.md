# s1 - Q202 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=7_
**Scope:** sourcetype=hardware, osquery:results, access_combined, aws:description | fields: host, cpu_type, columns.cpu_brand, columns.feature, columns.value, clientip, uri_path
**Insight:** partial (credible candidate, one web host's CPU inferred)
**Candidate:** E5-2676 v3   **Confidence:** 70

## Prior rounds
R1: Found the only CPU-model fields then known (hardware.cpu_type, osquery cpu_brand) = "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz" on 3 gacrux hosts; web-log hosts = 4 gacrux + hoth; submitted E5-2676 v3 with hoth and the 4th gacrux host unverified.

## This round
### What I ran
- access_combined | stats count by host, source -> gacrux fleet logs /var/log/httpd/access_log; hoth logs /var/log/apache2/access.log (5 rows, all read)
- osquery:results host=hoth | stats count by name -> 16 queries incl. pack_hardware-monitoring_cpuid (64 events)
- cpuid | stats count by columns.feature, columns.value -> product_name "AMD FX(tm)-8120 Eight-Core Processor" on hoth (50 of 64 rows read; product_name captured)
- access_combined host=hoth | stats count by clientip, uri_path -> 14 rows, ALL /suitecrm/* from internal 192.168.8.x clients
- aws:description ec2_instances (sample) -> i-0920036c8ca91e501 tagged aws:autoscaling:groupName="WebServers", t2.medium, AMI ami-0e86606d

### What it means
AWS infrastructure names the web tier: a gacrux host carries the "WebServers" auto-scaling-group tag, and all four gacrux instances serve Apache behind the Frothly ELB (ELB-HealthChecker user agents). hoth is an internal SuiteCRM app server (192.168.9.30) serving only internal clients, with a different CPU (AMD FX-8120) — ruled out of the web-server set. The processor number on the web servers is E5-2676 v3, directly recorded on 3 of the 4 (hardware cpu_type, corroborated by osquery cpu_brand); the 4th (i-0920036c8ca91e501) has no CPU record and is inferred from shared ASG/AMI/fleet uniformity.

## Ruled out
- hoth as a "web server" for this question - internal SuiteCRM server only (all 240 of its access log rows are /suitecrm/* from 192.168.8.x); not in the WebServers ASG; CPU is AMD FX-8120, not the fleet's Xeon
- code42:computer, WinHostMon/Script:GetEndpointInfo, dmesg/syslog core counts - no CPU-model data or no web servers (R1)

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p1 - amend or settle that one. The text you sent was discarded: "CPU-model evidence in the dataset lives in three feeds: hardware.cpu_type and os"
- selection premise not filed: you already have an open selection premise p2 - amend or settle that one. The text you sent was discarded: "The web servers the question means are the gacrux EC2 fleet in the 'WebServers' "

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=osquery:results host=hoth name=pack_hardware-monitoring_cpuid | st…` (50 of 64 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: Done with this scope. It established the web-server set well enough to carry forward, but its original coverage premise was refuted and its CPU answer for one selected web host remains inferred rather than directly evidenced.
- Scope I owned: sourcetypes=['aws:description', 'access_combined', 'aws:elb:accesslogs', 'osquery:results', 'hardware', 'cpu', 'top', 'WinHostMon', 'Script:GetEndpointInfo', 'Unix:Version'] sources=[] fields=['host', 'dest', 'instance_id', 'private_ip_address', 'public_dns_name', 'name', 'tag*', 'status', 'uri_path', 'http_user_agent', 'cpu', 'model', 'processor', 'brand', 'manufacturer', 'caption']
- Rounds worked: 2/5  (iterations: 22, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 (sourcetype=access_combined OR sourcetype=apache_error OR sourcetype=aws:elb:accesslogs) | stats count by sourcetype, host
- index=botsv3 host=hoth | stats count by sourcetype
- index=botsv3 sourcetype=access_combined host=hoth | stats count by clientip, uri_path
- index=botsv3 sourcetype=access_combined | stats count by host, source
- index=botsv3 sourcetype=aws:description source="us-west-1:ec2_instances" | stats count by instances{}.instance_id, instances{}.instance_type, instances{}.tags{}.value
- index=botsv3 sourcetype=aws:description | stats count by sourcetype, source
- index=botsv3 sourcetype=code42:computer | stats count by host
- index=botsv3 sourcetype=osquery:results columns.cpu_brand=* | stats count by host, columns.cpu_brand
- index=botsv3 sourcetype=osquery:results host=hoth name=pack_hardware-monitoring_cpuid | stats count by columns.feature, columns.value
- index=botsv3 sourcetype=osquery:results host=hoth | stats count by name
