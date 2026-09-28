# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=7_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn,ppn,sa,da,dp,dh,fss,fes,liuidp
**Insight:** partial
**Candidate:** none — prime suspect iexepler.exe, flow span 1686s, unverified
**Confidence:** 20

## Prior rounds
- Round 1: feed confirmed (78,459 events, all Aug 20 2018); all 60 pn values read, no miner-named process; iexepler.exe isolated as prime suspect (15 flows, span 1534763140–1534764826); duration never computed; hdoor.exe unexamined.

## This round
### What I ran
- get_sources syslog → cisconvmflowdata exists, 78,459 events.
- get_sourcetype_fields → fss/fes = flow start/end epoch seconds; pn/ppn = process/parent; sa/da/dp/dh = endpoints; liuidp = user.
- `| stats count by pn | search pn="*miner*" OR "*xmrig*" OR "*monero*" OR "*crypt*"` → 0 rows.
- Full pn listing, all 60 values read → no miner name; anomalies: iexepler.exe (15), hdoor.exe (7).
- `pn=iexeoler.exe` exact and raw term "iexeoler" → 0 (fieldsummary garbles the name; real value found via `pn=iex*`).
- `pn=iex* | stats ... by pn` → iexepler.exe: 15 flows, 192.168.8.103 → 192.168.9.30:8080, dh=Unknown, user FyodorMalteskesko, min(fss)=1534763140, max(fes)=1534764826. iexplore.exe: 33 flows to Microsoft CDN/bing on 443, three ordinary users.

### What it means
Prime suspect for the miner is iexepler.exe — a masquerade of iexplore.exe, run by attacker account FyodorMalteskesko, all 15 flows to one internal host 192.168.9.30:8080, spanning 1686s (10:25:40–10:53:46 UTC). But no record yet shows Monero generation: nothing names monero or a pool, hdoor.exe (7 events) is unexamined, and the question's duration was never computed — I hold only the span, not sum(fes-fss). No submittable value.

## Assumptions
- Coverage: pn — all 60 values read, no miner name (VERIFIED absent by name); ppn, dp, dh, da — only top values seen, pool port/hostname/dest not searched (UNVERIFIED); cisconvmsysdata (11 events) and cisconvmifdata (8 events) not searched (UNVERIFIED).
- Selection: iexepler.exe picked on masquerade name + attacker user + single internal dest; hdoor.exe not ruled out (UNVERIFIED).
- Definition: "total seconds generating" = sum of per-flow (fes-fss) or span max(fes)-min(fss); overlapping flows must not be double-counted — undetermined (UNVERIFIED).
- fss/fes are epoch seconds — VERIFIED from raw events (fss="1534778279" with matching fst string).

## Ruled out
- Any pn matching miner/xmrig/monero/crypt — 0 events.
- iexplore.exe (legitimate IE) — Microsoft destinations on 443, users BillyTun/BudStoll/MalloryKrausen.
- fieldsummary value "iexeoler.exe" — display garble; true value is iexepler.exe.

## Open questions for SH
- Is the Monero miner in this case identified by a pool destination (IP/port/hostname) I should pivot on, or by process name?
- Is hdoor.exe a known artifact of this case (backdoor vs miner)?
- Should "total seconds" be the sum of per-flow durations or the first-start-to-last-end span?

_Iteration cap reached: 12/12 iterations used this round — cut off, not finished._

_Partial results (runner): 1 result(s) this round returned only their first rows — `get_field_values: {"field": "pn", "source": "cisconvmflowdata", "sourcetype": "syslog", "top_n": 20}` (20 of 60 rows seen). A claim resting on them alone is UNVERIFIED._
