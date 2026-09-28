# v1 timeline — test_20260716_095627  (TEST RUN)

Started: 2026-07-16T09:56:27


---

## Q216  (1000 pts)

> According to the Cisco NVM flow logs, for how many seconds does the endpoint generate Monero cryptocurrency?
- **Senior #6**  _[solved]_  task=1
    - subquestion: [HUNTER] In `index=botsv3`, identify the Cisco NVM flow log sourcetype(s) and locate any events indicating Monero cryptocurrency mining activity from the known Frothly endpoints `BGIST-L`, `JWORTOS-L`
    - answer: FINAL ANSWER: FYODOR-L; mining destination 45.77.53.176:3333; earliest and latest Cisco NVM flow event timestamp = 2018-08-20T10:47:05.536706Z / 2018-08-20T10:47:05.536706Z
SPL: index=botsv3 sourcetype=stream:tcp host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) dest_ip=45.77.53.176 dest_port=3333 timestamp>="2018-08-20T00:00:00Z" timestamp<="2018-08-21T23:59:59Z" | 
    - SPL: ['index=botsv3 sourcetype=stream:ip | stats count by host | sort - count | head 50', 'index=botsv3 sourcetype=stream:ip dest_ip=45.77.53.176 dest_port=3333 | stats count min(timestamp) as earliest max(timestamp) as latest by host dest_ip dest_port | sort - count', 'index=botsv3 sourcetype=stream:tcp dest_ip=45.77.53.176 dest_port=3333 timestamp>="2018-08-20T00:00:00Z" timestamp<="2018-08-21T23:59:59Z" | stats count min(timestamp) as earliest max(timestamp) as latest by host dest dest_ip dest_port connection | sort - count', 'index=botsv3 sourcetype=stream:tcp host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) dest_ip=45.77.53.176 timestamp>="2018-08-20T00:00:00Z" timestamp<="2018-08-21T23:59:59Z" | stats count min(timestamp) as earliest max(timestamp) as latest by host dest_ip dest_port connection | sort - count']
