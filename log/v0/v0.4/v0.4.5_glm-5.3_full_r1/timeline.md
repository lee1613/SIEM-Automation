
---

## ↩ Resumed: 2026-09-24T12:00:18


---

## Q200  (100 pts)

> List out the IAM users that accessed an AWS service (successfully or unsuccessfully) in Frothly's AWS environment?

**SH FINAL:** `bstoll,btun,splunk_access,web_admin`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q200]: input=54,402  cached=37,120  output=1,857  est=$0.0803

---

## Q201  (100 pts)

> What field would you use to alert that AWS API activity have occurred without MFA (multi-factor authentication)?

**SH FINAL:** `userIdentity.sessionContext.attributes.mfaAuthenticated`  [CORRECT]  (delegations: 2, cumulative failed delegations: 0)

  SH tokens [Q201]: input=53,987  cached=48,384  output=1,525  est=$0.0490

---

## Q202  (500 pts)

> What is the processor number used on the web servers?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 9, cumulative failed delegations: 0)

  SH tokens [Q202]: input=361,395  cached=333,568  output=8,947  est=$0.2872

---

## Q203  (100 pts)

> Bud accidentally makes an S3 bucket publicly accessible. What is the event ID of the API call that enabled public access?

**SH FINAL:** `ab45689d-69cd-41e7-8705-5350402cf7ac`  [CORRECT]  (delegations: 2, cumulative failed delegations: 0)

  SH tokens [Q203]: input=115,760  cached=91,392  output=1,580  est=$0.1075

---

## Q204  (100 pts)

> What is the name of the S3 bucket that was made publicly accessible?

**SH FINAL:** `frothlywebcode`  [CORRECT]  (delegations: 2, cumulative failed delegations: 0)

  SH tokens [Q204]: input=174,917  cached=160,768  output=2,754  est=$0.1169

---

## Q205  (100 pts)

> What is the name of the text file that was successfully uploaded into the S3 bucket while it was publicly accessible?

**SH FINAL:** `OPEN_BUCKET_PLEASE_FIX.txt`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q205]: input=248,679  cached=230,144  output=2,675  est=$0.1440

---

## Q206  (100 pts)

> What is the size (in megabytes) of the .tar.gz file that was successfully uploaded into the S3 bucket while it was publicly accessible?

**SH FINAL:** `2.93`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q206]: input=224,039  cached=204,800  output=2,071  est=$0.1304

---

## Q208  (100 pts)

> A Frothly endpoint exhibits signs of coin mining activity. What is the name of the first process to reach 100 percent CPU processor utilization time from this activity on this endpoint?

**SH FINAL:** `chrome#5`  [CORRECT]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q208]: input=304,519  cached=287,488  output=2,543  est=$0.1526

---

## Q209  (500 pts)

> When a Frothly web server EC2 instance is launched via auto scaling, it performs automated configuration tasks after the instance starts. How many packages and dependent packages are installed by the cloud initialization script?

**SH FINAL:** `7,13`  [CORRECT]  (delegations: 9, cumulative failed delegations: 0)

  SH tokens [Q209]: input=705,824  cached=677,376  output=5,282  est=$0.3197

---

## Q210  (500 pts)

> What is the short hostname of the only Frothly endpoint to actually mine Monero cryptocurrency?

**SH FINAL:** `BSTOLL-L`  [CORRECT]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q210]: input=656,373  cached=623,616  output=4,511  est=$0.3055

---

## Q211  (100 pts)

> How many cryptocurrency mining destinations are visited by Frothly endpoints?

**SH FINAL:** `6`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q211]: input=443,012  cached=419,584  output=2,149  est=$0.1957

---

## Q212  (100 pts)

> Using Splunk's event order functions, what is the first seen signature ID of the coin miner threat according to Frothly's Symantec Endpoint Protection (SEP) data?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q212]: input=466,467  cached=447,232  output=2,490  est=$0.1972

