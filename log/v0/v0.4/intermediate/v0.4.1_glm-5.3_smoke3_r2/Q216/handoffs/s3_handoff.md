# s3 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=10_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields: sa, da, sp, dp, fss, fes, fst, fet, pn, ppn, ph, ibc, obc, dh, mnl, mhl
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 75

## Prior rounds
- R1: Opened NVM feed; found the sole dp=3333 flow (192.168.70.186→45.77.53.176, powershell.exe, fss=1534762025, fes=1534762137); computed 112 by hand; flagged broader-:443-set alternative (7,070 span) as UNVERIFIED.

## This round
### What I ran
- Text search (monero OR stratum OR pool OR miner OR xmr OR cryptonight) over all NVM → 4 events, all false positives (pool.adizio.com/pool.admedo.com, BruceGist's Edge on 192.168.105.214).
- All 22 dp values enumerated and read → only 3333 is a mining port; other rare ports belong to hdoor.exe/CrashPlan/putty/internal svchost on unrelated hosts.
- sa=192.168.70.186 by dp → 443/53/80/67/9997/5353/3333(×1).
- ph=D3F8FADE…6677 (the :3333 binary) → 1 flow on :3333 + 3,621 on :443, same IP.
- :443 set by sa/ph → spans TWO endpoints: 192.168.70.186 (3,814) and 192.168.24.128 (1,015), same binary hash.
- :443 timing vs :3333 window → 1,485 before, 78 overlapping, 2,251 after.
- Reverse direction (sp=3333 OR da=192.168.70.186) → no mining flows.
- `dp=3333 … | eval duration=fes-fss | stats values(duration)` → **112** (in-tool).

### What it means
The only NVM field value feed-wide that identifies Monero is dp=3333; no text, hostname, or module identifier exists. That sole flow's duration, computed in-tool, is 112 seconds.

## Assumptions
- Coverage: Monero can appear in NVM via (a) port 3333 — searched feed-wide, 1 flow; (b) text in any field — searched, 4 false positives only; (c) another mining port — all 22 dp values read, none; (d) reverse direction — none. VERIFIED.
- Selection: "the endpoint" = 192.168.70.186, sole owner of the :3333 flow; 192.168.24.128 shares the :443 channel but owns no :3333 flow. VERIFIED.
- Metric definition: duration = fes−fss on the Monero-identified flow. VERIFIED: the :443 set carries no Monero identifier in NVM (dh="Unknown", mnl/mhl empty) and is not endpoint-specific (shared binary across two endpoints), so it cannot be "the endpoint's Monero generation" per this feed.
- fss/fes are flow start/end epochs. VERIFIED (fst/fet match).

## Ruled out
- 7,070 (broader :443 span): no Monero identifier in NVM; shared with 192.168.24.128 (same ph), contradicting singular "the endpoint"; :3333 sits mid-window (78 :443 flows overlap it), so the sets are concurrent channels, not one activity; a span also counts idle gaps, not generation.
- 192.168.24.128, 192.168.105.214: no :3333 flow.
- Any other port/destination as mining: all 22 dp values and 192.168.70.186's full port list read.

## Open questions for SH
- None — the metric-definition premise is settled inside NVM; 112 stands.

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_field_values: {"field": "dp", "source": "cisconvmflowdata", "top_n": 15}` (15 of 22 rows seen). A claim resting on them alone is UNVERIFIED._


## What I'd tell my replacement
- Retired because: Done on substance. Handoff for final closure: the report text already states, "The only NVM field value feed-wide that identifies Monero is dp=3333; no text, hostname, or module identifier exists. That sole flow's duration, computed in-tool, is 112 seconds." It also states, "7,070 (broader :443 span): no Monero identifier in NVM; shared with 192.168.24.128 (same ph), contradicting singular 'the endpoint'; :3333 sits mid-window (78 :443 flows overlap it), so the sets are concurrent channels, not one activity; a span also counts idle gaps, not generation." The clarify closes the cutoff in substance with: "Yes. 112 is final with no further Cisco NVM work required." and "My R2 report's Open-questions section closed with: "None — the metric-definition premise is settled inside NVM; 112 stands."
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['sa', 'da', 'dp', 'dh', 'pn', 'ppn', 'fss', 'fes', 'liuidp', 'liuida']
- Rounds worked: 2/8  (iterations: 26, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata sa=192.168.70.186 | stats count min(fss) as first_start max(fes) as last_end by da dp pn ppn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (dp=58868 OR dp=50414 OR dp=4287 OR dp=8080 OR dp=22790 OR dp=52672 OR dp=53567 OR dp=56756 OR dp=65490 OR dp=3306 OR dp=21 OR dp=22) | stats count values(sa) as src values(da) as dst values(pn) as proc by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (monero OR stratum OR pool OR miner OR xmr OR cryptonight) | stats count by sourcetype
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (monero OR stratum OR pool OR miner OR xmr OR cryptonight) | stats list(_raw) as raw_events
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (sp=3333 OR da=192.168.70.186) | stats count by sa da sp dp pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 dp=443 | stats count min(fss) as first_start max(fes) as last_end by sa ph pn ppn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count dc(sa) as endpoints min(fss) as first_start max(fes) as last_end by dp pn ppn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count min(fss) as first_start max(fes) as last_end by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count min(fss) as first_start max(fes) as last_end values(sa) as endpoints by da pn ppn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats list(_raw) as raw_events
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=3333 | eval duration=fes-fss | stats values(fss) as fss values(fes) as fes values(duration) as duration_seconds
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=3333 | stats values(fss) as fss values(fes) as fes eval(round(fes-fss)) as duration_seconds
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 dp=443 | eval span=max(fes)-min(fss) | stats count min(fss) as first_start max(fes) as last_end values(span) as span_seconds sum(eval(if(fes<1534762025,1,0))) as flows_ended_before_3333 sum(eval(if(fss>1534762137,1,0))) as flows_started_after_3333 sum(eval(if(fss<=1534762137 AND fes>=1534762025,1,0))) as flows_overlapping_3333_window
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count sum(ibc) as total_in sum(obc) as total_out avg(ibc) as avg_in max(ibc) as max_in avg(obc) as avg_out max(obc) as max_out by dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 ph=D3F8FADE829D2B7BD596C4504A6DAE5C034E789B6A3DEFBE013BDA7D14466677 | stats count min(fss) as first_start max(fes) as last_end by da dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 pn=powershell.exe | stats count min(fss) as first_start max(fes) as last_end by da dp ppn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | stats count by dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | stats count min(fss) as first_start max(fes) as last_end by da dp pn ppn | sort - count
