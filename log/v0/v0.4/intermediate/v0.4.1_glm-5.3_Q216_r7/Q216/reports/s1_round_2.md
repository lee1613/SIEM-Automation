# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=10_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=fss,fes,sa,da,dh,dp,pn,ppn,pa,ph,liuid,mnl,mhl,ibc,obc
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 40

## Prior rounds
- R1: Pool=45.77.53.176 (frothly.com web server); miner=powershell.exe ph=D3F8FADE…6677; two mining endpoints found: 192.168.70.186 (span 7070s) and 192.168.24.128 (7102s); submitted 7070 partial.

## This round
### What I ran
- `| stats count by mnl` (all 33 values) and `da=45.77.53.176 | stats count by sa,mnl,mhl` → mnl/mhl empty for all 4,832 pool flows; values are Windows service DLLs only.
- `ph IN (…6677,…6600) | stats count by sa,da,dp,pn,ph` → miner hash on THREE endpoints: 192.168.24.128 (1,015 pool flows + bit.ly/leeholmes.com downloads), 192.168.70.186 (3,814 pool flows incl. the only 3333 flow), 192.168.8.103 (2 long flows to internal proxy 192.168.9.30: 101s, 108s).
- `sa IN (192.168.9.30,192.168.9.31)` → 0 events: the proxy's onward flows are invisible in this feed.
- `da=45.77.53.176 | eval dur=fes-fss | stats count,sum(dur),max(dur) by sa` → .70.186: sum 3564s, max 112s; .24.128: sum 1266s, max 12s.
- `| stats count by sa,liuid,liuida | sort sa` → .8.103 and .70.186 both FyodorMalteskesko; .24.128 AlBungstein.

### What it means
FOUND: multiple endpoints generate Monero directly to the pool. Literal singular "the endpoint" → one endpoint's window. The defining mining endpoint is 192.168.70.186: 79% of pool flows, the dataset's only Stratum-3333 connection, miner as SYSTEM via WmiPrvSE (attacker's dedicated deployment). Span = max(fes)−min(fss) = 1534766374−1534759304 = **7070**. Alternatives if SH rules otherwise: 7102 (patient zero 192.168.24.128) or 7113 (union window 1534759261→1534766374 — rejected: wording is singular; overlapping windows must not be summed).

## Assumptions
- Coverage: dest/dvc/udid/fv/vendor_product/iid = constants, cannot carry mining. dh: enumerated for all pool flows → Unknown (4,830) + www.frothly.com (2 benign). ds: not directly queried — UNVERIFIED. fss/fes (fst/fet twins): used in all span computations — VERIFIED. sa: full sa↔user map (50/57 rows; all mining endpoints covered). liuid/liuidp/liuida/liuat/paa/pa/pap/ppa/ppuat/puat: identity fields enumerated for pool flows — VERIFIED. pn/ppn/ph/pph: all 60 pn values; ph traced feed-wide — VERIFIED. pr: all pool flows TCP. dp: 443 + one 3333. sp: ephemeral. ibc/obc: byte counts NOT aggregated — UNVERIFIED (samples uniform ibc=0 obc=95). mnl/mhl: cannot carry mining — VERIFIED.
- Selection: 192.168.70.186 over 192.168.24.128 (delivery endpoint, 1,015 vs 3,815 flows), over 192.168.8.103 (2 proxy flows only), over 192.168.105.214 (benign) — VERIFIED.
- Definition: "generates for N seconds" = elapsed window of miner→pool flows; sum-of-durations (3564s) rejected — VERIFIED computation, interpretive definition.

## Ruled out
- mnl/mhl as mining indicators (empty on all pool flows).
- 192.168.8.103 as confirmable

_[truncated at 400 words]_

_Coverage check (runner): 9 field(s) of syslog are never named in your Coverage line: da, dh, dp, ds, mhl, pph, pr, puat, sp. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
