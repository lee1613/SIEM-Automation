# s2 - Q318 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=3_
**Scope:** sourcetype=aws:cloudwatch:guardduty source=lambda:guardduty:us-west-1 fields=detail.type, detail.service.action, detail.service.action.portProbeAction.portProbeDetails{}.remoteIpDetails.country.countryName, detail.resource.instanceDetails.instanceId, detail.resource.instanceDetails.tags.value; plus sourcetype=apache_error source=/var/log/httpd/error_log fields=client, message
**Insight:** partial — scope exhausted, no qualifying record
**Candidate:** none   **Confidence:** 90

## Prior rounds
- R1: GuardDuty field manifest showed 1 event — a China/Beijing port probe on web instance i-0cc93bade2b3cba63; apache_error sample showed 3 startup notices; alternate GuardDuty paths (aws:cloudwatchlogs/aws:cloudwatch/errors) held no findings. Submitted China, confidence 55.
- SH feedback: China attached only to recon; RETRY ordered — read the complete event, then decide whether any scope record shows brute force/password spray.

## This round
### What I ran
- get_raw_events aws:cloudwatch:guardduty -> the single event's complete raw JSON, read in full.
- get_sourcetype_fields apache_error -> 63 events (R1's 3-event sample was partial), 3 gacrux hosts incl. i-0cc93bade2b3cba63 (11).
- get_raw_events apache_error keyword=auth / password / denied -> 0 / 0 / 0 events.
- get_raw_events apache_error (first 20) -> Apache startup notices + favicon.ico 404s from client 172.16.0.149.
- `index=botsv3 sourcetype=apache_error | rex "\[(?<level>notice|warn|error)\]" | stats count by level` -> error 40, notice 14, warn 9 (sums to 63).
- `... | rex "\[error\] \[client (?<client>...)\] (?<msg>.*)" | stats count by msg` -> favicon.ico 24 + 14 (with referer), robots.txt 1, luci CGI 1 (sums to 40).
- `... | stats count by client` -> 172.16.0.149 (39), 153.197.134.1 (1).

### What it means
No GuardDuty or apache_error record shows brute-force/password-spray behavior against the web servers. The complete GuardDuty event is type Recon:EC2/PortProbeUnprotectedPort: actionType PORT_PROBE, localPort 22/SSH, remoteIpDetails 122.112.243.11 (China Telecom Shanghai, ASN 4812), country.countryName "China", city "Beijing", threatName "Scanner" (ProofPoint), severity 2, count 1, eventFirstSeen/LastSeen 2018-08-20T13:50:05Z/13:51:04Z, target i-0cc93bade2b3cba63 (WebServers ASG, production-FrothlyWebPubSecGroup, public IP 54.183.247.244). A 59-second port probe by a listed scanner — the China value belongs only to recon, not to a brute force or password spray. apache_error carries no authentication telemetry at all: all 40 [error] events are missing-file 404s plus one /var/www/cgi-bin/luci CGI probe; 14 notices and 9 warns are startup/module messages; auth/password/denied match zero events; the only clients are internal 172.16.0.149 (39) and 153.197.134.1 (one luci probe — single request, no repetition, no credential context). The question's act is therefore not recorded in this scope; the country must come from the feed recording the credential attempts themselves — the web access logs, via iplocation on the attacking client IP (s1's open lead 35.182.246.222, country still untested).

## Ruled out
- GuardDuty as brute-force evidence — its only finding is Recon:EC2/PortProbeUnprotectedPort (PORT_PROBE, SSH 22, threatName "Scanner"), not a credential attack.
- apache_error as brute-force evidence — all 63 events enumerated: 404s, startup notices, module warns; zero auth/password/denied events.
- 153.197.134.1 (apache_error's only external client) — one luci CGI probe, count 1, no repetition or auth context.
- China as the answer — attached only to the recon port probe; withdrawn per SH's q6/q8 rulings.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p4 - amend or settle that one. The text you sent was discarded: "The brute-force/password-spray act and its country are NOT recorded in GuardDuty"
- p5 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p6 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
