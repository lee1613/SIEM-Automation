# s2 - Q318 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=0_
**Scope:** sourcetype=aws:cloudwatch:guardduty | source=lambda:guardduty:us-west-1 | fields=detail.service.action.portProbeAction.portProbeDetails{}.remoteIpDetails.country.countryName; plus apache_error, aws:cloudwatchlogs, aws:cloudwatch, errors checked for hidden GuardDuty paths
**Insight:** FOUND
**Candidate:** China   **Confidence:** 55

## Prior rounds
- None — first round on this scope (GuardDuty / web-server error telemetry deviation).

## This round
### What I ran
- get_source_types -> 102 sourcetypes; aws:cloudwatch:guardduty and apache_error confirmed present.
- search_keyword "brute" -> 0 events; no field or value named brute anywhere in the index.
- get_sourcetype_fields aws:cloudwatch:guardduty -> field manifest of the sourcetype's single event (103 field rows, 51 returned): category Recon, action PORT_PROBE, port 22/SSH, against instance i-0cc93bade2b3cba63 (WebServers ASG, production-FrothlyWebPubSecGroup, public IP 54.183.247.244), createdAt 2018-08-20T14:01:29Z, remoteIpDetails city=Beijing, country=China.
- get_sources aws:cloudwatch:guardduty -> exactly 1 event, source lambda:guardduty:us-west-1.
- sample_events apache_error -> 3 events, all Apache/2.2.34 startup notices (Jul 26).
- get_sources on aws:cloudwatchlogs / aws:cloudwatch / errors -> lambda:DNS only; CloudWatch metrics only; /var/log/amazon/ssm/errors.log only.

### What it means
GuardDuty contains exactly one finding against the Frothly web tier, and it is country-tagged: remoteIpDetails.country.countryName = "China" (city Beijing). Apache error telemetry contains nothing. So the only country recorded against the Frothly web servers anywhere in the dataset is China, recorded verbatim — matching SH's "identify the attacking source IP or detection, and return the country it originates from exactly as recorded". Caveat carried in the confidence: the finding is a Recon port probe (SSH 22), not a labeled brute force or password spray; no feed in scope labels any credential attack against the web servers. The rival 35.182.246.222 lead has no in-dataset country record (Canada is untested external knowledge, open premise p3) and its brute-force act was never established (p2 open).

## Ruled out
- apache_error — 3 events, all startup notices; no auth failures or attack errors.
- aws:cloudwatchlogs / aws:cloudwatch / errors — DNS logs, CloudWatch metrics, SSM agent errors; no GuardDuty findings, no web telemetry.
- GuardDuty as a labeled brute-force source — its only finding is PORT_PROBE (Recon), not a credential attack; no SSHBruteForce-type finding exists.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p4 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "aws:cloudwatch:guardduty"}` (51 of 103 rows seen). A claim resting on them alone is UNVERIFIED._