---

## Q213  (100 pts)

> According to Symantec's website, what is the severity of this specific coin miner threat?

**SH FINAL:** `NOT_FOUND`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q213]: input=593,488  cached=572,928  output=2,613  est=$0.2338

---

## Q214  (100 pts)

> What is the short hostname of the only Frothly endpoint to show evidence of defeating the cryptocurrency threat?

**SH FINAL:** `BTUN-L`  [CORRECT]  (delegations: 2, cumulative failed delegations: 0)

  SH tokens [Q214]: input=413,787  cached=394,240  output=2,286  est=$0.1817

---

## Q215  (500 pts)

> What is the FQDN of the endpoint that is running a different Windows operating system edition than the others?

**SH FINAL:** `BSTOLL-L.froth.ly`  [CORRECT]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q215]: input=1,107,994  cached=1,079,808  output=5,479  est=$0.4226

---

## Q216  (1000 pts)

> According to the Cisco NVM flow logs, for how many seconds does the endpoint generate Monero cryptocurrency?

**SH FINAL:** `1667`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q216]: input=472,278  cached=444,416  output=2,706  est=$0.2213

---

## Q217  (1000 pts)

> What kind of Splunk visualization was in the first file attachment that Bud emails to Frothly employees to illustrate the coin miner issue?

---

## ↩ Resumed: 2026-09-24T15:59:07


---

## Q217  (1000 pts)

> What kind of Splunk visualization was in the first file attachment that Bud emails to Frothly employees to illustrate the coin miner issue?

**SH FINAL:** `line chart`  [WRONG]  (delegations: 11, cumulative failed delegations: 0)

  SH tokens [Q217]: input=275,315  cached=271,872  output=1,185  est=$0.0944

---


---

## ↩ Resumed: 2026-09-24T16:29:12


---

## Q218  (500 pts)

> What IAM user access key generates the most distinct errors when attempting to access IAM resources?

**SH FINAL:** `AKIAJOGCDXJ5NW5PXUPA`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q218]: input=711,702  cached=702,208  output=2,630  est=$0.2387

---

## Q219  (100 pts)

> Bud accidentally commits AWS access keys to an external code repository. Shortly after, he receives a notification from AWS that the account had been compromised. What is the support case ID that Amazon opens on his behalf?

**SH FINAL:** `5244329601`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q219]: input=589,894  cached=566,272  output=1,847  est=$0.2283

---

## Q221  (100 pts)

> Using the leaked key, the adversary makes an unauthorized attempt to create a key for a specific resource. What is the name of that resource?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q221]: input=916,038  cached=891,392  output=2,868  est=$0.3275

---

## Q222  (100 pts)

> Using the leaked key, the adversary makes an unauthorized attempt to describe an account. What is the full user agent string of the application that originated the request?

**SH FINAL:** `ElasticWolf/5.1.6`  [CORRECT]  (delegations: 1, cumulative failed delegations: 0)

  SH tokens [Q222]: input=630,909  cached=608,256  output=1,992  est=$0.2386

---


---

## ↩ Resumed: 2026-09-24T17:45:25


---

## Q223  (500 pts)

> The adversary attempts to launch an Ubuntu cloud image as the compromised IAM user. What is the codename for that operating system version in the first attempt?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 7, cumulative failed delegations: 0)

  SH tokens [Q223]: input=2,187,476  cached=2,163,456  output=9,026  est=$0.7363

---

## Q224  (1000 pts)

> Frothly uses Amazon Route 53 for their DNS web service. What is the average length of the distinct third-level subdomains in the queries to brewertalk.com?

**SH FINAL:** `8.10`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q224]: input=489,856  cached=374,784  output=2,056  est=$0.4122

---

## Q225  (500 pts)

> Using the payload data found in the memcached attack, what is the name of the .jpeg file that is used by Taedonggang to deface other brewery websites?

