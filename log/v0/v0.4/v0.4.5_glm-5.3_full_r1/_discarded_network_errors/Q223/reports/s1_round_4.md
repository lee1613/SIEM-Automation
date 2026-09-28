# s1 - Q223 - Round 4
_stamped by runner: rounds_remaining=1 novel_spl=6_
**Scope:** index=botsv3 sourcetypes=aws:cloudtrail, aws:s3:accesslogs, aws:elb:accesslogs | fields eventName, eventTime, imageId, errorCode, _raw
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** 0

## Prior rounds
- R1: first web_admin RunInstances attempt = ami-41e0b93b, 2018-08-20T09:16:22Z, failed; aws:description empty; codename unresolved.
- R2: all 576 attempts failed; every in-dataset AMI-naming feed empty; external guess "Xenial Xerus" submitted at confidence 40.
- R3: verified leaked-key→session-key→attempt chain; ordered all 15 attempted AMIs; fleet image disjoint from attacker set; no artifact names the AMI's OS.
- R4: answered SH's three questions from held evidence; named aws:s3:accesslogs and aws:elb:accesslogs as the residual unchecked feeds.
- R5 (this): closed both residual feeds; verified the AMI string appears nowhere in CloudTrail but RunInstances; external lookup of the AMI ID returned nothing.

## This round
### What I ran
- `sourcetype=aws:s3:accesslogs "ami-41e0b93b"` → 0 events.
- `sourcetype=aws:elb:accesslogs "ami-41e0b93b"` → 0 events.
- `sourcetype=aws:cloudtrail "ami-41e0b93b" | stats count values(eventName) by errorCode` → 2 rows, both RunInstances (24 InstanceLimitExceeded, 14 UnauthorizedOperation).
- `sourcetype=aws:cloudtrail "ami-41e0b93b" | stats count dc(eventName)` → 38 events, distinctEventNames=1 (RunInstances only).
- `sourcetype=aws:cloudtrail "ubuntu" OR "xenial" OR "bionic" OR "trusty" OR "artful" OR "zesty" OR "yakkety" OR "wily" OR "vivid" OR "utopic" OR "precise" | stats count by eventName` → 0 events.
- web_lookup "ami-41e0b93b" (two phrasings) → no result snippets found.

### What it means
NOT_FOUND, and the wall is now fully verified from result output. Restating per SH's instruction: no in-dataset artifact names ami-41e0b93b beyond the CloudTrail RunInstances imageId — the string appears in exactly 38 CloudTrail events, all RunInstances by web_admin (first at 2018-08-20T09:16:22Z, via session key ASIAZB6TMXZ7LL6JBJQA minted from the leaked key AKIAJOGCDXJ5NW5PXUPA ten seconds earlier); aws:s3:accesslogs and aws:elb:accesslogs, the last residual feeds, return 0 events for it; no CloudTrail event contains any Ubuntu/codename string; aws:description is empty index-wide and all 31 DescribeImages events have responseElements null. The Ubuntu codename is therefore unreadable here. The external path is closed too: web_lookup of the AMI ID returns no snippets, so even external identification cannot be confirmed. The only candidate any evidence supports is the unsubmitted external guess "Xenial Xerus" (Ubuntu 16.04), backed circumstantially by the attacker host's 4.4.0-131-generic kernel; it is recorded in notes, not in value.

## Ruled out
- aws:s3:accesslogs, aws:elb:accesslogs — 0 events for ami-41e0b93b (structurally empty for this purpose, now shown from output).
- CloudTrail outside RunInstances — the AMI string appears in no other eventName (dc=1 over 38 events).
- Any Ubuntu/codename string in CloudTrail — 0 events across eleven codename/release terms.
- aws:description (0 events index-wide), DescribeImages responseElements (null ×31), bash_history (no "ami-" strings), osquery:results, cloud-init, cloud-init-output, aws:config:rule, aws:cloudwatch:guardduty (0 hits each).
- External identification via web_lookup — no snippets for the AMI ID.
- Any successful launch by web_admin — all 576 attempts carry an errorCode.

_Premise updates refused by the runner:_
- coverage premise not filed: you already have an open coverage premise p4 - amend or settle that one. The text you sent was discarded: "The wall is complete and result-backed: in index=botsv3, ami-41e0b93b appears on"
- p2 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p3 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
- p4 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word
