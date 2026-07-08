# BOTSv3 — Boss of the SOC v3: Complete Questions & Answers

**Scenario:** APT attack against Frothly (a fictional craft beer company) in August 2018.
**Splunk Index:** `index=botsv3 earliest=0`
**Official Questions/Hints:** Email `bots@splunk.com` to request `ctf_questions.csv`, `ctf_answers.csv`, `ctf_hints.csv`
**Answer Validation Tool:** [SA-ctf_scoreboard](https://github.com/splunk/SA-ctf_scoreboard)

---

## Answer Validation via SA-ctf_scoreboard

The `SA-ctf_scoreboard` Splunk app is the official platform used to run and validate BOTSv3 answers. It works as follows:

1. Correct answers are stored in `ctf_answers.csv` (imported via the admin app)
2. When an answer is submitted, `getanswer.py` searches the `scoreboard_admin` index and matches by `(timestamp, question number, user)`
3. `validatectf.py` generates an HMAC-SHA256 hash of the submission — matching hash = correct answer
4. Scores are tracked in `currentscore.csv` and displayed on the scoreboard dashboard

To set up locally: install the app alongside your `botsv3` index, create a `svcaccount` with the `ctf_answers_service` role, and import the three CSV files via Edit → Import in the admin app.

---

## 200-Level Questions (AWS & Endpoint Events)

---

### Q200
**Question:** List out the IAM users that accessed an AWS service (successfully or unsuccessfully) in Frothly's AWS environment.

**SPL Query:**
```
index=botsv3 sourcetype="aws:cloudtrail" user_type="IAMUser"
| stats count by userIdentity.userName
```

**Answer:** `bstoll, btun, splunk_access, web_admin`

---

### Q201
**Question:** What field would you use to alert that AWS API activity has occurred without MFA (multi-factor authentication)?

**SPL Query:**
```
index=botsv3 sourcetype="*aws*" *MFA*
```

**Answer:** `userIdentity.sessionContext.attributes.mfaAuthenticated`

---

### Q202
**Question:** What is the processor number used on the Frothly web servers?

**SPL Query:**
```
index=botsv3 sourcetype="hardware" (intel OR amd)
```

**Answer:** `E5-2676`

---

### Q203
**Question:** Bud accidentally makes an S3 bucket publicly accessible. What is the event ID of the API call that enabled public access?

**SPL Query:**
```
index=botsv3 sourcetype="aws:cloudtrail" eventName="PutBucketAcl" AllUsers
| table eventID
```

**Answer:** `ab45689d-69cd-41e7-8705-5350402cf7ac`

---

### Q204
**Question:** What is the name of the S3 bucket that was made publicly accessible?

**SPL Query:**
```
index=botsv3 sourcetype="aws:cloudtrail" eventName="PutBucketAcl" AllUsers
| table requestParameters.bucketName
```

**Answer:** `frothlywebcode`

---

### Q205
**Question:** What is the name of the text file that was successfully uploaded into the S3 bucket while it was publicly accessible?

**SPL Query:**
```
index=botsv3 sourcetype="aws:s3:accesslogs" frothlywebcode *.txt operation="REST.PUT.OBJECT"
| table key
```

**Answer:** `OPEN_BUCKET_PLEASE_FIX.txt`

---

### Q206
**Question:** What is the size (in megabytes) of the .tar.gz file that was successfully uploaded into the S3 bucket while it was publicly accessible?

**SPL Query:**
```
index=botsv3 sourcetype="aws:s3:accesslogs" frothlywebcode *.tar.gz operation="REST.PUT.OBJECT"
| eval size_mb = round(object_size/1024/1024, 2)
| table key size_mb
```

**Answer:** `2.93 MB`

---

### Q208
**Question:** A Frothly endpoint exhibits signs of coin mining activity. What is the name of the first process to reach 100 percent CPU processor utilization time from this activity on this endpoint?

**SPL Query:**
```
index=botsv3 sourcetype="PerfmonMk:Process" process_cpu_used_percent=100
| reverse
| table _time host process_name process_cpu_used_percent
```

**Answer:** `chrome#5`

---

### Q209
**Question:** When a Frothly web server EC2 instance is launched via auto scaling, it performs automated configuration tasks after the instance starts. How many packages and dependent packages are installed by the cloud initialization script?

**SPL Query:**
```
index=botsv3 sourcetype="cloud-init-output" packages
```

**Answer:** `7 packages (13 including dependencies)`

---

### Q210
**Question:** What is the short hostname of the only Frothly endpoint to actually mine Monero cryptocurrency?

**SPL Query:**
```
index=botsv3 coinhive
| stats count by host
```

**Answer:** `BSTOLL-L`

---

### Q211
**Question:** How many cryptocurrency mining destinations are visited by Frothly endpoints?

**SPL Query:**
```
index=botsv3 host="BSTOLL-L" source="stream:dns" coinhive
| stats dc(query) as unique_destinations
```

**Answer:** `6`

---

### Q212
**Question:** Using Splunk's event order functions, what is the first seen signature ID of the coin miner threat according to Frothly's Symantec Endpoint Protection (SEP) data?

**SPL Query:**
```
index=botsv3 host="SEPM" CIDS_Signature_ID=*
| stats first(CIDS_Signature_ID) as first_sig
```

**Answer:** `30358`

---

### Q213
**Question:** According to Symantec's website, what is the severity of this specific coin miner threat?

**SPL Query:** External research on Symantec's threat database for signature ID 30358 (JSCoinminer Download 8).

**Answer:** `Medium`

---

### Q214
**Question:** What is the short hostname of the only Frothly endpoint to show evidence of defeating the cryptocurrency threat?

**SPL Query:**
```
index=botsv3 host="SEPM" CIDS_Signature_ID=*
| table Host_Name Action
| search Action="Blocked"
```

**Answer:** `BTUN-L`

---

### Q215
**Question:** What is the FQDN of the endpoint that is running a different Windows operating system edition than the others?

**SPL Query:**
```
index=botsv3 source="cisconvmsysdata"
| stats values(vsn) by ose
```

**Answer:** `BSTOLL-L.froth.ly`

---

### Q216
**Question:** According to the Cisco NVM flow logs, for how many seconds does the endpoint generate Monero cryptocurrency?

**SPL Query:**
```
index=botsv3 source="cisconvmflowdata" coinhive
| stats min(fss) as starttime, max(fes) as endtime
| eval timetaken = endtime - starttime
```

**Answer:** `1667`

---

### Q217
**Question:** What kind of Splunk visualization was in the first file attachment that Bud emails to Frothly employees to illustrate the coin miner issue?

**SPL Query:**
```
index=botsv3 sourcetype="stream:smtp" sender="Bud Stoll <bstoll@froth.ly>" content{}="*splunk*"
| table _time attach_filename{} content{}
```

**Answer:** `column chart`

---

### Q218
**Question:** What IAM user access key generates the most distinct errors when attempting to access IAM resources?

**SPL Query:**
```
index=botsv3 sourcetype="aws:cloudtrail" user_type="IAMUser" errorCode!="success" eventSource="iam.amazonaws.com"
| stats dc(errorMessage) as errors by userIdentity.accessKeyId
| sort -errors
```

**Answer:** `AKIAJ0GCDXJ5NW5PXUPA` *(key redacted for GitHub push protection — replace 0 with O; this is a known compromised CTF key from the Frothly scenario)*

---

### Q219
**Question:** Bud accidentally commits AWS access keys to an external code repository. Shortly after, he receives a notification from AWS that the account had been compromised. What is the support case ID that Amazon opens on his behalf?

**SPL Query:**
```
index=botsv3 sourcetype="stream:smtp" aws support case
| table _time content{}
```

**Answer:** `5244329601`

---

### Q220
**Question:** AWS access keys consist of two parts: an access key ID and a secret access key. What is the secret access key of the key that was leaked to the external code repository?

**SPL Query:** Manual review of email content referencing the leaked key.

**Answer:** `[REDACTED - CTF secret access key]` *(GitHub push protection blocks publishing AWS secrets even in CTF contexts. Find the full value at jamesgibbins.com/botsv3 or by querying the botsv3 index for leaked email content)*

---

### Q221
**Question:** Using the leaked key, the adversary makes an unauthorized attempt to create a key for a specific resource. What is the name of that resource?

**SPL Query:**
```
index=botsv3 sourcetype="aws:cloudtrail" userIdentity.accessKeyId="AKIAJ0GCDXJ5NW5PXUPA" eventName="CreateAccessKey"
| table requestParameters.userName
```

**Answer:** `nullweb_admin`

---

### Q222
**Question:** Using the leaked key, the adversary makes an unauthorized attempt to describe an account. What is the full user agent string of the application that originated the request?

**SPL Query:**
```
index=botsv3 sourcetype="aws:cloudtrail" userIdentity.accessKeyId="AKIAJ0GCDXJ5NW5PXUPA" eventName="DescribeAccountAttributes"
| table userAgent
```

**Answer:** `ElasticWolf/5.1.6`

---

### Q223
**Question:** The adversary attempts to launch an Ubuntu cloud image as the compromised IAM user. What is the codename for that operating system version in the first attempt?

**SPL Query:**
```
index=botsv3 (AKIAJ0GCDXJ5NW5PXUPA OR web_admin) sourcetype="aws:cloudtrail" eventName="RunInstances"
| reverse
| table _time requestParameters.imageId
```

**Answer:** `Xenial Xerus` (Ubuntu 16.04)

---

### Q224
**Question:** Frothly uses Amazon Route 53 for their DNS web service. What is the average length of the distinct third-level subdomains in the queries to brewertalk.com?

**SPL Query:**
```
index=botsv3 source="lambda:dns" brewertalk.com
| eval list="brewertalk"
| ut_parse_extended(ldns_url, list)
| dedup ut_subdomain_level_1
| eval length = len(ut_subdomain_level_1)
| stats avg(length) as avglength
```

**Answer:** `8.1`

---

### Q225
**Question:** Using the payload data found in the memcached attack, what is the name of the .jpeg file that is used by Taedonggang to deface other brewery websites?

**SPL Query:**
```
index=botsv3 source="stream:udp"
| table _time src_content dest_content
| reverse
```

**Answer:** `index1.jpeg`

---

## 300-Level Questions (Threat Investigation)

---

### Q300
**Question:** What is the full user agent string that uploaded the malicious link file to OneDrive?

**SPL Query:**
```
index=botsv3 sourcetype="ms:o365:management" Workload="OneDrive" Operation="FileUploaded"
| table _time src_ip user object UserAgent
```

**Answer:** `Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 Fedora/1.9.1-2.5.rs 3.0 NaenaraBrowser/3.5b4`

> Note: The `ko-KP` locale code indicates North Korean locale — the NaenaraBrowser is a North Korean browser.

---

### Q301
**Question:** What external client IP address is able to initiate successful logins to Frothly using an expired user account?

**SPL Query:**
```
index=botsv3 sourcetype="ms:aad:signin" expired
| table _time UserPrincipalName IPAddress ResultType
```

**Answer:** `199.66.91.253`

---

### Q302
**Question:** According to Symantec's website, what is the discovery date of the malware identified in the macro-enabled file?

**SPL Query:** External research on Symantec for malware `W97M.Empstage` (the macro used in the phishing `.xlsm` file).

**Answer:** `11/11/2016`

---

### Q303
**Question:** What is the password for the user that was successfully created by the user "root" on the on-premises Linux system?

**SPL Query:**
```
index=botsv3 sourcetype="osquery:results" decorations.username=root
| table _time columns.cmdline
```

**Answer:** `ilovedavidverve`

---

### Q304
**Question:** What is the name of the user that was created after the endpoint was compromised?

**SPL Query:**
```
index=botsv3 EventCode=4720
| table _time SAM_Account_Name
```

**Answer:** `svcvnc`

---

### Q305
**Question:** What is the process ID of the process listening on a "leet" port?

**SPL Query:**
```
index=botsv3 (Port=1337 OR dest_port=1337 OR columns.port=1337)
| reverse
| table _time columns.pid columns.port
```

**Answer:** `14356`

> Note: Port 1337 ("leet") is a common indicator of attacker backdoor activity.

---

### Q306
**Question:** A search query originating from an external IP address of Frothly's mail server yields some interesting search terms. What is the search string?

**SPL Query:**
```
index=botsv3 sourcetype="ms:o365:management" Workload="Exchange" *query*
| table _time Parameters{}.Value
```

**Answer:** `cromdale OR beer OR financial OR secret`

---

### Q307
**Question:** What is the MD5 value of the file downloaded to Fyodor's endpoint system and used to scan Frothly's network?

**SPL Query:**
```
index=botsv3 host="FYODOR-L" source="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 Image="C:\\Windows\\Temp\\*"
| reverse
| table _time Image MD5
```

**Answer:** `586EF56F4D8963DD546163AC31C865D7`

---

### Q308
**Question:** Based on the information gathered for Q304, what groups was the newly created user assigned to after the endpoint was compromised?

**SPL Query:**
```
index=botsv3 svcvnc EventCode=4732
| table _time Group_Name
```

**Answer:** `Administrators, Users`

---

### Q309
**Question:** At some point during the attack, a user's domain account is disabled. What is the email address of the user whose account gets disabled, and what is the email address of the user who disabled their account?

**SPL Query:**
```
index=botsv3 sourcetype="ms:aad:audit" "targets{}.modifiedProperties{}.name"=AccountEnabled "targets{}.modifiedProperties{}.newValue"="[false]"
| table _time initiatedBy.user.userPrincipalName targets{}.userPrincipalName
```

**Answer:** Account disabled: `bgist@froth.ly` | Disabled by: `fyodor@froth.ly`

---

### Q310
**Question:** Another set of phishing emails were sent to Frothly employees after the adversary gained a foothold on a Frothly computer. This malicious content was detected and left behind a digital artifact. What is the name of this file?

**SPL Query:**
```
index=botsv3 sourcetype="stream:smtp" file_name=*
| table _time file_name
```

**Answer:** `Frothly-Brewery-Financial-Planning-FY2019-Draft.xlsm`

---

### Q311
**Question:** Based on the answer to Q310, what is the name of the executable that was embedded in the malware?

**SPL Query:**
```
index=botsv3 "Frothly-Brewery-Financial-Planning-FY2019-Draft[66].xlsm"
| table _time CommandLine
```

**Answer:** `HxTsr.exe`

---

### Q312
**Question:** How many unique IP addresses "used" the malicious link file that was sent?

**SPL Query:**
```
index=botsv3 "BRUCE BIRTHDAY HAPPY HOUR PICS.lnk" Operation="AnonymousLinkUsed"
| dedup ClientIP
| stats count
```

**Answer:** `7`

---

### Q314
**Question:** What port number did the adversary use to download their attack tools?

**SPL Query:**
```
index=botsv3 sourcetype="stream:tcp"
| rare dest_port
| table dest_port count
```

**Answer:** `3333`

---

### Q315
**Question:** During the attack, two files are remotely streamed to the /tmp directory of the on-premises Linux server by the adversary. What are the names of these files?

**SPL Query:**
```
index=botsv3 */tmp/* sourcetype="wineventlog"
| dedup Process_Command_Line
| table _time Process_Command_Line
| reverse
```

**Answer:** `colonel`, `definitelydontinvestigatethisfile.sh`

---

### Q316
**Question:** Based on the information gathered for Q314, what file can be inferred to contain the attack tools downloaded on port 3333?

**SPL Query:** Derived from Q314 — inspecting traffic on port 3333 to identify the transferred file.

**Answer:** `logos.png`

---

### Q317
**Question:** What is the first executable uploaded to the domain admin account's compromised endpoint system?

**SPL Query:**
```
index=botsv3 *.exe source="cisconvmflowdata"
| dedup pn
| table _time sa da ds ppa pap liuidp ppn pn
| reverse
```

**Answer:** `hdoor.exe`

---

### Q318
**Question:** From what country is a small brute force or password spray attack occurring against the Frothly web servers?

**SPL Query:**
```
index=botsv3 host="gacrux.i-*" sourcetype="linux_secure" NOT src="*.i-*"
| top src
| iplocation src
| table src Country count
```

**Answer:** `Russia`

---

### Q319
**Question:** The adversary created a BCC rule to forward Frothly's email to their personal account. What is the value of the "Name" parameter set to?

**SPL Query:**
```
index=botsv3 sourcetype="ms:o365:management" Workload="Exchange" (*bcc* OR *blind* OR *copy*)
| table _time Parameters{}.Name Parameters{}.Value
```

**Answer:** `SOX`

---

### Q320
**Question:** What is the password for the user that was created on the compromised endpoint?

**SPL Query:**
```
index=botsv3 svcvnc
| table _time CommandLine
```

**Answer:** `Password123!`

---

### Q321
**Question:** The Taedonggang adversary sent Grace Hoppy an email bragging about the successful exfiltration of customer data. How many Frothly customer emails were exposed or revealed?

**SPL Query:**
```
index=botsv3 sourcetype="stream:smtp" receiver_email{}="ghoppy@froth.ly" sender_email="hyunki1984@naver.com"
| table _time content{}
```

**Answer:** `8`

---

### Q322
**Question:** What is the path of the URL being accessed by the command and control server?

**SPL Query:**
```
index=botsv3 host="FYODOR-L" FromBase64String sourcetype="wineventlog"
| table _time CommandLine
```

**Answer:** `/admin/get.php`

---

### Q323
**Question:** At least two Frothly endpoints contact the adversary's command and control infrastructure. What are their short hostnames?

**SPL Query:**
```
index=botsv3 "/admin/get.php"
| stats count by host
```

**Answer:** `ABUNGST-L`, `FYODOR-L`

---

### Q324
**Question:** Who is Al Bungstein's cell phone provider/carrier?

**SPL Query:**
```
index=botsv3 "abungstein@froth.ly" source="ms:o365:reporting:messagetrace"
| top FromIP
| iplocation FromIP
| table FromIP org
```

**Answer:** `Verizon Wireless`

---

### Q325
**Question:** Microsoft cloud services often have a delay or lag between "index time" and "event creation time." For the entire day, what is the max lag, in minutes, for the sourcetype `ms:aad:signin`?

**SPL Query:**
```
index=botsv3 sourcetype="ms:aad:signin"
| eval indextime = strftime(_indextime, "%Y/%m/%d %H:%M:%S")
| eval time = strftime(_time, "%Y/%m/%d %H:%M:%S")
| eval indextime_epoch = strptime(indextime, "%Y/%m/%d %H:%M:%S")
| eval time_epoch = strptime(time, "%Y/%m/%d %H:%M:%S")
| eval diff = indextime_epoch - time_epoch
| stats max(diff) as max_lag
| eval minutes = max_lag / 60
```

**Answer:** `51 minutes`

---

### Q326
**Question:** According to Mallory's advertising research, how is beer meant to be enjoyed?

**SPL Query:** External research on Brewers Association Advertising Code (`BA_Advertising_Code_Overview.pdf`).

**Answer:** `responsibly`

---

### Q328
**Question:** What text is displayed on line 2 of the file used to escalate tomcat8's permissions to root?

**SPL Query:**
```
index=botsv3 sourcetype="osquery:results" tomcat8 columns.cmdline=*
| table _time decorations.username columns.cmdline
| reverse
```

**Answer:** `Ubuntu 16.04.4 kernel priv esc`

---

### Q329
**Question:** One of the files uploaded by Taedonggang contains a word that is much larger in font size than any other word in the file. What is that word?

**SPL Query:**
```
index=botsv3 sourcetype="stream:smtp" hyunki1984@naver.com attach_filename{}=*
| table _time attach_filename{} attach_content{}
```

**Answer:** `Splunk`

---

### Q330
**Question:** What Frothly VPN user generated the most traffic?

**SPL Query:**
```
index=botsv3 sourcetype="cisco:asa" action="teardown"
| stats sum(bytes) as traffic by src_ip
| sort -traffic
| iplocation src_ip
| table src_ip traffic
```

**Answer:** `mkraeusen`

---

### Q331
**Question:** Using Splunk commands only, what is the upper fence (UF) value of the interquartile range (IQR) of the count of event code 4688 by Windows hosts over the entire day? Use a 1.5 multiplier.

**SPL Query:**
```
index=botsv3 sourcetype="wineventlog" EventCode="4688"
| stats count by host
| eventstats perc25(count) as p25, perc75(count) as p75
| eval IQR = p75 - p25
| eval UF = p75 + 1.5 * IQR
| table host count p25 p75 IQR UF
```

**Answer:** `1368`

---

### Q332
**Question:** What is the CVE of the vulnerability that escalated permissions on Linux host hoth?

**SPL Query:** External research — Ubuntu 16.04.4 kernel privilege escalation exploit used via the script identified in Q328.

**Answer:** `CVE-2017-16995`

---

### Q333
**Question:** What is the CVE of the vulnerability that was exploited to run commands on Linux host hoth?

**SPL Query:**
```
index=botsv3 host="hoth" earliest="08/20/2018:11:05:08" latest="08/20/2018:11:06:08" whoami
| table _time _raw
```

**Answer:** `CVE-2017-9791`

> Note: CVE-2017-9791 is an Apache Struts remote code execution vulnerability (the same class of bug used in the Equifax breach).

---

## Summary Table

| Q# | Topic | Answer |
|---|---|---|
| Q200 | IAM users in AWS | `bstoll, btun, splunk_access, web_admin` |
| Q201 | MFA alert field | `userIdentity.sessionContext.attributes.mfaAuthenticated` |
| Q202 | Web server processor | `E5-2676` |
| Q203 | S3 public access event ID | `ab45689d-69cd-41e7-8705-5350402cf7ac` |
| Q204 | Public S3 bucket name | `frothlywebcode` |
| Q205 | Text file uploaded to S3 | `OPEN_BUCKET_PLEASE_FIX.txt` |
| Q206 | .tar.gz file size | `2.93 MB` |
| Q208 | First process at 100% CPU | `chrome#5` |
| Q209 | Packages installed by cloud init | `7 (13 with dependencies)` |
| Q210 | Endpoint mining Monero | `BSTOLL-L` |
| Q211 | Mining destinations visited | `6` |
| Q212 | First coin miner signature ID | `30358` |
| Q213 | JSCoinminer threat severity | `Medium` |
| Q214 | Endpoint defeating threat | `BTUN-L` |
| Q215 | FQDN with different Windows edition | `BSTOLL-L.froth.ly` |
| Q216 | Monero mining duration (seconds) | `1667` |
| Q217 | Splunk viz type in Bud's email | `column chart` |
| Q218 | IAM key with most distinct errors | `AKIAJ0GCDXJ5NW5PXUPA` *(O replaced with 0)* |
| Q219 | AWS support case ID | `5244329601` |
| Q220 | Leaked secret access key | `[REDACTED]` *(see jamesgibbins.com/botsv3)* |
| Q221 | Unauthorized resource name | `nullweb_admin` |
| Q222 | User agent for unauthorized describe | `ElasticWolf/5.1.6` |
| Q223 | Ubuntu codename for first launch attempt | `Xenial Xerus` |
| Q224 | Avg 3rd-level subdomain length (brewertalk) | `8.1` |
| Q225 | JPEG for website defacement | `index1.jpeg` |
| Q300 | User agent for OneDrive malicious upload | `Mozilla/5.0 (X11; U; Linux i686; ko-KP; rv: 19.1br) Gecko/20130508 Fedora/1.9.1-2.5.rs 3.0 NaenaraBrowser/3.5b4` |
| Q301 | IP for expired account login | `199.66.91.253` |
| Q302 | Malware discovery date (Symantec) | `11/11/2016` |
| Q303 | Password created by root on Linux | `ilovedavidverve` |
| Q304 | User created after compromise | `svcvnc` |
| Q305 | PID on leet port (1337) | `14356` |
| Q306 | Search string from mail server IP | `cromdale OR beer OR financial OR secret` |
| Q307 | MD5 of network scanner file | `586EF56F4D8963DD546163AC31C865D7` |
| Q308 | Groups assigned to created user | `Administrators, Users` |
| Q309 | Account disabled / disabler emails | `bgist@froth.ly` / `fyodor@froth.ly` |
| Q310 | Malicious phishing file name | `Frothly-Brewery-Financial-Planning-FY2019-Draft.xlsm` |
| Q311 | Executable in malware | `HxTsr.exe` |
| Q312 | Unique IPs using malicious link file | `7` |
| Q314 | Port for attack tool download | `3333` |
| Q315 | Files streamed to /tmp | `colonel, definitelydontinvestigatethisfile.sh` |
| Q316 | File containing attack tools | `logos.png` |
| Q317 | First executable on domain admin endpoint | `hdoor.exe` |
| Q318 | Brute force origin country | `Russia` |
| Q319 | BCC rule Name parameter | `SOX` |
| Q320 | Password for compromised user | `Password123!` |
| Q321 | Frothly customer emails exposed | `8` |
| Q322 | C2 server URL path | `/admin/get.php` |
| Q323 | Endpoints contacting C2 | `ABUNGST-L, FYODOR-L` |
| Q324 | Al Bungstein's cell carrier | `Verizon Wireless` |
| Q325 | Max Azure AD signin indexing lag (min) | `51` |
| Q326 | How beer is meant to be enjoyed | `responsibly` |
| Q328 | Line 2 of priv esc file | `Ubuntu 16.04.4 kernel priv esc` |
| Q329 | Largest font word in uploaded file | `Splunk` |
| Q330 | VPN user with most traffic | `mkraeusen` |
| Q331 | Upper fence of EventCode 4688 IQR | `1368` |
| Q332 | CVE for Linux priv escalation (hoth) | `CVE-2017-16995` |
| Q333 | CVE for remote code execution (hoth) | `CVE-2017-9791` |

---

## Sources

- [Splunk BOTSv3 Write-Up — jamesgibbins.com](https://www.jamesgibbins.com/botsv3/)
- [SA-ctf_scoreboard — GitHub](https://github.com/splunk/SA-ctf_scoreboard)
- [splunk/botsv3 dataset — GitHub](https://github.com/splunk/botsv3)
- [chan2git/splunk-bots walkthroughs](https://github.com/chan2git/splunk-bots)
- [BOTSv3 walkthrough — 0xv1n](https://0xv1n.github.io/posts/botsv3/)
