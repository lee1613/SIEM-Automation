# s2 - Q202 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Scope:** sourcetype=hardware, osquery:results, aws:description, dmesg | fields: cpu_type, host, columns.feature, columns.value, id, instance_type, image_id
**Insight:** partial (round cap hit)   **Candidate:** E5-2676 v3   **Confidence:** 70

## Prior rounds
- None — first round. Inherited: p1 REFUTED (CPU evidence not limited to hardware.cpu_type / osquery cpu_brand; cpuid product_name exists); web-server set = gacrux fleet in WebServers ASG incl. i-0920036c8ca91e501; hoth ruled out as internal SuiteCRM server.

## This round
### What I ran
- `sourcetype=osquery:results columns.feature="product_name" | stats count by host, columns.value` -> 1 event: hoth only, "AMD FX(tm)-8120 Eight-Core Processor" (hoth = ruled-out internal box).
- `sourcetype=aws:description "i-0920036c8ca91e501" | stats count by source` -> 4 sources; raw ec2_instances event read: t2.medium, AMI amzn-ami-hvm-2018.03.0.20180622-x86_64-gp2, hypervisor xen, ASG WebServers — no CPU-model string.
- `sourcetype=hardware | stats count by host, cpu_type` -> 3 rows (complete), all gacrux: "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz".
- `sourcetype=aws:description source="us-west-1:ec2_instances" "WebServers" | stats count by id, instance_type` -> 8 rows (complete), all t2.medium.
- `sourcetype=dmesg | stats count by host` -> only the same 3 gacrux hosts; no i-0920036c8ca91e501 coverage.

### What it means
Direct CPU-model evidence covers 3 of 8 web servers: Intel Xeon E5-2676 v3 @ 2.40GHz → processor number **E5-2676 v3**. i-0920036c8ca91e501 has osquery coverage (47,098 events, host=gacrux.i-0920036c8ca91e501) but no product_name row; its aws:description record ties it to t2.medium, the same instance type as the three CPU-confirmed members — instance-type corroboration, not ASG/AMI imputation, but still not direct CPU proof on that host. Cap hit before searching sourcetype=cpu, osquery cpu_brand per host, and cloud-init/bootstrap.

## Ruled out
- aws:description as a CPU-model source — instance metadata carries type/AMI/hypervisor, no CPU string.
- dmesg — covers only the 3 hardware-covered gacrux hosts.
- osquery:results cpuid product_name — hoth only.
- hoth's AMD FX-8120 as the web-server CPU — hoth is not a web server.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "osquery:results"}` (38 of 153 rows seen). A claim resting on them alone is UNVERIFIED._