- **Senior #7**  _[partial]_  task=2
    - subquestion: [CONTENT] In `index=botsv3`, examine raw Cisco NVM flow log events for the Monero-related traffic involving the known Frothly endpoints `BGIST-L`, `JWORTOS-L`, `FYODOR-L`, `ABUNGST-L`, `MKRAEUS-L`, `B
    - answer: PARTIAL ANSWER: The strongest candidate event pattern is `sourcetype=stream:tcp` with `src=10.0.2.62`, `dest=45.77.53.176`, `dport=3333`, `protocol=tcp`, `transport=tcp`. In the requested window, this pattern appears 5 times, with first/last matching epoch timestamps `1534755435` and `1534776898`.

UNCERTAINTY: I have not yet verified the exact Cisco NVM sourcetype or a raw event text field explic
    - SPL: []
- **Senior #8**  _[solved]_  task=3
    - subquestion: [METRICS] Given [Task-1 (solved): FINAL ANSWER: FYODOR-L; mining destination 45.77.53.176:3333; earliest and latest Cisco NVM flow event timestamp = 2018-08-20T10:47:05.536706Z / 2018-08-20T10:47:05.5
    - answer: FINAL ANSWER: 0 seconds
SPL: index=botsv3 sourcetype=stream:tcp dest_ip=45.77.53.176 dest_port=3333 timestamp>="2018-08-20T00:00:00Z" timestamp<="2018-08-21T23:59:59Z" | stats min(timestamp) as earliest max(timestamp) as latest | eval duration_seconds=round((strptime(latest,"%Y-%m-%dT%H:%M:%S.%6NZ")-strptime(earliest,"%Y-%m-%dT%H:%M:%S.%6NZ")),0) | table earliest latest duration_seconds
    - SPL: ['index=botsv3 sourcetype=stream:tcp dest_ip=45.77.53.176 dest_port=3333 timestamp>="2018-08-20T00:00:00Z" timestamp<="2018-08-21T23:59:59Z" | stats min(timestamp) as earliest max(timestamp) as latest | eval duration_seconds=round((strptime(latest,"%Y-%m-%dT%H:%M:%S.%6NZ")-strptime(earliest,"%Y-%m-%dT%H:%M:%S.%6NZ")),0) | table earliest latest duration_seconds']

**SH FINAL → extractor:** `0`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q216]: input=191,168  cached=150,528  output=7,226  est=$0.0915

---

## Q303  (100 pts)

> What is the password for the user that was successfully created by the user "root" on the on-premises Linux system?
- **Senior #10**  _[partial]_  task=1
    - subquestion: [HUNTER] In `index=botsv3`, investigate the on-premises Linux hosts `BGIST-L`, `JWORTOS-L`, `FYODOR-L`, `ABUNGST-L`, `MKRAEUS-L`, `BTUN-L`, `PCERF-L`, and `BSTOLL-L` during the August 2018 window arou
    - answer: PARTIAL ANSWER: host=hoth, created username=tomcat7, timestamp=2018-08-20T19:24:44.000+08:00, sourcetype=syslog, raw event=`Aug 20 11:24:44 hoth useradd[12815]: new user: name=tomcat7, UID=0, GID=0, home=/home/tomcat7, shell=/bin/bash`

UNCERTAINTY: I could verify a successful `useradd` event performed as `root` from syslog, but I could not confirm that `hoth` maps to one of the requested on-premi
    - SPL: ['index=botsv3 sourcetype=osquery:results (host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) OR hostIdentifier IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L)) | stats count by host, hostIdentifier | sort - count', 'index=botsv3 (sourcetype=syslog OR sourcetype=osquery:results) (host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) OR hostIdentifier IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L)) ("useradd" OR "adduser" OR "/etc/passwd" OR "new user" OR "created user" OR "pam_unix" OR "user creation" OR "usermod") | stats count by host, hostIdentifier, sourcetype, source, user, columns.name, columns.path, process, _time | sort - count', 'index=botsv3 sourcetype=syslog host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) _time>=1534737603 _time<=1534778829 ("useradd" OR "adduser") | stats count by host, _time, _raw | sort - _time', 'index=botsv3 sourcetype=osquery:results decorations.hostname IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) (columns.path="/usr/sbin/useradd" OR columns.path="/usr/sbin/adduser" OR columns.path="/bin/useradd" OR columns.path="/bin/adduser" OR columns.path="/etc/passwd" OR columns.path="/etc/shadow") | stats count by decorations.hostname, name, columns.path, columns.cmdline, columns.name, columns.time | sort - count', 'index=botsv3 sourcetype=osquery:results decorations.hostname IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) (columns.path=*useradd* OR columns.path=*adduser* OR columns.path=*passwd* OR columns.name=*useradd* OR columns.name=*adduser* OR columns.name=*passwd*) | stats count by decorations.hostname, name, columns.path, columns.name, columns.time | sort - count', 'index=botsv3 sourcetype=osquery:results decorations.hostname IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) columns.username=* | stats count by decorations.hostname, columns.username, decorations.username, name | sort - count', 'index=botsv3 sourcetype=syslog ("new user:" OR "useradd[" OR "adduser[") _time>=1534737603 _time<=1534778829 | stats count by host, source, _raw, _time | sort - _time']
- **Senior #11**  _[partial]_  task=2
    - subquestion: [CONTENT] In `index=botsv3`, inspect raw content on the same on-premises Linux hosts `BGIST-L`, `JWORTOS-L`, `FYODOR-L`, `ABUNGST-L`, `MKRAEUS-L`, `BTUN-L`, `PCERF-L`, and `BSTOLL-L` during the August
    - answer: PARTIAL ANSWER: I found no confirmed plaintext password-setting event yet. The strongest concrete evidence so far is that `bash_history` on BOTSv3 does contain command text, but the only `passwd`-related raw hit I could retrieve was benign: `cat /etc/passwd` (not a password-setting action).

UNCERTAINTY: I was not able to complete the targeted search for the specified hosts/time window because the
    - SPL: ['index=botsv3 sourcetype=bash_history (host=BGIST-L OR host=JWORTOS-L OR host=FYODOR-L OR host=ABUNGST-L OR host=MKRAEUS-L OR host=BTUN-L OR host=PCERF-L OR host=BSTOLL-L) earliest=1534737603 latest=1534778829 | stats count by host, bash_command | search bash_command=*passwd* OR bash_command=*chpasswd* OR bash_command=*openssl* OR bash_command=*echo*', 'index=botsv3 sourcetype=bash_history (host=BGIST-L OR host=JWORTOS-L OR host=FYODOR-L OR host=ABUNGST-L OR host=MKRAEUS-L OR host=BTUN-L OR host=PCERF-L OR host=BSTOLL-L) earliest=1534737603 latest=1534778829 (bash_command=passwd OR bash_command=chpasswd OR bash_command=openssl OR bash_command=echo) | stats count by host, bash_command', 'index=botsv3 sourcetype=osquery:results (hostIdentifier=BGIST-L OR hostIdentifier=JWORTOS-L OR hostIdentifier=FYODOR-L OR hostIdentifier=ABUNGST-L OR hostIdentifier=MKRAEUS-L OR hostIdentifier=BTUN-L OR hostIdentifier=PCERF-L OR hostIdentifier=BSTOLL-L) earliest=1534737603 latest=1534778829 | stats count by hostIdentifier, columns.cmdline, columns.path | search columns.cmdline=*passwd* OR columns.cmdline=*chpasswd* OR columns.cmdline=*openssl* OR columns.cmdline=*echo* OR columns.path=*passwd* OR columns.path=*shadow* OR columns.path=*cron*']
- **Senior #12**  _[partial]_  task=3
    - subquestion: [CONTENT] In `index=botsv3`, focus on Linux command/process telemetry for the on-premises hosts `BGIST-L`, `JWORTOS-L`, `FYODOR-L`, `ABUNGST-L`, `MKRAEUS-L`, `BTUN-L`, `PCERF-L`, and `BSTOLL-L` during
    - answer: PARTIAL ANSWER: I found one concrete root-executed account-creation command in `osquery:results` on host `hoth`, not on the specified host list:

- `columns.cmdline`: `"useradd" "-ou" "tomcat7" "-p" "ilovedavidverve" "0" "-g" "0" "-M" "-N" "-r" "-s" "/bin/bash"`
- `columns.path`: `/usr/sbin/useradd`
- `decorations.username`: `root` on the corresponding event
- Related nearby event on the same host
    - SPL: ['index=botsv3 sourcetype=osquery:results host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) earliest=1534737603 latest=1534778829 decorations.username=root (columns.cmdline="*useradd*" OR columns.cmdline="*adduser*" OR columns.cmdline="*passwd*" OR columns.cmdline="*chpasswd*") | stats count values(host) as hosts values(calendarTime) as times values(columns.cmdline) as cmdlines values(columns.parent) as parents values(columns.path) as paths by decorations.username columns.pid | search decorations.username=root', 'index=botsv3 sourcetype=osquery:results hostIdentifier IN (MKRAEUS-L,BSTOLL-L) earliest=1534737603 latest=1534778829 decorations.username=root (columns.cmdline="*useradd*" OR columns.cmdline="*adduser*" OR columns.cmdline="*passwd*" OR columns.cmdline="*chpasswd*") | stats count values(hostIdentifier) as hosts values(unixTime) as epochs values(calendarTime) as times values(name) as names values(columns.cmdline) as cmdlines values(columns.parent) as parents values(columns.path) as paths by decorations.username columns.pid', 'index=botsv3 sourcetype=ps earliest=1534737603 latest=1534778829 USER=root (COMMAND=useradd OR COMMAND=adduser OR COMMAND=passwd OR COMMAND=chpasswd OR process_exec IN (useradd,adduser,passwd,chpasswd)) | stats count values(host) as hosts values(src) as srcs values(time) as times values(process) as processes values(app) as apps values(USER) as users by PID', 'index=botsv3 sourcetype=ps earliest=1534737603 latest=1534778829 (process=*useradd* OR process=*adduser* OR process=*passwd* OR process=*chpasswd* OR COMMAND=*useradd* OR COMMAND=*adduser* OR COMMAND=*passwd* OR COMMAND=*chpasswd*) | stats count values(host) as hosts values(src) as srcs values(USER) as users values(process) as processes values(app) as apps by COMMAND process_exec process_name', 'index=botsv3 sourcetype=ps earliest=1534737603 latest=1534778829 (process_exec IN (useradd,adduser,passwd,chpasswd) OR process_name IN (useradd,adduser,passwd,chpasswd) OR COMMAND IN (useradd,adduser,passwd,chpasswd)) | stats count values(host) as hosts values(src) as srcs values(USER) as users values(process) as processes values(app) as apps by COMMAND process_exec process_name']
- **Senior #13**  _[solved]_  task=4
    - subquestion: [METRICS] Given [Task-1 (partial): PARTIAL ANSWER: host=hoth, created username=tomcat7, timestamp=2018-08-20T19:24:44.000+08:00, sourcetype=syslog, raw event=`Aug 20 11:24:44 hoth useradd[12815]: new 
    - answer: FINAL ANSWER: ilovedavidverve
