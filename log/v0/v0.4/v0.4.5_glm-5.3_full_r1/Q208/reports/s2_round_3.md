# s2 - Q208 - Round 3
_stamped by runner: rounds_remaining=0 novel_spl=7_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BSTOLL-L EventCode=1 _time>=1534772000 | stats count min(_time) as first_t values(ProcessGuid) as guid values(ParentImage) as parent values(ParentProcessId) as ppid values(User) as user values(CommandLine) as cmdline by Image ProcessId | sort first_t
- index=botsv3 sourcetype="PerfmonMk:Process" ID_Process=3400 _time>=1534772230 _time<=1534772345 | stats count values(process_name) as instance values(eval(round('%_Processor_Time',2))) as pct_processor by _time | sort _time
- index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BSTOLL-L ProcessId=3400 | stats count min(_time) as first_t max(_time) as last_t values(EventCode) as eventcodes values(Image) as images values(CommandLine) as cmdlines values(ParentImage) as parents values(DestinationIp) as dest_ips values(DestinationHostname) as dest_hosts values(DestinationPort) as dest_ports
- index=botsv3 sourcetype="PerfmonMk:Process" | stats count(eval('%_Processor_Time'=100)) as n100 max(eval('%_Processor_Time')) as maxcpu count as samples by process_name | where n100>0 OR maxcpu>99.9 | sort -n100
### What it means
Intention: The rename is confirmed — PID 3400 was recorded as "chrome#5" when it FIRST hit 100% (17:37:50), then as "chrome#4" for the sustained run. Now I must (a) verify no other instances (Idle/_Total, or events missing process_name) reached 100% — resolving the fieldsummary 1588-vs-134 discrepancy, (b) characterize the MicrosoftEdgeCP#2 spike at 13:36 to rule it in/out of the mining activity, and (c) check the `ps` feed for rival mining endpoints. Batching independent queries:

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" host=BSTOLL-…` (25 of 416 rows seen). A claim resting on them alone is UNVERIFIED._
