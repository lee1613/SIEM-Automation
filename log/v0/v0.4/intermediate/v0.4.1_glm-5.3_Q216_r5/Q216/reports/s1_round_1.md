# s1 - Q216 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=12_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=dp, sp, sa, da, dh, pn, ppn, mnl, mhl, fss, fes, fst, fet, ibc, obc
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 95

## Prior rounds
- Round 1 (this round): first round on this scope; no prior rounds.

## This round
### What I ran
- `index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dp | sort dp` -> 22 distinct ports; dp=3333 appears exactly once; no 4444/5555/7777/14444/45700 anywhere.
- `index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | eval duration=fes-fss | stats ...` -> 1 event: sa=192.168.70.186, da=45.77.53.176, pn=powershell.exe, fss=1534762025, fes=1534762137, duration=112.
- `get_raw_events` on that event -> fst="Mon Aug 20 10:47:05 2018", fet="Mon Aug 20 10:48:57 2018", dh="Unknown", mnl="''", ibc=5782875, liuid=AzureAD\FyodorMalteskesko.
- `da=45.77.53.176 | stats count by sa, dp, pn, ppn` -> 3 endpoints; only 192.168.70.186 uses dp=3333; 192.168.24.128 and 192.168.105.214 use 443/80 only.
- `sp` full value list -> ephemeral/service ports only; no pool port on the source side.

### What it means
FOUND: the exact basis for calling this traffic Monero-related in this feed is **destination port 3333**, the standard Monero Stratum pool port — the only Monero-indicative value anywhere in the feed (dh is "Unknown" and mnl is empty, so no hostname or module evidence exists). The single dp=3333 flow belongs to endpoint **192.168.70.186** (FyodorMalteskesko's host, powershell.exe). Duration computed in SPL as `fes-fss` = 1534762137 − 1534762025 = **112** whole seconds, independently confirmed by fst/fet (10:47:05 → 10:48:57 = 1m52s).

## Assumptions
- Coverage: dp — full 22-value enumeration, only 3333 is a Stratum port (VERIFIED); sp — full top-20 list, ephemeral only (VERIFIED); da — top-20 list, 45.77.53.176 is the pool IP (VERIFIED); dh — "Unknown" for pool IP, no hostname basis (VERIFIED); pn/ppn — powershell.exe/powershell.exe on the 3333 flow (VERIFIED); mnl/mhl — empty on the 3333 flow, no module basis (VERIFIED); fss/fes — epoch seconds, duration computed in SPL (VERIFIED).
- Selection: endpoint 192.168.70.186 chosen because it owns the only dp=3333 flow; 192.168.24.128 and 192.168.105.214 ruled out — they reach the pool IP only on 443/80 (VERIFIED).
- Premise: 3333 is the Monero Stratum port — industry-standard knowledge, not verifiable inside BOTSv3 (UNVERIFIED in-feed, but the feed offers no competing basis).

## Ruled out
- dp=8080 (26 events) — internal traffic to 192.168.9.30, not a pool.
- dp=3306/9997/58868/50414 — MySQL/Splunk ports, not Stratum.
- 443/80 flows to 45.77.53.176 — same pool IP but no Monero port basis.

## Open questions for SH
- Should

_[truncated at 400 words]_

_Coverage check (runner): 25 field(s) of syslog are never named in your Coverage line: dest, ds, dvc, fet, fst, fv, ibc, iid, liuat, liuid, obc, pa, ph, ppa, pph, ppuat, pr, puat, sa, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