**SH FINAL:** `index1.jpeg`  [CORRECT]  (delegations: 8, cumulative failed delegations: 0)

  SH tokens [Q225]: input=1,444,527  cached=1,408,256  output=5,819  est=$0.5300

---

## Q300  (100 pts)

> What is the full user agent string that uploaded the malicious link file to OneDrive?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q300]: input=699,195  cached=665,344  output=2,322  est=$0.2858

---

## Q301  (100 pts)

> What external client IP address is able to initiate successful logins to Frothly using an expired user account?

**SH FINAL:** `NOT_FOUND`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q301]: input=727,110  cached=702,208  output=2,297  est=$0.2723

---

## Q302  (100 pts)

> According to Symantec's website, what is the discovery date of the malware identified in the macro-enabled file?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q302]: input=746,534  cached=722,688  output=2,375  est=$0.2759

---

## Q303  (100 pts)

> What is the password for the user that was successfully created by the user "root" on the on-premises Linux system?

**SH FINAL:** `ilovedavidverve`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q303]: input=772,704  cached=745,216  output=2,404  est=$0.2911

---

## Q304  (100 pts)

> What is the name of the user that was created after the endpoint was compromised?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q304]: input=794,507  cached=768,768  output=2,275  est=$0.2907

---

## Q305  (100 pts)

> What is the process ID of the process listening on a "leet" port?

**SH FINAL:** `14356`  [CORRECT]  (delegations: 1, cumulative failed delegations: 0)

  SH tokens [Q305]: input=655,072  cached=630,784  output=2,004  est=$0.2485

---

## Q306  (100 pts)

> A search query originating from an external IP address of Frothly's mail server yields some interesting search terms. What is the search string?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q306]: input=838,624  cached=812,800  output=2,484  est=$0.3050

---

## Q307  (100 pts)

> What is the MD5 value of the file downloaded to Fyodor's endpoint system and used to scan Frothly's network?

**SH FINAL:** `586EF56F4D8963DD546163AC31C865D7`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q307]: input=487,165  cached=375,808  output=2,090  est=$0.4037

---

## Q308  (100 pts)

> Based on the information gathered for question 304, what groups was this user assigned to after the endpoint was compromised?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q308]: input=633,416  cached=606,976  output=2,330  est=$0.2528

---

## Q309  (100 pts)

> At some point during the attack, a user's domain account is disabled. What is the email address of the user whose account gets disabled and what is the email address of the user who disabled their account?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q309]: input=655,169  cached=629,504  output=2,287  est=$0.2558

---

## Q310  (500 pts)

> Another set of phishing emails were sent to Frothly employees after the adversary gained a foothold on a Frothly computer. This malicious content was detected and left behind a digital artifact. What is the name of this file?

**SH FINAL:** `Bruce Birthday Happy Hour Pics.lnk`  [WRONG]  (delegations: 10, cumulative failed delegations: 0)

  SH tokens [Q310]: input=1,849,809  cached=1,805,056  output=7,155  est=$0.6705

---

## Q311  (500 pts)

> Based on the answer to question 310, what is the name of the executable that was embedded in the malware?

---

## ↩ Resumed: 2026-09-24T20:58:27


---

## Q311  (500 pts)

> Based on the answer to question 310, what is the name of the executable that was embedded in the malware?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 7, cumulative failed delegations: 0)

  SH tokens [Q311]: input=314,750  cached=312,832  output=1,098  est=$0.0995

---

## Q312  (500 pts)

> How many unique IP addresses "used" the malicious link file that was sent?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 6, cumulative failed delegations: 0)

  SH tokens [Q312]: input=2,131,365  cached=2,087,680  output=7,005  est=$0.7362

---

## Q314  (500 pts)

> What port number did the adversary use to download their attack tools?

**SH FINAL:** `3333`  [CORRECT]  (delegations: 6, cumulative failed delegations: 0)

  SH tokens [Q314]: input=1,420,180  cached=1,296,640  output=7,309  est=$0.7426

