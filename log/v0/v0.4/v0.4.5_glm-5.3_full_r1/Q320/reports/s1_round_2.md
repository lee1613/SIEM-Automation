# s1 - Q320 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=5_
**Scope:** sourcetype=stream:http, syslog | source=/var/log/auth.log | fields=form_data, _raw, host, src_ip, uri_path
**Insight:** FOUND
**Candidate:** davidverve.com   **Confidence:** 90

## Prior rounds
- Round 1: osquery:results (0 "useradd" events feed-wide) and Unix:UserAccounts (hoth absent, gacrux-only) ruled out; candidate ilovedavidverve carried unverified.

## This round
### What I ran
- get_sources bash_history -> klagerfield + ec2-user; get_raw_events "useradd" bash_history -> 0 events.
- `sourcetype=linux_secure "useradd"` -> 24 events, all Aug 20 bootstrap package users (ec2-user, apache, memcached, streamfwd) on gacrux hosts, no passwords.
- hoth osquery shell_history ("passwd"/"adduser"/"chpasswd") -> 4 benign audit/splunk commands.
- `sourcetype=stream:http "useradd"` -> 1 event: POST /frothlyinventory/integration/saveGangster.action, hoth, src 192.168.8.103.
- get_raw_events -> Struts2 OGNL RCE, `#cmd='useradd -ou 0 -g 0 -M -N -r -s /bin/bash  tomcat7 -p davidverve.com'`, 2018-08-20T19:07:04+08:00, status 200.
- `sourcetype=stream:http "tomcat7"` -> only that 1 event (no later password change).
- hoth auth.log (tomcat7/useradd/new user/passwd/chpasswd) -> 1 event: "Aug 20 11:24:44 hoth useradd[12815]: new user: name=tomcat7, UID=0, GID=0, home=/home/tomcat7, shell=/bin/bash".

### What it means
FOUND. The user-creation act on hoth is the Struts2 RCE POST whose command line literally carries `-p davidverve.com`; hoth's auth.log confirms the account was created (tomcat7, UID=0). No passwd/chpasswd follows in auth.log or the HTTP stream, so the recorded password is **davidverve.com**. This refutes the premise value ilovedavidverve — the actual command text reads `-p davidverve.com`.

## Ruled out
- bash_history (both sources) - 0 events contain useradd.
- linux_secure useradd events - benign gacrux bootstrap installs, not hoth, no password recorded.
- hoth osquery shell_history - only benign audit/splunk commands.
- ilovedavidverve (premise p2) - contradicted by the literal command `-p davidverve.com`.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p3 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
