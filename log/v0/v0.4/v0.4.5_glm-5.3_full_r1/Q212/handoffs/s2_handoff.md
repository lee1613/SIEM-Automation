# s2 - Q212 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=7_
**Scope:** sourcetype=symantec:ep:security:file (source=agt_security.tmp) + rival sweep of the 7 other symantec:ep:* feeds | fields: CIDS_Signature_ID, Begin_Time, End_Time, _time, Host_Name, signature

**Insight:** FOUND
**Candidate:** 30356   **Confidence:** 95

## Prior rounds
- R1 (prior senior, lost to transport): established 46 JSCoinminer events in symantec:ep:security:file, all BTUN-L, candidate signature IDs 30356/30358; risk:file and behavior:file held no miner; five SEP feeds left unsearched.

## This round
### What I ran
- get_sourcetype_fields security:file -> 46 events, Host_Name distinct=1 (BTUN-L), CIDS_Signature_ID 30356 (23) / 30358 (23); Begin_Time/End_Time are Aug 18 while _time is Aug 20.
- get_raw_events JSCoinminer -> raw lines carry "Begin: 2018-08-18 21:00:27,End: ..." — Begin_Time is the detection timestamp; _time is the SEPM dump time.
- `... | eval begin_epoch=strptime(Begin_Time,"%Y-%m-%d %H:%M:%S") | stats min(begin_epoch) min(Begin_Time) count by CIDS_Signature_ID | sort first_epoch` -> 30356 first at 2018-08-18 20:51:13 (epoch 1534596673), 30358 at 20:51:14 (epoch 1534596674); full 23-value Begin_Time lists per signature, read to end.
- `... | sort 0 begin_epoch | stats first(CIDS_Signature_ID) first(Begin_Time) earliest(begin_epoch) by CIDS_Signature_ID` -> identical: 30356 @ 20:51:13, 30358 @ 20:51:14.
- _time comparison by signature -> both share the same _time set starting 2018-08-20 21:37:40; _time is tied and is dump time.
- Rival sweep of the 7 other SEP feeds (agent, agt_system, behavior, packet, risk, scm_system, traffic) for coinminer/miner/crypto/coin -> 0 events.
- Completeness check `| stats count count(eval(isnull(CIDS_Signature_ID)))` -> 46 events, 0 missing CIDS, distinct sigs exactly [30356, 30358] (fieldsummary's "63" was an artifact).

### What it means
FOUND: Begin_Time is the SEP field that records when each detection actually occurred (Aug 18); _time only records when the agt_security.tmp dump was written (Aug 20) and is identical for both signatures, so it cannot order them. Ordering the 46 JSCoinminer events on Begin_Time with Splunk event-order functions (sort + first(), earliest(), min() — all agree) puts 30356 at 2018-08-18 20:51:13, one second ahead of 30358 (20:51:14). No other SEP feed contains any coin-miner detection, so no rival changes the answer. First seen signature ID = 30356.

## Ruled out
- 30358 as first seen — min(Begin_Time)=2018-08-18 20:51:14, one second after 30356's 20:51:13.
- _time as the ordering field — SEPM dump time (Aug 20 21:37:40+), tied between both signatures; represents log export, not detection.
- The 7 other SEP feeds as coin-miner sources — text sweep for coinminer/miner/crypto/coin returned 0 events.
- A third signature ID in security:file — isnull(CIDS_Signature_ID)=0 of 46; distinct sigs exactly [30356, 30358].

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._

_Premise updates refused by the runner:_
- p4 stays UNVERIFIED: its quote is in no result you ran - copy the query output that shows it word for word


## What I'd tell my replacement
- Retired because: end of question (turns)
- Scope I owned: sourcetypes=['symantec:ep:security:file', 'symantec:ep:risk:file', 'symantec:ep:behavior:file'] sources=[] fields=['signature_id', 'CIDS_Signature_ID', 'signature', 'Host_Name', 'Begin_Time', '_time', 'Intrusion_URL']
- Rounds worked: 1/3  (iterations: 11, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype IN ("symantec:ep:agent:file","symantec:ep:agt_system:file","symantec:ep:behavior:file","symantec:ep:packet:file","symantec:ep:risk:file","symantec:ep:scm_system:file","symantec:ep:traffic:file") (coinminer OR miner OR crypto OR coin)
| stats count by sourcetype signature CIDS_Signature_ID Risk_Name Event_Description
| sort - count
- index=botsv3 sourcetype="symantec:ep:*" NOT sourcetype="symantec:ep:security:file" (coinminer OR Coinminer OR miner OR Miner OR crypto OR coin)
| stats count by sourcetype signature CIDS_Signature_ID Risk_Name Event_Description
| sort - count
- index=botsv3 sourcetype=symantec:ep:security:file CIDS_Signature_ID!=*
| stats count dc(Host_Name) as hosts values(Host_Name) as host_names values(signature) as sigs values(Event_Description) as descs by _time
| stats count values(host_names) as all_hosts values(sigs) as all_sigs values(descs) as all_descs
- index=botsv3 sourcetype=symantec:ep:security:file CIDS_Signature_ID=*
| eval begin_epoch=strptime(Begin_Time,"%Y-%m-%d %H:%M:%S")
| sort 0 begin_epoch
| stats first(CIDS_Signature_ID) as first_seen_sig first(Begin_Time) as first_seen_time earliest(begin_epoch) as earliest_epoch by CIDS_Signature_ID
- index=botsv3 sourcetype=symantec:ep:security:file CIDS_Signature_ID=*
| eval begin_epoch=strptime(Begin_Time,"%Y-%m-%d %H:%M:%S")
| stats min(begin_epoch) as first_epoch min(Begin_Time) as first_begin_str max(Begin_Time) as last_begin_str values(Begin_Time) as all_begins count by CIDS_Signature_ID
| sort first_epoch
- index=botsv3 sourcetype=symantec:ep:security:file | eval t=strftime(_time,"%Y-%m-%d %H:%M:%S") | stats count values(t) as index_times min(Begin_Time) as first_begin by CIDS_Signature_ID
- index=botsv3 sourcetype=symantec:ep:security:file | stats count count(eval(isnull(CIDS_Signature_ID))) as events_missing_cids dc(CIDS_Signature_ID) as distinct_sigs values(CIDS_Signature_ID) as sigs
