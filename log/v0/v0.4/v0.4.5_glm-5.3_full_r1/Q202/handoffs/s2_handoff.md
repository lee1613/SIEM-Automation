# s2 - Q202 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=1_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=top | stats count by host
### What it means
Intention: `top` covers gacrux.i-0920036c8ca91e501 (23,917 events) — Unix TA top output can carry a CPU-model header. I'll search that host's top and ps events for a processor string (Xeon/Intel), and sample raw top events to see the header structure.


## What I'd tell my replacement
- Retired because: api_failed: transport failure
- Scope I owned: sourcetypes=['hardware', 'osquery:results', 'aws:description', 'aws:cloudwatch', 'aws:config:rule', 'cloud-init', 'amazon-ssm-agent', 'amazon-ssm-agent-too_small', 'syslog', 'dmesg'] sources=[] fields=['host', 'instance_id', 'cpu_type', 'columns.cpu_brand', 'columns.feature', 'columns.value', 'instanceType', 'imageId', 'tags{}', '_raw']
- Rounds worked: 4/5  (iterations: 19, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 "i-0920036c8ca91e501" | stats count by sourcetype, source
- index=botsv3 sourcetype=aws:description "i-0920036c8ca91e501" | stats count by source
- index=botsv3 sourcetype=aws:description source="us-west-1:ec2_instances" "WebServers" | stats count by id, instance_type, host
- index=botsv3 sourcetype=cpu | stats count by host
- index=botsv3 sourcetype=dmesg | stats count by host
- index=botsv3 sourcetype=hardware | stats count by host, cpu_type
- index=botsv3 sourcetype=osquery:results columns.cpu_brand=* | stats count by host, columns.cpu_brand
- index=botsv3 sourcetype=osquery:results columns.cpu_brand=* | stats count by name, host
- index=botsv3 sourcetype=osquery:results columns.feature="product_name" | stats count by host, columns.value
- index=botsv3 sourcetype=osquery:results host="gacrux.i-0920036c8ca91e501" | stats count by name, source
- index=botsv3 sourcetype=top | stats count by host
