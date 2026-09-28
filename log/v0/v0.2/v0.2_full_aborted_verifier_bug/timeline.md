# v1 timeline — run_1.2  (FULL RUN)

Started: 2026-07-08T08:09:36


---

## Q200  (100 pts)

> List out the IAM users that accessed an AWS service (successfully or unsuccessfully) in Frothly's AWS environment?
- **Senior #1**  _[failed]_  task=1
    - subquestion: In Splunk index=botsv3, search the August 2018 timeframe for Frothly AWS audit data and determine which sourcetype(s) contain AWS API access records for the Frothly AWS environment. Prioritize CloudTr
    - answer: Intention: The errorCode search returned no results, meaning all CloudTrail events in this dataset were successful API calls. I now have a complete picture. Let me verify there are no other AWS-related sourcetypes I might have missed by searching for "s3" or "iam" keywords.
→ call search_keyword<arg_key>keyword</arg_key><arg_value>s3</arg_value></tool_call>
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail | stats count by userIdentity.type, userIdentity.userName, userIdentity.accountId | sort -count', 'index=botsv3 sourcetype=aws:cloudtrail | stats count by userIdentity.principalId, userIdentity.arn, userIdentity.invokedBy | sort -count | head 20', 'index=botsv3 sourcetype=aws:cloudtrail | stats count by awsRegion, recipientAccountId | sort -count', 'index=botsv3 sourcetype=aws:cloudtrail | stats count by sourceIPAddress, userAgent | sort -count | head 15']
- **Senior #2**  _[solved]_  task=2
    - subquestion: In Splunk index=botsv3, search the August 2018 timeframe in Frothly AWS audit logs for all AWS service access attempts, successful or unsuccessful, and extract every distinct IAM user involved. Use Cl
    - answer: I now have complete, verified results. The query returned exactly 4 distinct IAM users from CloudTrail records where `userIdentity.type=IAMUser`, excluding all AssumedRole, AWSService, and other non-user principals.

---

## FINAL ANSWER

**4 distinct IAM users** accessed AWS services in the Frothly CloudTrail audit logs (August 2018):

