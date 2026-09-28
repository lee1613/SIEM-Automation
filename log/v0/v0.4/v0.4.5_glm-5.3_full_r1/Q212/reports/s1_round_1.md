# s1 - Q212 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=4_
**Scope:** sourcetype=symantec:ep:security:file, symantec:ep:risk:file, symantec:ep:behavior:file | fields: signature_id, CIDS_Signature_ID, signature, Host_Name, Begin_Time, _time
**Insight:** NOT_FOUND (candidates narrowed to two; event-order computation not yet run)
**Candidate:** none — the answer is one of {30356, 30358}, undetermined

## Prior rounds
Round 1 (this round): identified SEP feeds, located the coin miner threat, narrowed signature IDs to two.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; 8 symantec:ep:* feeds exist.
- get_sourcetype_fields symantec:ep:risk:file -> 1 event: Backdoor.PsEmpire on BGIST-L, 2018-08-20 09:58:20. Not a coin miner.
- get_sourcetype_fields symantec:ep:security:file -> 46 events, all Host_Name=BTUN-L, CIDS_Signature_ID 30356 (23) / 30358 (23), strings "Web Attack: JSCoinminer Download 6/8", SubIDs 70471/70481, src 54.67.127.227 (brewertalk.com), action=blocked, user=BillyTun.
- get_sourcetype_fields symantec:ep:behavior:file -> 2192 application-control events (Block scripts, Prevent modification of system files), 5 hosts, no coin-miner signature.
- `sourcetype=symantec:ep:security:file | stats count by signature, signature_id, Host_Name` -> 2 rows: 30356/23/BTUN-L, 30358/23/BTUN-L.
- `NOT CIDS_Signature_ID=*` -> 0 events; `stats count, dc(signature_id)` -> 46 events, 2 SIDs.
- Wildcard search across all symantec:ep:* feeds for "coinminer" -> rejected by the tool; agent:file, agt_system:file, packet:file, scm_system:file, traffic:file remain unsearched for that literal.

### What it means
The coin miner threat in SEP data is the JSCoinminer web-attack IDS detections, entirely on BTUN-L. Exactly two signature IDs exist — 30356 and 30358 — with perfectly symmetric counts (23/23 overall, 19/19 Edge, 4/4 Chrome), so nothing in the aggregates distinguishes which was first seen. The event-order query (sort by time, take first) was not run before tool withdrawal, so no single value can be honestly submitted.

## Ruled out
- BSTOLL-L (carried lead) as the coin-miner endpoint — no SEP coin-miner detections on it; security:file is BTUN-L only, risk:file is BGIST-L only, behavior:file is app-control only.
- symantec:ep:risk:file — its only event is Backdoor.PsEmpire, not a coin miner.
- symantec:ep:behavior:file — application-control events only, no miner signatures.
- Count-based inference between 30356/30358 — symmetric everywhere.

## Next step
`index=botsv3 sourcetype=symantec:ep:security:file signature="*Coinminer*" | sort 0 _time | head 1 | table _time Begin_Time signature_id signature Intrusion_URL`, cross-checked with `| stats first(signature_id), last(signature_id), min(Begin_Time)`. Note: only 2 distinct _time values exist (13:46:32 = 38 events, 14:01:32 = 8) vs 15 distinct Begin_Times from 2018-08-18 20:51:22 — the ordering basis matters and is flagged to SH.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