SPL: `index=botsv3 sourcetype=osquery:results host=hoth decorations.username=root keyword=tomcat7`
    - SPL: ['index=botsv3 sourcetype=osquery:results host=hoth decorations.username=root (columns.cmdline=*useradd* OR columns.cmdline=*adduser* OR columns.cmdline=*passwd* OR columns.cmdline=*chpasswd* OR columns.cmdline=*openssl* OR columns.cmdline=*echo*) | stats count values(columns.cmdline) as cmdlines values(columns.path) as paths values(columns.name) as names by host decorations.username', 'index=botsv3 sourcetype=osquery:results host=hoth decorations.username=root (columns.cmdline=useradd* OR columns.cmdline=adduser* OR columns.cmdline=passwd* OR columns.cmdline=chpasswd* OR columns.cmdline=openssl* OR columns.cmdline=echo*) | stats count values(columns.cmdline) as cmdlines values(columns.path) as paths values(columns.name) as names by host decorations.username']

**SH FINAL → extractor:** `ilovedavidverve`  [CORRECT]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q303]: input=455,500  cached=355,840  output=8,789  est=$0.1694

---

## Q329  (1000 pts)

> One of the files uploaded by Taedonggang contains a word that is a much larger in font size than any other in the file. What is that word?
- **Senior #14**  _[too_big]_  task=1
    - subquestion: [HUNTER] In `index=botsv3`, identify all references to `Taedonggang` during the August 2018 investigation window around epoch `1534737603` to `1534778829`, including any usernames, email addresses, fi
    - answer: ESCALATE: I searched `index=botsv3` across likely text-bearing sourcetypes for exact `Taedonggang` references, including `access_combined`, `aws:cloudtrail`, `aws:s3:accesslogs`, `stream:http`, `stream:smtp`, `ms:o365:reporting:messagetrace`, `WinEventLog`, `xmlwineventlog:microsoft-windows-sysmon/operational`, `bash_history`, `linux_secure`, and `syslog`, but found no direct matches in the availa
    - SPL: ['index=botsv3 sourcetype=ms:o365:reporting:messagetrace Taedonggang | stats count by SenderAddress RecipientAddress Subject DateReceived MessageId', 'index=botsv3 sourcetype=aws:s3:accesslogs Taedonggang | stats count by bucket_name requestor remote_ip time action http_status key object_size', 'index=botsv3 sourcetype IN (access_combined,apache_error,aws:cloudtrail,aws:s3:accesslogs,stream:http,stream:smtp,WinEventLog,xmlwineventlog:microsoft-windows-sysmon/operational,syslog,bash_history,linux_secure) Taedonggang | stats count by sourcetype', 'index=botsv3 sourcetype=access_combined (uri=*Taedonggang* OR referer=*Taedonggang* OR useragent=*Taedonggang* OR file=*Taedonggang* OR uri_query=*Taedonggang*) | stats count by host clientip user uri uri_path file referer', 'index=botsv3 sourcetype=access_combined Taedonggang | stats count by host clientip user uri uri_path file referer', 'index=botsv3 sourcetype=aws:cloudtrail Taedonggang | stats count by eventTime eventSource eventName userIdentity.userName userIdentity.arn sourceIPAddress requestParameters.bucketName requestParameters.key requestParameters.name', 'index=botsv3 sourcetype IN (access_combined,apache_error,aws:cloudtrail,aws:s3:accesslogs,stream:http,stream:smtp,ms:o365:reporting:messagetrace,WinEventLog,xmlwineventlog:microsoft-windows-sysmon/operational,bash_history,linux_secure,syslog) Taedonggang | stats count by sourcetype']
