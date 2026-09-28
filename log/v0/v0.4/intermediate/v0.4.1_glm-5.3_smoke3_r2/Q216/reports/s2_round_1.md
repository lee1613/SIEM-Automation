# s2 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=5_
**Scope:** index=botsv3 sourcetype=stream:dns (query, src_ip, _time) + sourcetype=stream:tcp (duration, flow_id, connection, dest) — NVM scope (syslog / cisconvmflowdata) excluded per task boundary.
**Insight:** NOT_FOUND (partial: endpoint identified, duration not computed)
**Candidate:** none   **Confidence:** 15

## Prior rounds
- Round 1: mapped feeds; keyword monero/xmr = 0 hits; found Coinhive Monero-mining DNS from a single endpoint (BSTOLL-L, 192.168.247.131); confirmed stream:tcp carries per-flow `duration`; did not reach the duration computation.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; stream:dns, stream:tcp present.
- keyword `monero` / `xmr` -> 0 hits anywhere (no field or value names it).
- osquery:results | stats count by name -> 38 scheduled queries, none miner-specific.
- stream:dns (query="*pool*" OR "*xmr*" OR "*monero*" OR "*coin*" OR "*hash*") | stats count by query -> coinhive.com (6) + ws001/ws005/ws011/ws014/ws019.coinhive.com (3 each); nothing else.
- stream:dns query="*coinhive*" | stats by src_ip -> exactly one src_ip: 192.168.247.131, window 1534772253.910–1534772319.701.
- stream:dns src_ip=192.168.247.131 | stats by query -> 670 rows; host = BSTOLL-L (mDNS BSTOLL-L.local); www.brewertalk.com 16x, 1534770442–1534773387.
- get_sourcetype_fields stream:tcp -> `duration`, `flow_id`, `connection` exist; 45.77.53.176:443 is the top connection (4,955 events).

### What it means
NOT_FOUND for the number. The Monero-generating endpoint is identified: BSTOLL-L (192.168.247.131) resolves coinhive.com and five ws00X.coinhive.com mining servers — Coinhive is browser-based Monero mining, and this is the only host in the dataset doing so. But the DNS window (65.8 s) is name resolution, not generation; the duration must be measured on stream:tcp flows (which carry a per-flow `duration` field) to the coinhive servers or to 45.77.53.176:443 — the exact 443 stream the NVM line ties to mining. I exhausted iterations before running that query, so no numeric candidate exists.

## Assumptions
- Coverage: stream:dns `query` — searched pool/xmr/monero/coin/hash -> coinhive only (VERIFIED). stream:tcp `duration`/`flow_id`/`connection` — fields confirmed to exist, flows NOT yet searched (UNVERIFIED). Dataset-wide keyword monero/xmr -> 0 events (VERIFIED).
- Selection: BSTOLL-L is the only src_ip resolving coinhive/ws00X.coinhive.com (VERIFIED — the coinhive search returned exactly one src_ip); no other endpoint showed mining-pool DNS.
- Premise: Coinhive = Monero generation (external, well-established). DNS resolution alone does not prove mining ran — the TCP flows to ws00X.coinhive.com would (UNVERIFIED).
- Premise: "for how many seconds" = duration of the mining session's flows — single-flow `duration` vs first-to-last span not yet fixed; the NVM line's 45.77.53.176:443 stream suggests a single long flow (UNVERIFIED).

## Ruled out
- Any feed naming monero/xmr directly — keyword search, 0 events.
- osquery:results miner-specific packs — none among the 38 query names.
- Mining-pool DNS other than coinhive — none in the keyword search.

## Open questions for SH
- Is the in-scope Monero generation the Coinhive browser mining on BSTOLL-L, and should duration be measured on flows to the ws00X.coinhive.com servers or on the 45.77.53.176:443 session the NVM line associates with mining?
- Should the answer be a single flow's `duration` field or the first-to-last span of the mining flows?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 2 result(s) this round returned only their first rows — `get_sourcetype_fields: {"sourcetype": "stream:tcp"}` (46 of 92 rows seen); `run_splunk_search: index=botsv3 sourcetype=stream:dns src_ip=192.168.247.131 | stats count min(_time) as firs…` (50 of 670 rows seen). A claim resting on them alone is UNVERIFIED._
