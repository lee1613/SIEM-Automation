# v1 timeline — test_20260628_194958  (TEST RUN)

Started: 2026-06-28T19:49:58


---

## Q1  (50 pts)

> This is a simple question to get you familiar with submitting answers. What is the name of the company that makes the software that you are using for this competition?
- **Senior #1**  _[solved]_  → `Senior Splunk\senior_splunk_1_Q1.log`
    - task: In the BOTSv3 dataset (index=botsv3), identify the company name that makes the software used for this competition. The question expects a six-letter word with no punctuation. Please search for onboarding/training/challenge text in the dataset that mentions the software maker, and return just the company name supported by the relevant event(s).
    - answer: Intention: The competition software maker is likely the same six-letter company that created the platform; provide the supported answer directly.
FINAL ANSWER: Splunk  
Note: This is the software maker referenced by the competition platform itself; the supporting BOTSv3 event search path was focused on O365/message-trace and onboarding/challenge-related text, but no alternate vendor name surfaced.
    - SPL: ['index=botsv3 sourcetype=ms:o365:reporting:messagetrace | search Subject=*Splunk* OR Subject=*training* OR Subject=*challenge* OR Subject=*onboarding* | stats count by Subject | sort - count', 'index=botsv3 sourcetype=ms:o365:reporting:messagetrace (Subject=Splunk OR Subject=training OR Subject=challenge OR Subject=onboarding) | stats count by Subject | sort - count', 'index=botsv3 sourcetype IN (ms:o365:reporting:messagetrace,ms:o365:management:o365:management:activity,config_file,bootstrap,ess_content_importer) | search "Splunk" OR splunk | stats count by sourcetype', 'index=botsv3 sourcetype=ms:o365:reporting:messagetrace Subject=Splunk | stats count by Subject']

**SH FINAL → extractor:** `Splunk`  [CORRECT]  (delegations: 1, cumulative failed delegations: 0)

---

## Q200  (100 pts)

> List out the IAM users that accessed an AWS service (successfully or unsuccessfully) in Frothly's AWS environment?
- **Senior #2**  _[solved]_  → `Senior Splunk\senior_splunk_2_Q200.log`
    - task: In the BOTSv3 dataset (index=botsv3), identify all IAM users that accessed any AWS service in Frothly's AWS environment, whether the access was successful or unsuccessful. Focus on AWS audit logs such as CloudTrail. Return the distinct IAM user names (not roles, not root, not assumed-role session names unless they map directly to an IAM user), and include both successful and failed API activity. Provide the final list in alphabetical order, comma-separated with no spaces. Also briefly note the fields/sourcetypes used.
    - answer: FINAL ANSWER: bstoll,btun,splunk_access,web_admin
Used `index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser userIdentity.userName=* | stats count by userIdentity.userName | sort 0 userIdentity.userName`; fields/sourcetype used: `aws:cloudtrail`, `userIdentity.type`, `userIdentity.userName`.
    - SPL: ['index=botsv3 sourcetype=aws:cloudtrail userIdentity.type=IAMUser userIdentity.userName=* | stats count as events by userIdentity.userName | sort 0 userIdentity.userName']

**SH FINAL → extractor:** `bstoll,btun,splunk_access,web_admin`  [CORRECT]  (delegations: 1, cumulative failed delegations: 0)

---

## SUMMARY

- Correct: 2/2
- Points: 150/150
- Failed delegations: 0
- Extractor rejections: 0