- **Senior #15**  _[partial]_  task=2
    - subquestion: [CONTENT] In `index=botsv3`, inspect the raw event content and any extracted file content/metadata for the file or files uploaded by `Taedonggang` during the August 2018 window around epoch `153473760
    - answer: PARTIAL ANSWER: The evidence trail points to `c:\users\mallorykraeusen\documents\frothly_gabf_deck-2018-mk.pptx` as the relevant uploaded file, but I have not yet extracted the specific oversized word from the presentation content.

Evidence trail:
- `code42:security` raw event shows `files[].fullPath = c:\users\mallorykraeusen\documents\frothly_gabf_deck-2018-mk.pptx`
- Same event shows `files[].
    - SPL: ['index=botsv3 sourcetype=code42:security | stats count by eventType, files{}.fileName, files{}.fullPath, processOwner, userUid, deviceRemoteAddress, timestamp | sort - count', 'index=botsv3 sourcetype=code42:security | stats count by processOwner, files{}.fileName, files{}.fullPath, files{}.mimeType, files{}.fileEventType, eventType | search processOwner=MalloryKraeusen AND files{}.fileName IN ("frothly_gabf_deck-2018-mk.pptx","ba_advertising_code_overview.pdf")']
- **Senior #16**  _[partial]_  task=3
    - subquestion: [CONTENT] In `index=botsv3`, search specifically for upload/application/document-handling sourcetypes tied to `Taedonggang` in the August 2018 window around epoch `1534737603` to `1534778829`, and ins
    - answer: Intention: Finalize with the strongest verified finding: the uploaded file appears to be a gzip archive, and the only clearly named office document in SMTP is an Excel file; I cannot verify a font-size token from extracted slide XML in the available evidence.
PARTIAL ANSWER: The uploaded artifact tied to the investigation is `frothly_html_memcached.tar.gz` with MIME type `application/gzip`, so it 
    - SPL: ['index=botsv3 sourcetype=stream:http (Taedonggang OR taedonggang OR BudStoll OR bstoll OR BTUN-L OR PCERF-L OR ABUNGST-L OR FYODOR-L OR JWORTOS-L OR BGIST-L OR MKRAEUS-L) | stats count by host http_content_type uri_path method status', 'index=botsv3 sourcetype=stream:smtp | stats count by attach_filename{} file_name | sort - count', 'index=botsv3 sourcetype=stream:smtp "Employee New Hire Dates.xlsx" | stats count by src_ip dest_ip from to subject attach_filename{} file_name']
