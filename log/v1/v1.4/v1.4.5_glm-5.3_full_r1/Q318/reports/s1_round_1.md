# s1 - Q318 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=4_
**Scope:** sourcetype=access_combined, aws:elb:accesslogs, stream:http | source=/var/log/httpd/access_log, /var/log/apache2/access.log, s3://frothlyweblogs (ELB) | fields client_ip, clientip, request, action, form_data, elb_status_code
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 35

## Prior rounds
- Round 1 (this round): mapped all web-tier feeds; found 35.182.246.222 as the only repeated-login source; no country lookup run yet.

## This round
### What I ran
- get_source_types; get_sources(access_combined) → /var/log/httpd/access_log (3,667 ev, brewertalk.com MyBB on 4 gacrux hosts behind FrothlyWebLB) + /var/log/apache2/access.log (240 ev, SuiteCRM on hoth, internal clients only)
- ELB `request="*member.php*" | stats count by client_ip, action, elb_status_code` (15 rows) → 35.182.246.222: login=11, lostpw=11, register=11, profile=18; 45.62.48.155: profile=9; 12.196.122.127: register=6; 91.207.175.249: profile=2
- ELB `client_ip="35.182.246.222" request="*member.php*"` timeline (50 of 51 rows) → scripted GETs at 6-10s intervals, 13:11-13:25Z, all status 200
- stream:http `http_method=POST url="*member.php*"` form_data (16 rows) → do_login only 4: 62.251.109.73 (bootyman x2), 107.77.75.123 (fyodor, empty pw), 157.97.121.69 (empty) — single attempts, no spray

### What it means
NOT_FOUND. The only repeated-login source on the web tier is 35.182.246.222 (11 attempts — fits "small"), but its records are login-page GETs with no visible credential submissions, so the brute-force act is not positively shown, and no geolocation was run — no country value can be submitted. Next round: `| iplocation client_ip` on the ELB feed; tie the "__main__/0.2" Python UA (197 ELB events) to its client_ip; identify the 68 ELB 460-status / 64 request_processing_time=-1 clients; check apache_error and GuardDuty.

## Ruled out
- /var/log/apache2/access.log (SuiteCRM, hoth) — internal 192.168.8.x clients only; 14 Login page hits; no external brute force
- stream:http do_login POSTs — 4 single attempts across 3 IPs; no repeated-credential pattern
- httpd access_log clientip — ELB private IPs (172.16.0.149/172.16.1.239) mask true clients
- 91.207.175.249 (841 ELB events, top external client) — zero login actions; scanning/exploit volume, not auth attempts
- 12.196.122.127 — forum account registrations (Trojaan/Bootyman), no logins

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=aws:elb:accesslogs client_ip="35.182.246.222" request="*member.php…` (50 of 51 rows seen). A claim resting on them alone is UNVERIFIED._
