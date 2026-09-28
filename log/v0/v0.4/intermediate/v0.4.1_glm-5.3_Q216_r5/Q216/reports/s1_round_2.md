# s1 - Q216 - Round 2
_stamped by runner: rounds_remaining=6 novel_spl=11_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=dp, sp, sa, da, dh, pn, ppn, mnl, mhl, fss, fes, fst, fet, ibc, obc, dest, ds, dvc, fv, iid, liuat, liuid, liuidp, liuida, pa, pap, paa, ph, ppa, pph, ppuat, pr, puat, udid, vendor_product
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 95

## Prior rounds
- Round 1: Confirmed feed (78,459 events); found single dp=3333 flow 192.168.70.186→45.77.53.176 powershell.exe, fss=1534762025 fes=1534762137; SPL duration=112s; submitted 112 with one UNVERIFIED external premise and 25 unnamed fields.

## This round
### What I ran
- `web_lookup` "Monero Stratum port 3333" and "port 3333" -> no snippets (2 attempts); external premise stays UNVERIFIED-external.
- Keyword sweep `(monero OR stratum OR xmrig OR minerd OR xmr OR supportxmr OR nanopool OR minergate OR monerohash)` -> 0 events; `(pool OR mine OR coin OR crypt)` -> only ad-exchange pools (pool.adizio.com/pool.admedo.com, 443) and cryptsvc.dll.
- `| stats values(dest), values(ds), values(dvc), values(fv), values(udid), values(vendor_product), values(pr), values(iid), values(liuat/liuida/paa/puat/ppuat/liuid/liuidp/pa/pap)` -> all values enumerated: infra constants, Frothly employees, NT AUTHORITY; no Monero carrier.
- `| stats count by pn, ppn | sort pn` (both halves, 76 rows) -> no miner-named process; hdoor.exe -> internal 192.168.9.x on 21/22/3306 only.
- `| stats count by dh` (1,573 rows) / `by da` (2,735 rows) / `by mnl` (33 rows) -> no pool hostname, no pool IP besides 45.77.53.176, all modules are Windows service DLLs.
- `pn=powershell.exe | stats count by ph, pph, da, dp` -> dp=3333 flow's hash D3F8FADE...6677 identical to the 3,814 flows to 45.77.53.176:443.

### What it means
FOUND: no field in the feed carries a competing Monero indicator — dp=3333 is the sole basis, and it is unique (one flow, one endpoint). The process-hash match proves the same powershell.exe process made both the 3333 flow and the 443 flows to the pool IP, strengthening the chain. Duration = fes-fss = 112 whole seconds, corroborated by fst/fet.

## Assumptions
- Coverage: dest/dvc=splunkhwf.froth.ly, fv=nvzFlow_v3, udid=1 UUID, vendor_product=nix, pr=6/17, iid=0-42, liuat/puat/ppuat=0/1/2 — constants, cannot carry concept (VERIFIED, all values enumerated); ds=Unknown/froth.ly/localdomain (VERIFIED); liuid/liuidp/liuida/pa/pap/paa — Frothly employees + NT AUTHORITY only, no miner account (VERIFIED); ph/pph — opaque hashes, no label, but tie 3333 flow to pool-IP 443 flows (VERIFIED); fst/fet — corroborate fss/fes = 112s (VERIFIED); ibc/obc — byte context, 5,782,875 in on 3333 flow (VERIFIED); sa — full enumeration, 192.168.70.186 unique 3333 endpoint (VERIFIED); dh/da/mnl/mhl/pn/ppn — full enumeration, no Monero value (VERIFIED); raw-text keyword sweep — 0 Monero hits (VERIFIED).

_[truncated at 400 words]_

_Coverage check (runner): 3 field(s) of syslog are never named in your Coverage line: dp, ppa, sp. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