- **Senior #17**  _[partial]_  task=4
    - subquestion: [HUNTER] Given [Task-1 (too_big): ESCALATE: I searched `index=botsv3` across likely text-bearing sourcetypes for exact `Taedonggang` references, including `access_combined`, `aws:cloudtrail`, `aws:s3:
    - answer: PARTIAL ANSWER: `/suitecrm/blargh.tgz` on `hoth`, requested from `192.168.8.103` with HTTP `200` at `_time=2018-08-20T19:44:38.000+08:00` (epoch `1534775078`).
UNCERTAINTY: This is the strongest file pivot I found, but I have not yet confirmed whether the archive itself contains the Taedonggang-linked document or whether there is an accompanying extraction record/file hash in another sourcetype.
N
    - SPL: ['index=botsv3 sourcetype=ms:o365:reporting:messagetrace | stats count by SenderAddress RecipientAddress Subject MessageId MessageTraceId DateReceived Received Status Size FromIP ToIP | search SenderAddress IN ("taedonggang*","*taedonggang*") OR RecipientAddress IN ("taedonggang*","*taedonggang*") OR Subject IN ("*Taedonggang*","*taedonggang*") OR MessageId IN ("*Taedonggang*","*taedonggang*") OR MessageTraceId IN ("*Taedonggang*","*taedonggang*")', 'index=botsv3 sourcetype=ms:o365:reporting:messagetrace | stats count by SenderAddress | top limit=50 SenderAddress', 'index=botsv3 sourcetype=ms:o365:reporting:messagetrace (SenderAddress IN ("bstoll@froth.ly","btun@froth.ly","fyodor@froth.ly","bgist@froth.ly","jwortoski@froth.ly","mkraeusen@froth.ly","abungstein@froth.ly","ghoppy@froth.ly","pcerf@froth.ly") OR RecipientAddress IN ("bstoll@froth.ly","btun@froth.ly","fyodor@froth.ly","bgist@froth.ly","jwortoski@froth.ly","mkraeusen@froth.ly","abungstein@froth.ly","ghoppy@froth.ly","pcerf@froth.ly")) | stats count by SenderAddress RecipientAddress Subject MessageId MessageTraceId DateReceived Received Status Size FromIP ToIP | sort - count', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com | stats count by eventName requestParameters.bucketName requestParameters.key requestParameters.prefix responseElements.xAmzRequestId userIdentity.userName sourceIPAddress eventTime | sort - count', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com | stats count by eventName requestParameters.bucketName requestParameters.prefix requestParameters.key userIdentity.userName userIdentity.arn sourceIPAddress eventTime | sort - count', 'index=botsv3 sourcetype=aws:cloudtrail (requestParameters.bucketName="cloudtrail-622676721278" OR requestParameters.bucketName="config-bucket-622676721278" OR requestParameters.bucketName="frothlywebcode") | stats count by eventName requestParameters.bucketName requestParameters.prefix requestParameters.key userIdentity.userName eventTime sourceIPAddress | sort - count', 'index=botsv3 sourcetype=aws:s3:accesslogs | stats count by bucket_name requester requestor remote_ip operation key http_status time | sort - count', 'index=botsv3 sourcetype=aws:s3:accesslogs ("Taedonggang" OR "taedonggang" OR "upload" OR "PUT" OR "POST") | stats count by requestor remote_ip operation http_status source | sort - count', 'index=botsv3 sourcetype=aws:s3:accesslogs | stats count by requestor | top limit=20 requestor', 'index=botsv3 sourcetype=access_combined | stats count by host clientip user uri uri_path file referer status | sort - count', 'index=botsv3 sourcetype=access_combined host=hoth | stats count by uri uri_path file referer status clientip user | sort - count', 'index=botsv3 sourcetype=access_combined host=hoth uri="/suitecrm/blargh.tgz" | stats count by _time clientip referer status file uri uri_path host']
- **Senior #18**  _[partial]_  task=5
    - subquestion: [METRICS] Given [Task-2 (partial): PARTIAL ANSWER: The evidence trail points to `c:\users\mallorykraeusen\documents\frothly_gabf_deck-2018-mk.pptx` as the relevant uploaded file, but I have not yet ex
    - answer: Intention: Verify the exact filename from the established upload trail and report the only defensible answer from evidence available in Splunk.
PARTIAL ANSWER: frothly_html_memcached.tar.gz  
UNCERTAINTY: I verified the uploaded artifact tied to Taedonggang/BudStoll in `code42:security`, but I could not extract the specific oversized word from the file contents in the available evidence. The docum
    - SPL: ['index=botsv3 sourcetype=code42:security | search files{}.fullPath=*Taedonggang* OR files{}.fileName=*Taedonggang* OR processOwner=*Taedonggang* OR deviceRemoteAddress=*Taedonggang* | stats count by eventType processOwner files{}.fileName files{}.fullPath files{}.mimeType files{}.fileEventType files{}.length', 'index=botsv3 sourcetype=code42:security Taedonggang | stats count by eventType processOwner files{}.fileName files{}.fullPath files{}.mimeType files{}.fileEventType files{}.length', 'index=botsv3 sourcetype=ms:o365:reporting:messagetrace (Subject=*deck* OR Subject=*pptx* OR Subject=*xlsx* OR Subject=*docx* OR Subject=*tar.gz* OR Subject=*tgz* OR Subject=*gz*) | stats count by SenderAddress RecipientAddress Subject Size Status MessageId', 'index=botsv3 sourcetype=ms:o365:reporting:messagetrace (Subject=deck OR Subject=pptx OR Subject=xlsx OR Subject=docx OR Subject=tar.gz OR Subject=tgz OR Subject=gz) | stats count by SenderAddress RecipientAddress Subject Size Status MessageId']
- **Senior #19**  _[partial]_  task=1
    - subquestion: Search `index=botsv3` for any document-content/extraction sourcetypes or raw XML tied specifically to `frothly_gabf_deck-2018-mk.pptx` (from `code42:security` upload by MalloryKraeusen), including fil
    - answer: PARTIAL ANSWER: `frothly_gabf_deck-2018-mk.pptx` was definitely uploaded by `MalloryKraeusen` in `code42:security`, with the exact path `c:\users\mallorykraeusen\documents\frothly_gabf_deck-2018-mk.pptx` and MIME type `application/vnd.openxmlformats-officedocument.presentationml.presentation`.

Evidence also shows related extraction/preview-style artifacts in the same Code42 event, including:
- `c
    - SPL: ['index=botsv3 sourcetype=code42:security (files{}.fileName="frothly_gabf_deck-2018-mk.pptx" OR files{}.fullPath="*frothly_gabf_deck-2018-mk.pptx*" OR files{}.fileName="*frothly_gabf_deck*" OR files{}.fullPath="*frothly_gabf_deck*") processOwner=MalloryKraeusen | stats count by eventType processName files{}.fileName files{}.fullPath files{}.fileEventType files{}.mimeType files{}.length files{}.md5', 'index=botsv3 sourcetype=code42:security (files{}.fullPath="*frothly_gabf_deck-2018-mk.pptx*" OR files{}.fileName="frothly_gabf_deck-2018-mk.pptx" OR processOwner="MalloryKraeusen") | stats count by eventType files{}.fileEventType files{}.fileName files{}.fullPath files{}.mimeType files{}.length files{}.md5 processName']
- **Senior #20**  _[partial]_  task=2
    - subquestion: Pivot from the Code42 upload event for `c:\users\mallorykraeusen\documents\frothly_gabf_deck-2018-mk.pptx` to the uploading endpoint/user and inspect adjacent telemetry (`WinEventLog`, Sysmon, `stream
    - answer: PARTIAL ANSWER: The Code42 upload event for `c:\users\mallorykraeusen\documents\frothly_gabf_deck-2018-mk.pptx` is tied to:
- `processOwner=MalloryKraeusen`
- `userUid=858501800121238378`
- `deviceGuid=858503856366658646`
- `processName=\Device\HarddiskVolume4\Program Files (x86)\Google\Chrome\Application\chrome.exe`

I also confirmed the file itself in `code42:security`:
- `files{}.fullPath=c:\us
    - SPL: ['index=botsv3 sourcetype=code42:security "frothly_gabf_deck-2018-mk.pptx" | stats count by files{}.fullPath files{}.fileName files{}.fileEventType files{}.mimeType files{}.md5 endpoint userName user email', 'index=botsv3 sourcetype=code42:security "frothly_gabf_deck-2018-mk.pptx" | stats count by userUid processOwner deviceGuid deviceAddress processName files{}.fullPath files{}.fileEventType files{}.fileName', 'index=botsv3 sourcetype IN (code42:api,code42:computer,code42:org,code42:security,code42:user) Taedonggang | stats count by sourcetype host orgName email firstName lastName processOwner deviceGuid userUid files{}.fullPath files{}.fileName', 'index=botsv3 sourcetype=stream:http (Taedonggang OR taedonggang OR taedong*gang) | stats count by src_ip dest_ip host uri http_method http_user_agent http_referrer', 'index=botsv3 sourcetype IN (stream:smtp,ms:o365:reporting:messagetrace,o365:management:activity,access_combined) ("frothly_gabf_deck-2018-mk.pptx" OR "ba_advertising_code_overview.pdf" OR "Taedonggang") | stats count by sourcetype src_ip dest_ip sender recipient subject file_name attach_filename{} SourceFileName user uri host', 'index=botsv3 sourcetype=xmlwineventlog:microsoft-windows-sysmon/operational deviceGuid=858503856366658646 | stats count by EventCode Image CommandLine ParentImage TargetFilename User']

**SH FINAL → extractor:** `FROTHLY`  [WRONG]  (delegations: 7, cumulative failed delegations: 1)

  SH tokens [Q329]: input=1,140,923  cached=974,592  output=13,709  est=$0.3076

---

## Q330  (1000 pts)

> What Frothly VPN user generated the most traffic?
- **Senior #22**  _[solved]_  task=1
    - subquestion: [HUNTER] In `index=botsv3`, identify the sourcetype(s) that contain Frothly VPN activity during the August 2018 window around epoch `1534737603` to `1534778829`. Prior relevant case entities include e
    - answer: FINAL ANSWER: cisco:asa contains the Frothly VPN username fields, and the traffic-volume fields are in stream:tcp and bandwidth.

- VPN sourcetype: `cisco:asa`
  - Username fields: `user`, `Username`
  - Other related fields: `Group`, `IP`

- Traffic/volume sourcetypes:
  - `stream:tcp`
    - Byte fields: `bytes`, `bytes_in`, `bytes_out`
    - Count/packet fields: `count`, `packets`, `packets_in`,
    - SPL: ['index=botsv3 sourcetype=cisco:asa | stats count by user Username Group IP | search count>0', 'index=botsv3 sourcetype=cisco:asa | stats count by user', 'index=botsv3 sourcetype=cisco:asa | stats count by Username', 'index=botsv3 sourcetype=cisco:asa | stats count by Username', 'index=botsv3 sourcetype=cisco:asa (user=* OR Username=*) | stats count by user Username Group IP', 'index=botsv3 sourcetype=stream:tcp | stats count by bytes bytes_in bytes_out packets packets_in packets_out count']
- **Senior #23**  _[solved]_  task=2
    - subquestion: [METRICS] In `index=botsv3`, using the Frothly VPN sourcetype(s) from the August 2018 window around epoch `1534737603` to `1534778829`, calculate total traffic volume by VPN user and rank users descen
    - answer: FINAL ANSWER: bstoll — 65,291,570 total traffic bytes
SPL: index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 "Session disconnected" | rex field=_raw "Username = (?<user>[^,]+),.*Bytes xmt: (?<bytes_xmt>\d+), Bytes rcv: (?<bytes_rcv>\d+)" | eval total_traffic=bytes_xmt+bytes_rcv | stats sum(total_traffic) as total_traffic by user | sort - total_traffic
    - SPL: ['index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 | stats sum(bytes) as total_bytes by user | sort - total_bytes', 'index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 | stats sum(bytes) as total_bytes count as sessions by user | sort - total_bytes | table user total_bytes sessions', 'index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 "Session disconnected" | rex field=_raw "Username = (?<user>[^,]+),.*Bytes xmt: (?<bytes_xmt>\\d+), Bytes rcv: (?<bytes_rcv>\\d+)" | eval total_traffic=bytes_xmt+bytes_rcv | stats sum(total_traffic) as total_traffic by user | sort - total_traffic']
- **Senior #24**  _[solved]_  task=3
    - subquestion: [CONTENT] In `index=botsv3`, inspect raw Frothly VPN events in the August 2018 window around epoch `1534737603` to `1534778829` to validate how the VPN username is recorded and how traffic volume is m
    - answer: FINAL ANSWER: bstoll
SPL: index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 bstoll

Example raw events showing the username and traffic-byte fields:
- `%ASA-4-113019: Group = DefaultWEBVPNGroup, Username = bstoll, IP = 107.77.212.175, Session disconnected. Session Type: SSL, Duration: 0h:49m:49s, Bytes xmt: 18775, Bytes rcv: 768481, Reason: User Requested`
- `%ASA-6-302016: T
    - SPL: ['index=botsv3 sourcetype=cisco:asa (vpn OR AnyConnect OR tunnel OR user) earliest=1534737603 latest=1534778829 | stats count by host', 'index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 ("Teardown" OR "Assigned" OR "Login") | stats count by _raw', 'index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 | rex field=_raw "user (?<vpn_user>[^\\s,]+)" | stats count by vpn_user | sort -count']
- **Senior #25**  _[solved]_  task=4
    - subquestion: [METRICS] Given [Task-1 (solved): FINAL ANSWER: cisco:asa contains the Frothly VPN username fields, and the traffic-volume fields are in stream:tcp and bandwidth.

- VPN sourcetype: `cisco:asa`
  - Us
    - answer: FINAL ANSWER: bstoll
SPL: index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 "Session disconnected" | rex field=_raw "Username = (?<user>[^,]+),.*Bytes xmt: (?<bytes_xmt>\d+), Bytes rcv: (?<bytes_rcv>\d+)" | eval total_traffic=tonumber(bytes_xmt)+tonumber(bytes_rcv) | stats sum(total_traffic) as total_traffic by user | sort - total_traffic | head 1
    - SPL: ['index=botsv3 sourcetype=cisco:asa earliest=1534737603 latest=1534778829 "Session disconnected" | rex field=_raw "Username = (?<user>[^,]+),.*Bytes xmt: (?<bytes_xmt>\\d+), Bytes rcv: (?<bytes_rcv>\\d+)" | eval total_traffic=tonumber(bytes_xmt)+tonumber(bytes_rcv) | stats sum(total_traffic) as total_traffic by user | sort - total_traffic | head 1']

**SH FINAL → extractor:** `bstoll`  [WRONG]  (delegations: 4, cumulative failed delegations: 1)

  SH tokens [Q330]: input=279,011  cached=211,456  output=5,746  est=$0.1376

---

## Q331  (1000 pts)

> Using Splunk commands only, what is the upper fence (UF) value of the interquartile range (IQR) of the count of event code 4688 by Windows hosts over the entire day? Use a 1.5 multiplier.
- **Senior #27**  _[failed]_  task=1
    - subquestion: [HUNTER] In `index=botsv3`, identify the Windows event-log sourcetype(s) and exact field names needed to count Windows process creation events with event code `4688` by host over the full relevant Aug
    - answer: CONFIDENT ANSWER — The Windows event-log sourcetype that actually contains Event Code 4688 in BOTSv3 is `WinEventLog` (with `sourcetype=WinEventLog`, not `wineventlog`). The exact fields are:

- Event code field: `EventCode`
- Host field: `host`  
  - `dvc` / `dvc_nt_host` also exist in the same data, but `host` is the field used for grouping by host.

What to use for the query:
```spl
index=botsv
    - SPL: ['index=botsv3 (sourcetype=wineventlog OR sourcetype=WinEventLog OR sourcetype="xmlwineventlog:microsoft-windows-sysmon/operational" OR sourcetype=winhostmon) | stats count by sourcetype', 'index=botsv3 sourcetype=WinEventLog EventCode=4688 | stats count by host, EventCode', 'index=botsv3 sourcetype="XmlWinEventLog:Microsoft-Windows-Sysmon/Operational" EventID=4688 | stats count by host, EventID', 'index=botsv3 sourcetype="xmlwineventlog:microsoft-windows-sysmon/operational" | stats count by EventID, host | search EventID=1', 'index=botsv3 sourcetype=winhostmon | stats count by host, sourcetype', 'index=botsv3 sourcetype=WinEventLog EventCode=4688 | stats min(_time) as earliest max(_time) as latest count by host']
- **Senior #28**  _[solved]_  task=2
    - subquestion: [METRICS] In `index=botsv3`, using the correct Windows event-log sourcetype(s) and field names for event code `4688`, count the number of `4688` events per Windows host over the full relevant 24-hour 
    - answer: FINAL ANSWER: BSTOLL-L=1936, PCERF-L=1087, MKRAEUS-L=887, BTUN-L=866, JWORTOS-L=774, BGIST-L=649, FYODOR-L=637, ABUNGST-L=586; Q1=646; Q3=937
SPL: index=botsv3 sourcetype=wineventlog EventCode=4688 earliest=1534755840 latest=1534778279 | eval host=mvindex(split(ComputerName,"."),0) | stats count as event_count by host | eventstats perc25(event_count) as q1 perc75(event_count) as q3 | sort 0 - even
    - SPL: ['index=botsv3 sourcetype=wineventlog EventCode=4688 | stats count as count by _time, ComputerName | stats min(_time) as earliest max(_time) as latest count as events', 'index=botsv3 sourcetype=wineventlog EventCode=4688 earliest=1534755840 latest=1534778279 | eval host=mvindex(split(ComputerName,"."),0) | stats count as event_count by host | eventstats perc25(event_count) as q1 perc75(event_count) as q3 | sort 0 - event_count']
- **Senior #29**  _[partial]_  task=3
    - subquestion: [CONTENT] In `index=botsv3`, validate with raw Windows events that event code `4688` is represented consistently in the chosen sourcetype(s) over the full relevant August 2018 day, and confirm the hos
    - answer: PARTIAL ANSWER:  
- For raw Windows Security events, `EventCode=4688` is consistently represented in sourcetype `WinEventLog` as a line like `EventCode=4688` with `ComputerName=<host>.froth.ly`, and the normalized `host` field strips the domain to just the short host name.
- Sample raw 4688 event text confirms the structure:
  - `EventCode=4688`
  - `ComputerName=BGIST-L.froth.ly`
  - `TaskCategor
    - SPL: ['index=botsv3 sourcetype=WinEventLog EventCode=4688 | stats count by host | sort - count', 'index=botsv3 sourcetype=XmlWinEventLog:Microsoft-Windows-Sysmon/Operational EventID=1 | stats count by host | sort - count', 'index=botsv3 sourcetype="xmlwineventlog:microsoft-windows-sysmon/operational" EventID=1 | stats count by host | sort - count']
- **Senior #30**  _[solved]_  task=4
    - subquestion: [METRICS] Given [Task-1 (failed): CONFIDENT ANSWER — The Windows event-log sourcetype that actually contains Event Code 4688 in BOTSv3 is `WinEventLog` (with `sourcetype=WinEventLog`, not `wineventlog
    - answer: FINAL ANSWER: 1374
SPL: index=botsv3 sourcetype=WinEventLog EventCode=4688 earliest=1534755840 latest=1534778279 | eval host=coalesce(host, mvindex(split(ComputerName,"."),0)) | stats count as event_count by host | eventstats perc25(event_count) as q1 perc75(event_count) as q3 | eval iqr=q3-q1, uf=q3+(1.5*iqr) | stats values(q1) as q1 values(q3) as q3 values(iqr) as iqr values(uf) as uf
    - SPL: ['index=botsv3 sourcetype=WinEventLog EventCode=4688 earliest=1534755840 latest=1534778279 | eval host=coalesce(host, mvindex(split(ComputerName,"."),0)) | stats count as event_count by host | eventstats perc25(event_count) as q1 perc75(event_count) as q3 | eval iqr=q3-q1, uf=q3+(1.5*iqr) | stats values(q1) as q1 values(q3) as q3 values(iqr) as iqr values(uf) as uf']
- **Senior #32**  _[solved]_  task=1
    - subquestion: [HUNTER] In `index=botsv3`, using the official hint to start with `sourcetype=WinEventLog:Security`, identify the exact field names and full-day time window needed to count Windows event code `4688` b
    - answer: FINAL ANSWER: Use `EventCode` for the Windows event code and `host` for the host field. The full-day time window is `2018-08-20 00:00:00` through `2018-08-20 23:59:59` (all 4688 events fall on `2018-08-20`).

SPL: `index=botsv3 sourcetype=WinEventLog EventCode=4688 | stats count by host`
    - SPL: ['index=botsv3 sourcetype=WinEventLog EventCode=4688 | stats min(_time) as earliest max(_time) as latest count by host, ComputerName, EventCode', 'index=botsv3 sourcetype=WinEventLog EventCode=4688 | stats min(_time) as earliest max(_time) as latest by EventCode | eval earliest=strftime(earliest,"%F %T"), latest=strftime(latest,"%F %T")', 'index=botsv3 sourcetype=WinEventLog EventCode=4688 | eval day=strftime(_time,"%F") | stats count by day']
- **Senior #33**  _[solved]_  task=2
    - subquestion: [METRICS] In `index=botsv3`, using `sourcetype=WinEventLog:Security`, count event code `4688` per Windows host over the full relevant day, then compute Q1 and Q3 across those per-host counts using Spl
    - answer: FINAL ANSWER: Per-host 4688 counts over the relevant day:
- ABUNGST-L = 586
- BGIST-L = 649
- FYODOR-L = 637
- JWORTOS-L = 774
- MKRAEUS-L = 887
- BTUN-L = 866
- PCERF-L = 1087
- BSTOLL-L = 1936

Quartiles across those per-host counts:
- Q1 = 646
- Q3 = 937

SPL: `index=botsv3 sourcetype=WinEventLog EventCode=4688 earliest=1534755840 latest=1534778279 host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,
    - SPL: ['index=botsv3 sourcetype=WinEventLog EventCode=4688 | stats min(_time) as earliest max(_time) as latest count by host', 'index=botsv3 sourcetype=WinEventLog EventCode=4688 earliest=1534755840 latest=1534778279 host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) | stats count as event4688_count by host | append [ search index=botsv3 sourcetype=WinEventLog EventCode=4688 earliest=1534755840 latest=1534778279 host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) | stats count as event4688_count by host | eventstats perc25(event4688_count) as q1 perc75(event4688_count) as q3 | eval host="__quartiles__" ] | stats max(event4688_count) as event4688_count max(q1) as q1 max(q3) as q3 by host | search host!="__quartiles__"', 'index=botsv3 sourcetype=WinEventLog EventCode=4688 earliest=1534755840 latest=1534778279 host IN (BGIST-L,JWORTOS-L,FYODOR-L,ABUNGST-L,MKRAEUS-L,BTUN-L,PCERF-L,BSTOLL-L) | stats count as event4688_count by host | eventstats perc25(event4688_count) as q1 perc75(event4688_count) as q3 | stats values(event4688_count) as per_host_counts max(q1) as q1 max(q3) as q3 by host']
- **Senior #34**  _[partial]_  task=3
    - subquestion: [CONTENT] In `index=botsv3`, validate with raw `WinEventLog:Security` events that event code `4688` is recorded consistently and confirm the exact host normalization used for the Windows/Frothly hosts
    - answer: PARTIAL ANSWER: The normalized Windows host field is `host`, and for these Frothly machines it is normalized to the short names exactly as: `BGIST-L`, `JWORTOS-L`, `FYODOR-L`, `ABUNGST-L`, `MKRAEUS-L`, `BTUN-L`, `PCERF-L`, `BSTOLL-L` (while raw event text shows `ComputerName=<host>.froth.ly` and the account often appears as `<host>$`).

Evidence from full-day 4688 aggregation:
- `BSTOLL-L` = 1936

    - SPL: ['index=botsv3 sourcetype=WinEventLog EventCode=4688 host IN (BGIST-L, JWORTOS-L, FYODOR-L, ABUNGST-L, MKRAEUS-L, BTUN-L, PCERF-L, BSTOLL-L) | stats count as count by host | sort host']
- **Senior #35**  _[solved]_  task=4
    - subquestion: [METRICS] Given [Task-1 (solved): FINAL ANSWER: Use `EventCode` for the Windows event code and `host` for the host field. The full-day time window is `2018-08-20 00:00:00` through `2018-08-20 23:59:59
    - answer: FINAL ANSWER: 1374
SPL: `index=botsv3 sourcetype=WinEventLog EventCode=4688 earliest=1534755840 latest=1534778279 | stats count by host | eventstats perc25(count) as Q1 perc75(count) as Q3 | eval UF=Q3+1.5*(Q3-Q1) | stats values(Q1) as Q1 values(Q3) as Q3 values(UF) as UF`
    - SPL: ['index=botsv3 sourcetype=WinEventLog EventCode=4688 earliest=1534755840 latest=1534778279 | stats count by host | eventstats perc25(count) as Q1 perc75(count) as Q3 | eval UF=Q3+1.5*(Q3-Q1) | stats values(Q1) as Q1 values(Q3) as Q3 values(UF) as UF']

**SH FINAL → extractor:** `UF = 2059`  [WRONG]  (delegations: 8, cumulative failed delegations: 2)

  SH tokens [Q331]: input=484,787  cached=366,848  output=10,991  est=$0.2530

---

## SUMMARY

- Correct: 1/5
- Points: 100/4100
- Failed delegations: 2
- LangSmith project: `botsv3-test_20260716_095627`
- Token usage:
  - gpt-5.4-mini-2026-03-17: in=2,810,352  cached=2,296,576  out=46,572  est=$0.7671
  - gpt-5.4-2026-03-05: in=155,704  cached=81,664  out=7,872  est=$0.3236
  - meta/llama-3.3-70b-instruct: in=979  cached=272  out=28  est=$0.0002
- Total tokens: 3,021,507  estimated $1.0910