| # | Username | ARN | Events | Services Accessed | Error Cod
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser | stats count as event_count, dc(eventSource) as distinct_services, values(eventSource) as eventSources, values(eventName) as eventNames, values(errorCode) as errorCodes, values(errorMessage) as errorMessages, values(userIdentity.arn) as userArn, values(sourceIPAddress) as sourceIPs by userIdentity.userName | sort userIdentity.userName', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser | stats count, dc(eventSource) as services_accessed, values(eventSource) as eventSources, values(eventName) as eventNames, values(errorCode) as errorCodes, values(userIdentity.arn) as userArn, values(sourceIPAddress) as sourceIPs by userIdentity.userName | sort userIdentity.userName']
- **Senior #3**  _[solved]_  task=3
    - subquestion: Given [Task-1 (failed): Intention: The errorCode search returned no results, meaning all CloudTrail events in this dataset were successful API calls. I now have a complete picture. Let me verify there
    - answer: The query returned exactly 4 distinct IAM users from CloudTrail records where `userIdentity.type=IAMUser`, with no filtering on success/failure — all events are included regardless of outcome.

The 4 users, sorted alphabetically and in lowercase:
1. **bstoll** — 615 events
2. **btun** — 73 events
3. **splunk_access** — 4,091 events
4. **web_admin** — 646 events

FINAL ANSWER: bstoll,btun,splunk_ac
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser | stats count by userIdentity.userName | sort userIdentity.userName']

---

## ↩ Resumed: 2026-07-08T08:58:34


---

## Q200  (100 pts)

> List out the IAM users that accessed an AWS service (successfully or unsuccessfully) in Frothly's AWS environment?

**SH FINAL → extractor:** `bstoll,btun,splunk_access,web_admin`  [CORRECT]  (delegations: 0, cumulative failed delegations: 0)

  SH tokens [Q200]: input=2,003  cached=0  output=33  est=$0.0055

---

## Q201  (100 pts)

> What field would you use to alert that AWS API activity have occurred without MFA (multi-factor authentication)?
- **Senior #1**  _[partial]_  task=1
    - subquestion: In Splunk index=botsv3, search the August 2018 Frothly AWS CloudTrail logs using sourcetype=aws:cloudtrail and inspect the raw JSON structure of representative API events for confirmed IAM users bstol
    - answer: ## PARTIAL ANSWER

Based on raw JSON event inspection across all four confirmed IAM users (bstoll, btun, splunk_access, web_admin) in `aws:cloudtrail`, I identified **two candidate JSON paths related to MFA status**:

### 1. `userIdentity.sessionContext.attributes.mfaAuthenticated`
- **Present in:** All four users (bstoll: 611 events, btun: 73, splunk_access: 45, web_admin: 637)
- **Value:** `"fal
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName=web_admin | stats count by userIdentity.userName, userIdentity.type, userIdentity.sessionContext.attributes.mfaAuthenticated', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName IN (bstoll, btun, splunk_access, web_admin) | stats count by userIdentity.userName, userIdentity.sessionContext.attributes.mfaAuthenticated', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName IN (bstoll, btun, splunk_access, web_admin) additionalEventData.MFAUsed=* | stats count by userIdentity.userName, additionalEventData.MFAUsed', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName IN (bstoll, btun, splunk_access, web_admin) | eval has_sessionContext=if(isnull(userIdentity.sessionContext), "no", "yes") | stats count by userIdentity.userName, has_sessionContext, userIdentity.sessionContext.attributes.mfaAuthenticated', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName=web_admin userIdentity.sessionContext.attributes.mfaAuthenticated=* | head 1 | table _raw', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName=web_admin userIdentity.sessionContext.attributes.mfaAuthenticated=* | head 1 | stats values(_raw) as raw_event', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName=splunk_access userIdentity.sessionContext.attributes.mfaAuthenticated=* | head 1 | stats values(_raw) as raw_event', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName=bstoll additionalEventData.MFAUsed=* | head 1 | stats values(_raw) as raw_event']
- **Senior #2**  _[solved]_  task=2
    - subquestion: In Splunk index=botsv3, search the August 2018 Frothly AWS CloudTrail logs using sourcetype=aws:cloudtrail and determine which field is appropriate for alerting when AWS API activity occurred without 
    - answer: Now I have all the evidence needed. Let me compile the findings.

## Summary of Investigation

I investigated two MFA-related fields in the `aws:cloudtrail` sourcetype:

### Field 1: `userIdentity.sessionContext.attributes.mfaAuthenticated`
- **JSON path in raw event:**
  ```json
  "userIdentity": {
    "sessionContext": {
      "attributes": {
        "mfaAuthenticated": "false",
        "creatio
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName IN (bstoll, btun, splunk_access, web_admin) | stats count as total_events, count(userIdentity.sessionContext.attributes.mfaAuthenticated) as mfa_auth_count, values(userIdentity.sessionContext.attributes.mfaAuthenticated) as mfa_auth_values, count(additionalEventData.MFAUsed) as mfa_used_count, values(additionalEventData.MFAUsed) as mfa_used_values by userIdentity.userName', 'index=botsv3 sourcetype=aws:cloudtrail | stats count by userIdentity.sessionContext.attributes.mfaAuthenticated', 'index=botsv3 sourcetype=aws:cloudtrail | stats count by additionalEventData.MFAUsed']
- **Senior #3**  _[solved]_  task=3
    - subquestion: Given [Task-1 (partial): ## PARTIAL ANSWER

Based on raw JSON event inspection across all four confirmed IAM users (bstoll, btun, splunk_access, web_admin) in `aws:cloudtrail`, I identified **two cand
    - answer: The evidence is definitive. Comparing the two candidate fields:

| Field | Event Count | Value(s) | Coverage |
|---|---|---|---|
| `userIdentity.sessionContext.attributes.mfaAuthenticated` | 2,155 | `"false"` | Present across all IAM users and AssumedRole sessions |
| `additionalEventData.MFAUsed` | 4 | `"No"` | Only in specific console-login-type events |

The raw JSON confirms the exact nested s
    - SPL: []

**SH FINAL → extractor:** `userIdentity.sessionContext.attributes.mfaAuthenticated`  [CORRECT]  (delegations: 3, cumulative failed delegations: 0)

  SH tokens [Q201]: input=243,545  cached=1,792  output=10,370  est=$0.2499

---

## Q202  (500 pts)

> What is the processor number used on the web servers?
- **Senior #4**  _[partial]_  task=1
    - subquestion: In Splunk index=botsv3 for the August 2018 Frothly environment, identify which hosts are the web servers. Use likely web-related sourcetypes and evidence such as apache, nginx, IIS, web access logs, s
    - answer: PARTIAL ANSWER: The Frothly web servers are **5 hosts**:

1. **gacrux.i-0920036c8ca91e501** (172.16.0.178)
2. **gacrux.i-0cc93bade2b3cba63** (172.16.0.145)
3. **gacrux.i-06fea586f3d3c8ce8** (172.16.0.127)
4. **gacrux.i-09cbc261e84259b54** (172.16.0.13)
5. **hoth** (192.168.9.30)

**Sourcetypes establishing they are web servers:**

| Sourcetype | Evidence |
|---|---|
| `access_combined` | Apache ac
    - SPL: ['index=botsv3 sourcetype=access_combined | stats count by host source', 'index=botsv3 sourcetype=unix:service (app=httpd OR app=apache2 OR app=apache OR app=nginx) | stats count by host app', 'index=botsv3 sourcetype=unix:service host=hoth | stats count by app', 'index=botsv3 sourcetype=stream:http | stats count by host | sort -count', 'index=botsv3 sourcetype=openports (host=hoth OR host=gacrux*) | stats count by host dest_port | sort host, dest_port', 'index=botsv3 sourcetype=netstat (host=hoth OR host=gacrux*) | stats count by host local_port | sort host, local_port', 'index=botsv3 sourcetype=script:listeningports (host=hoth OR host=gacrux*) | stats count by host local_port | sort host, local_port', 'index=botsv3 sourcetype=aws:elb:accesslogs | rex field=_raw "\\s(?P<backend_ip>\\d+\\.\\d+\\.\\d+\\.\\d+):\\d+\\s" | stats count by backend_ip | sort backend_ip', 'index=botsv3 sourcetype=aws:elb:accesslogs | rex field=_raw "^[^\\s]+\\s+[^\\s]+\\s+[^\\s]+\\s+(?P<backend_ip>\\d+\\.\\d+\\.\\d+\\.\\d+):\\d+\\s" | stats count by backend_ip | sort backend_ip', 'index=botsv3 sourcetype=aws:elb:accesslogs | rex field=_raw "^[^\\s]+\\s[^\\s]+\\s[^\\s]+\\s[^\\s]+\\s(?P<backend_ip>\\d+\\.\\d+\\.\\d+\\.\\d+):\\d+\\s" | stats count by backend_ip | sort backend_ip', 'index=botsv3 sourcetype=aws:description (172.16.0.13 OR 172.16.0.127 OR 172.16.0.145 OR 172.16.0.178) | stats count by host', 'index=botsv3 sourcetype=stream:http (dest_ip=172.16.0.13 OR dest_ip=172.16.0.127 OR dest_ip=172.16.0.145 OR dest_ip=172.16.0.178) | stats count by host dest_ip | sort dest_ip', 'index=botsv3 sourcetype=stream:http host=hoth | stats count by dest_ip | sort -count', 'index=botsv3 sourcetype=access_combined host=hoth | stats count by source uri_path | sort -count']
- **Senior #5**  _[solved]_  task=2
    - subquestion: In Splunk index=botsv3 for the August 2018 Frothly environment, search host inventory, endpoint telemetry, osquery, hardware, system information, or similar sourcetypes for CPU model details on server
    - answer: I now have a complete picture across three sourcetypes. Let me compile the final results.

---

## FINAL ANSWER

Three sourcetypes in `index=botsv3` expose CPU processor model strings exactly as recorded:

---

### 1. `sourcetype=hardware` (Linux/Unix TA — server hosts)

**Field: `cpu_type`** — contains the full processor model string.

| Host | `cpu_type` | `cpu_count` | `cpu_cores` | `cpu_mhz` |
    - SPL: ['index=botsv3 sourcetype=hardware | stats count by host cpu_type cpu_count cpu_cores cpu_freq cpu_mhz', 'index=botsv3 sourcetype=winhostmon (CPU OR processor OR Processor) | stats count by Type', 'index=botsv3 sourcetype=winhostmon Type=Processor | stats count by host', 'index=botsv3 sourcetype=winhostmon Type=Processor | stats count by host Name Manufacturer ClockSpeedMHz NumberOfCores NumberOfProcessors', 'index=botsv3 sourcetype=osquery:results | stats count by name', 'index=botsv3 sourcetype=osquery:results name=pack_hardware-monitoring_cpuid | stats count by hostIdentifier columns.name columns.model columns.stepping columns.family', 'index=botsv3 sourcetype=osquery:results name=system_info | stats count by hostIdentifier columns.hostname columns.cpu_brand columns.physical_memory', 'index=botsv3 sourcetype=osquery:results name=pack_hardware-monitoring_cpuid | stats count by hostIdentifier columns.feature columns.value']
- **Senior #6**  _[partial]_  task=3
    - subquestion: Given [Task-1 (partial): PARTIAL ANSWER: The Frothly web servers are **5 hosts**:

1. **gacrux.i-0920036c8ca91e501** (172.16.0.178)
2. **gacrux.i-0cc93bade2b3cba63** (172.16.0.145)
3. **gacrux.i-06fea
    - answer: ## PARTIAL ANSWER

**CPU model string found for 3 of 5 web servers — all identical:**

`Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz`

| Host | Sourcetype | Field | Value |
|---|---|---|---|
| gacrux.i-06fea586f3d3c8ce8 | `hardware` | `cpu_type` | Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz |
| gacrux.i-09cbc261e84259b54 | `hardware` | `cpu_type` | Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz |
| gacrux.i
    - SPL: ['index=botsv3 sourcetype=osquery:results | stats count by name | sort -count', 'index=botsc3 sourcetype=osquery:results name="pack_hardware-monitoring_cpuid" | stats count by host', 'index=botsv3 sourcetype=osquery:results name="pack_hardware-monitoring_cpuid" | stats count by host', 'index=botsv3 sourcetype=osquery:results name="system_info" | stats count by host', 'index=botsv3 sourcetype=osquery:results name="system_profile" | stats count by host', 'index=botsv3 sourcetype=osquery:results name="system_info" | stats count by host, columns.cpu_brand, columns.hostname', 'index=botsv3 (host=hoth OR host="gacrux.i-0920036c8ca91e501") "Xeon" | stats count by host, sourcetype', 'index=botsv3 sourcetype=osquery:results (host=hoth OR host="gacrux.i-0920036c8ca91e501") "Xeon" | stats count by host, name, columns.cpu_brand', 'index=botsv3 sourcetype=osquery:results (host=hoth OR host="gacrux.i-0920036c8ca91e501") "Intel" | stats count by host, name']
- **Verifier #7**  _[refuted]_
    - candidate: Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz
    - result: The evidence is clear. The CloudTrail logs show exactly 4 IAM users (userIdentity.type=IAMUser) that accessed AWS services:

1. **bstoll** — 615 events
2. **btun** — 73 events
3. **splunk_access** — 4091 events
4. **web_admin** — 646 events

The candidate answer "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz" is a CPU model string — completely unrelated to IAM usernames. It is definitively wrong.

The

**SH FINAL → extractor:** `bstoll,btun,splunk_access,web_admin`  [WRONG]  (delegations: 4, cumulative failed delegations: 0)

  SH tokens [Q202]: input=1,034,129  cached=4,608  output=20,032  est=$0.9515

---

## Q203  (100 pts)

> Bud accidentally makes an S3 bucket publicly accessible. What is the event ID of the API call that enabled public access?
- **Senior #8**  _[partial]_  task=1
    - subquestion: In Splunk index=botsv3 sourcetype=aws:cloudtrail for the August 2018 Frothly AWS environment, search for all S3 API calls made by IAM user `btun` (Bud) using fields such as `userIdentity.userName`, `e
    - answer: PARTIAL ANSWER: IAM user `btun` (Bud) made **zero S3 API calls** in the BOTSv3 CloudTrail data. All 73 of btun's CloudTrail events are EC2, autoscaling, monitoring, ELB, and IAM operations — no S3 events whatsoever. The only S3 bucket change events that could affect public accessibility in the entire dataset are **2 `PutBucketAcl` events made by `bstoll`** (not btun), both on bucket `frothlywebcod
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName=btun eventSource=s3.amazonaws.com | stats count by eventName, eventID, eventTime', 'index=botsv3 sourcetype=aws:cloudtrail | top limit=50 userIdentity.userName', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName="btun" | top limit=50 eventSource', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName="btun" | stats count by eventSource, eventName', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com | stats count by userIdentity.userName, eventName | sort -count', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com eventName=PutBucketAcl | stats eventTime, eventID, requestParameters, responseElements by userIdentity.userName, eventName', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com eventName=PutBucketAcl | table _time, eventTime, eventID, userIdentity.userName, eventName, requestParameters, responseElements', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com eventName=PutBucketAcl | stats values(eventTime) as eventTime, values(userIdentity.userName) as userName, values(eventName) as eventName, values(requestParameters) as requestParameters, values(responseElements) as responseElements by eventID', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com (eventName=PutBucketPolicy OR eventName=DeleteBucket OR eventName=CreateBucket OR eventName=PutBucketWebsite OR eventName=PutBucketCors OR eventName=DeleteBucketPolicy OR eventName=PutBucketLogging OR eventName=PutBucketVersioning OR eventName=PutBucketLifecycle OR eventName=PutBucketReplication OR eventName=PutBucketEncryption OR eventName=PutBucketTagging OR eventName=PutBucketNotification OR eventName=PutBucketRequestPayment) | stats count by eventName, userIdentity.userName', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com | stats count by userIdentity.userName, userIdentity.type', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com | stats count by eventName | sort -count']
- **Senior #9**  _[solved]_  task=2
    - subquestion: In Splunk index=botsv3 sourcetype=aws:cloudtrail for the August 2018 Frothly AWS environment, identify any S3 bucket configuration or permission change events that resulted in a bucket becoming public
    - answer: The second raw event is the definitive answer. It contains ACL grants to `http://acs.amazonaws.com/groups/global/AllUsers` (the public "AllUsers" group) with both **READ** and **WRITE** permissions — explicitly making the bucket publicly accessible.

---

**FINAL ANSWER:**

| Field | Value |
|---|---|
| **Responsible IAM User** | `bstoll` |
| **Bucket Name** | `frothlywebcode` |
| **eventName** | 
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail eventName IN ("PutBucketAcl","PutBucketPolicy","PutObjectAcl","CreateBucket","PutBucketWebsite","DeleteBucketPolicy","DeleteBucketAcl","PutBucketCors","PutBucketLogging","PutBucketReplication","PutBucketVersioning","PutBucketLifecycle","PutBucketEncryption","PutBucketTagging","PutPublicAccessBlock") | stats count by eventName, userIdentity.userName, requestParameters.bucketName, eventID']
- **Senior #10**  _[failed]_  task=3
    - subquestion: Given [Task-1 (partial): PARTIAL ANSWER: IAM user `btun` (Bud) made **zero S3 API calls** in the BOTSv3 CloudTrail data. All 73 of btun's CloudTrail events are EC2, autoscaling, monitoring, ELB, and I
    - answer: Intention: Let me search for "Bud" in the dataset to find identity mapping evidence linking Bud to a specific IAM user.
→ call search_keyword<arg_key>keyword</arg_key><arg_value>Bud</arg_value></tool_call>
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail eventName=PutBucketAcl | stats values(eventID) as eventID, values(userIdentity.arn) as user_arn, values(requestParameters.bucketName) as bucket_name, values(eventTime) as event_time by eventName', 'index=botsv3 sourcetype=aws:cloudtrail eventName=PutBucketAcl | stats values(eventID) as eventID, values(eventTime) as event_time, count(eval(match(_raw, "AllUsers"))) as has_allusers, count(eval(match(_raw, "WRITE"))) as has_write by eventTime', 'index=botsv3 sourcetype=aws:cloudtrail eventName=PutBucketAcl "AllUsers" | stats values(eventID) as eventID, values(eventTime) as event_time', 'index=botsv3 sourcetype=aws:cloudtrail eventName=PutBucketAcl eventID="9a33d8df-1e16-4d58-b36d-8e80ce68f8a3" | stats values(eventID) as eventID, count(eval(match(_raw, "AllUsers"))) as has_allusers', 'index=botsv3 sourcetype=aws:cloudtrail userIdentity.userName=btun | stats count by userIdentity.userName, userIdentity.arn']

**SH FINAL → extractor:** `ab45689d-69cd-41e7-8705-5350402cf7ac`  [CORRECT]  (delegations: 3, cumulative failed delegations: 1)

  SH tokens [Q203]: input=174,827  cached=8,192  output=7,854  est=$0.1812

---

## Q204  (100 pts)

> What is the name of the S3 bucket that was made publicly accessible?

**SH FINAL → extractor:** `frothlywebcode`  [CORRECT]  (delegations: 0, cumulative failed delegations: 1)

  SH tokens [Q204]: input=6,608  cached=0  output=23  est=$0.0169

---

## Q205  (100 pts)

> What is the name of the text file that was successfully uploaded into the S3 bucket while it was publicly accessible?
- **Senior #11**  _[partial]_  task=1
    - subquestion: In Splunk index=botsv3 sourcetype=aws:cloudtrail for the August 2018 Frothly AWS environment, search for all S3 object upload events to bucket `frothlywebcode` after the public-access-enabling `PutBuc
    - answer: PARTIAL ANSWER: No S3 object upload events (PutObject, CompleteMultipartUpload, etc.) exist in `aws:cloudtrail` for the `frothlywebcode` bucket. CloudTrail only recorded bucket-level management events (GetBucket*, PutBucketAcl) — S3 data/object-level event logging was not enabled. The only post-PutBucketAcl S3 CloudTrail events are read operations (GetBucketAcl, GetBucketPolicy, GetBucketCors, etc
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail eventID=ab45689d-69cd-41e7-8705-5350402cf7ac | stats values(eventName) as eventName values(eventTime) as eventTime values(requestParameters.bucketName) as bucketName values(sourceIPAddress) as sourceIP values(userIdentity.userName) as userName values(userIdentity.arn) as userArn', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com requestParameters.bucketName=frothlywebcode | stats count by eventName | sort -count', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com (eventName=PutObject OR eventName=CompleteMultipartUpload OR eventName=CopyObject OR eventName=CreateMultipartUpload OR eventName=UploadPart OR eventName=POST OR eventName=PUT) | stats count by eventName | sort -count', 'index=botsv3 sourcetype=aws:s3:accesslogs bucket=frothlywebcode | stats count by operation | sort -count', 'index=botsv3 sourcetype=aws:s3:accesslogs | stats count by bucket operation | sort -count', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com | stats count by eventName | sort -count', 'index=botsv3 sourcetype=stream:http (frothlywebcode OR s3.amazonaws.com) | stats count by http_method uri_path | head 20', 'index=botsv3 sourcetype=stream:http (http_method=PUT OR http_method=POST) | stats count by http_method uri_host uri_path | head 30', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com requestParameters.bucketName=frothlywebcode eventTime>\\"2018-08-20T13:01:46Z\\" | stats count by eventName eventTime eventID sourceIPAddress userIdentity.userName | sort eventTime', 'index=botsv3 sourcetype=bash_history frothlywebcode | stats count by _time host | sort -_time', 'index=botsv3 sourcetype=bash_history s3-upload.py | stats count by _raw | head 10']
- **Senior #12**  _[partial]_  task=2
    - subquestion: In Splunk index=botsv3 sourcetype=aws:cloudtrail for the August 2018 Frothly AWS environment, identify any uploads to bucket `frothlywebcode` during the period when it was publicly accessible that res
    - answer: PARTIAL ANSWER: The `frothlywebcode` bucket was made publicly accessible (READ+WRITE for AllUsers) via `PutBucketAcl` by user `bstoll` from IP `107.77.212.175` at **2018-08-20T13:01:46Z**, and public access was removed at **2018-08-20T13:57:54Z** (approximately 56 minutes of public access). There are **158 S3 access log events** in `sourcetype=aws:s3:accesslogs` that mention "frothlywebcode", whic
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com requestParameters.bucketName=frothlywebcode | stats count by eventName', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com eventName=PutObject | stats count by eventName, requestParameters.bucketName, requestParameters.key', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com | stats count by eventName', 'index=botsv3 sourcetype=aws:cloudtrail eventSource=s3.amazonaws.com eventName=PutBucketAcl | stats count by eventTime, eventName, requestParameters.bucketName, requestParameters, userIdentity.userName, sourceIPAddress', 'index=botsv3 sourcetype=aws:cloudtrail frothlywebcode | stats count by eventName, eventTime', 'index=botsv3 sourcetype=aws:s3:accesslogs bucket_name=frothlywebcode | stats count by operation, http_status', 'index=botsv3 sourcetype=aws:s3:accesslogs frothlywebcode | stats count', 'index=botsv3 sourcetype=aws:s3:accesslogs frothlywebcode | stats count by operation, http_status']
- **Senior #13**  _[solved]_  task=3
    - subquestion: Given [Task-1 (partial): PARTIAL ANSWER: No S3 object upload events (PutObject, CompleteMultipartUpload, etc.) exist in `aws:cloudtrail` for the `frothlywebcode` bucket. CloudTrail only recorded bucke
    - answer: I now have all 4 PUT.OBJECT events for the `frothlywebcode` bucket. Let me analyze them against the public access window (13:01:46Z to 13:57:54Z):

1. **13:02:44Z** — `OPEN_BUCKET_PLEASE_FIX.txt` — HTTP **200** (success) — anonymous, IP 52.66.146.128, Boto3/1.7.62 ✅ During public window
2. **13:04:17Z** — `frothly_html_memcached.tar.gz` — HTTP **200** (success) — anonymous, IP 35.182.246.222, Boto
    - SPL: ['index=botsv3 sourcetype=aws:s3:accesslogs frothlywebcode "REST.PUT.OBJECT" | stats count by _time, _raw', 'index=botsv3 sourcetype=aws:s3:accesslogs frothlywebcode "REST.PUT.OBJECT" | table _time _raw', 'index=botsv3 sourcetype=aws:s3:accesslogs frothlywebcode "REST.PUT.OBJECT" | stats values(_raw) as raw_event by _time']

**SH FINAL → extractor:** `OPEN_BUCKET_PLEASE_FIX.txt`  [CORRECT]  (delegations: 3, cumulative failed delegations: 1)

  SH tokens [Q205]: input=428,949  cached=12,288  output=12,977  est=$0.4090

---

## Q206  (100 pts)

> What is the size (in megabytes) of the .tar.gz file that was successfully uploaded into the S3 bucket while it was publicly accessible?
- **Senior #14**  _[failed]_  task=1
    - subquestion: In Splunk index=botsv3 for the August 2018 Frothly environment, search the S3 access evidence for the successful upload of `frothly_html_memcached.tar.gz` into bucket `frothlywebcode` during the publi
    - answer: 
    - SPL: []
