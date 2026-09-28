# s2 - Q318 - Round 3
_stamped by runner: rounds_remaining=2 novel_spl=9_
**Scope:** sourcetype=aws:elb:accesslogs fields=client_ip, request, action, elb_status_code, user_agent (RETRY: ELB-side rival 35.182.246.222); GuardDuty/apache_error already exhausted in R2
**Insight:** partial
**Candidate:** Canada   **Confidence:** 78

## Prior rounds
- R1: GuardDuty field manifest showed 1 event — China/Beijing port probe on web instance i-0cc93bade2b3cba63; apache_error sample 3 startup notices. Submitted China (55).
- R2: complete GuardDuty event read — Recon:EC2/PortProbeUnprotectedPort (PORT_PROBE, SSH 22, 122.112.243.11, threatName "Scanner"); apache_error fully enumerated (63 events, zero auth/password/denied). Withdrew China; scope-exhaustive negative.
- R3: RETRY sent me to the ELB-side rival; country now established in-dataset.

## This round
### What I ran
- get_sourcetype_fields aws:elb:accesslogs -> 2051 events, client_ip (15 distinct), scripted UA "__main__/0.2" present.
- `client_ip="35.182.246.222" | iplocation client_ip | stats count by Country, City` -> **Canada, Toronto, 197 events** (single row).
- `request="*member.php*" | stats count by client_ip` -> 10 clients; 35.182.246.222 (51) top; rivals 12.196.122.127 (17), 45.62.48.155 (10).
- 35.182.246.222 member.php by action/status -> login 11, lostpw 11, register 11, profile 18 — all 200.
- Rivals' member.php by action -> 12.196.122.127: register 6/profile 3/emailuser 1; 45.62.48.155: profile 9/register 1 — **no login, no lostpw**.
- 35.182.246.222 by user_agent -> "__main__/0.2" x197 (sole UA, scripted Python).
- rex method from request -> **all GETs** (help 11, lastpost 28, login 11, lostpw 11, profile 18, register 11).
- min/max _time by action -> login span ~655s; overall 1534770685→1534771609 (~924s = 15.4 min; 197 requests ≈ 1 per 4.7s).

### What it means
The country is established from in-dataset evidence: iplocation on 35.182.246.222 returns Canada for all 197 of its ELB events. Selection is data-backed: of 10 member.php clients, it is the only one with login (11) and lostpw (11) actions — the credential-attack signature — executed by a scripted agent with uniform 11/11/11 counts over ~15 minutes. That is the closest supported fit to "small brute force or password spray" once GuardDuty (recon only) and apache_error (no auth telemetry) are ruled out. NAMED GAP, per the RETRY instruction: all its requests are GETs — the feed shows repeated login-form/lostpw/register fetches, not POSTed credentials, and no failed-auth telemetry exists anywhere I searched. Country and IP are data-backed; the credential-submission act is inferred from the pattern, not directly recorded.

## Ruled out
- GuardDuty China finding — recon port probe only (R2).
- apache_error — no authentication telemetry (R2).
- 12.196.122.127, 45.62.48.155 — member.php clients with zero login/lostpw actions.
- 153.197.134.1 — single luci CGI probe (R2).

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- selection premise not filed: you already have an open selection premise p5 - amend or settle that one. The text you sent was discarded: "35.182.246.222 is the attacking source IP on the Frothly web tier, not any other"
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p6 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word


## What I'd tell my replacement
- Retired because: retired: SH stamped one of its verifications false
- Scope I owned: sourcetypes=['aws:cloudwatch:guardduty', 'apache_error'] sources=[] fields=['type', 'service.action.networkConnectionAction.remoteIpDetails.country.countryName', 'service.action.networkConnectionAction.remoteIpDetails.ipAddressV4', 'severity', 'title', 'description', 'clientip', 'src_ip', 'message', 'status', 'uri_path', 'user', 'host']
- Rounds worked: 3/5  (iterations: 33, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=apache_error | rex field=_raw "\[(?<level>notice|warn|error)\]" | stats count by level
- index=botsv3 sourcetype=apache_error | rex field=_raw "\[client (?<client>\d+\.\d+\.\d+\.\d+)\]" | stats count by client
- index=botsv3 sourcetype=apache_error | rex field=_raw "\[error\] \[client (?<client>\d+\.\d+\.\d+\.\d+)\] (?<msg>.*)" | stats count by msg
- index=botsv3 sourcetype=aws:elb:accesslogs (client_ip="12.196.122.127" OR client_ip="45.62.48.155") request="*member.php*" | stats count by client_ip, action, elb_status_code
- index=botsv3 sourcetype=aws:elb:accesslogs client_ip="35.182.246.222" request="*member.php*" | stats count by action, elb_status_code
- index=botsv3 sourcetype=aws:elb:accesslogs client_ip="35.182.246.222" | iplocation client_ip | stats count by Country, City
- index=botsv3 sourcetype=aws:elb:accesslogs client_ip="35.182.246.222" | rex field=request "^(?<method>[A-Z]+) " | stats count by method, action
- index=botsv3 sourcetype=aws:elb:accesslogs client_ip="35.182.246.222" | stats count by user_agent
- index=botsv3 sourcetype=aws:elb:accesslogs client_ip="35.182.246.222" | stats count by user_agent, request_method
- index=botsv3 sourcetype=aws:elb:accesslogs client_ip="35.182.246.222" | stats count, min(_time) AS first, max(_time) AS last by action
- index=botsv3 sourcetype=aws:elb:accesslogs client_ip="35.182.246.222" | stats count, min(_time) AS first, max(_time) AS last, (max(_time)-min(_time)) AS duration_secs by action
- index=botsv3 sourcetype=aws:elb:accesslogs request="*member.php*" | stats count by client_ip