---

## Q315  (500 pts)

> During the attack, two files are remotely streamed to the /tmp directory of the on-premises Linux server by the adversary. What are the names of these files?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 8, cumulative failed delegations: 0)

  SH tokens [Q315]: input=1,875,227  cached=1,820,416  output=9,307  est=$0.7317

---

## Q316  (500 pts)

> Based on the information gathered for question 314, what file can be inferred to contain the attack tools?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 6, cumulative failed delegations: 0)

  SH tokens [Q316]: input=1,588,991  cached=1,536,512  output=6,046  est=$0.6060

---


---

## ↩ Resumed: 2026-09-24T22:46:49


---

## Q317  (500 pts)

> What is the first executable uploaded to the domain admin account's compromised endpoint system?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 8, cumulative failed delegations: 0)

  SH tokens [Q317]: input=2,251,178  cached=2,228,992  output=9,199  est=$0.7507

---

## Q318  (500 pts)

> From what country is a small brute force or password spray attack occurring against the Frothly web servers?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 5, cumulative failed delegations: 0)

  SH tokens [Q318]: input=1,291,869  cached=1,175,040  output=7,337  est=$0.6959

---

## Q319  (500 pts)

> The adversary created a BCC rule to forward Frothly's email to his personal account. What is the value of the "Name" parameter set to?

**SH FINAL:** `SOX`  [CORRECT]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q319]: input=1,252,118  cached=1,208,064  output=4,680  est=$0.4824

---

## Q320  (500 pts)

> What is the password for the user that was created on the compromised endpoint?

**SH FINAL:** `davidverve.com`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q320]: input=1,622,136  cached=1,580,288  output=5,457  est=$0.5815

---

## Q321  (500 pts)

> The Taedonggang adversary sent Grace Hoppy an email bragging about the successful exfiltration of customer data. How many Frothly customer emails were exposed or revealed?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 9, cumulative failed delegations: 0)

  SH tokens [Q321]: input=2,084,551  cached=2,033,408  output=7,415  est=$0.7474

---

## Q322  (500 pts)

> What is the path of the URL being accessed by the command and control server?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q322]: input=884,421  cached=778,496  output=4,705  est=$0.5300

---

## Q323  (500 pts)

> At least two Frothly endpoints contact the adversary's command and control infrastructure. What are their short hostnames?

**SH FINAL:** `ABUNGST-L,FYODOR-L`  [CORRECT]  (delegations: 2, cumulative failed delegations: 0)

  SH tokens [Q323]: input=663,266  cached=628,480  output=2,674  est=$0.2842

---

## Q324  (500 pts)

> Who is Al Bungstein's cell phone provider/carrier?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 7, cumulative failed delegations: 0)

  SH tokens [Q324]: input=1,421,963  cached=1,379,840  output=6,471  est=$0.5473

---

## Q325  (500 pts)

> Microsoft cloud services often have a delay or lag between "index time" and "event creation time". For the entire day, what is the max lag, in minutes, for the sourcetype: ms:aad:signin?

**SH FINAL:** `51`  [CORRECT]  (delegations: 2, cumulative failed delegations: 0)

  SH tokens [Q325]: input=758,587  cached=717,568  output=2,470  est=$0.3190

---

## Q326  (500 pts)

> According to Mallory's advertising research, how is beer meant to be enjoyed?

**SH FINAL:** `SH retired without answering`  [WRONG]  (delegations: 9, cumulative failed delegations: 0)

  SH tokens [Q326]: input=1,936,964  cached=1,890,304  output=6,702  est=$0.6898

---


---

## ↩ Resumed: 2026-09-25T03:21:53


---


---

## ↩ Resumed: 2026-09-25T07:46:58


---


---

## ↩ Resumed: 2026-09-25T09:53:58


---

## Q328  (1000 pts)

> What text is displayed on line 2 of the file used to escalate tomcat8's permissions to root?
