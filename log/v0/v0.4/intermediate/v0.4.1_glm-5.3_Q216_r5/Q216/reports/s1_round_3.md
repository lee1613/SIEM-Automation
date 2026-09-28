# s1 - Q216 - Round 3
_stamped by runner: rounds_remaining=5 novel_spl=3_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=dp, sp, ppa, sa, da, fss, fes, fst, fet, pn, ppn, ph, pph
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 95

## Prior rounds
- Round 1: Confirmed feed (78,459 events); found single dp=3333 flow 192.168.70.186→45.77.53.176 powershell.exe, fss=1534762025 fes=1534762137; SPL duration=112s; submitted with one UNVERIFIED external premise.
- Round 2: Enumerated all 25 runner-named fields (dest, ds, dvc, fet, fst, fv, ibc, obc, iid, liuat, liuid, liuidp, liuida, pa, ph, ppa, pph, ppuat, pr, puat, sa, udid, vendor_product, pap, paa) — no Monero carrier; keyword sweep = 0 hits; process-hash tie between 3333 flow and 443 pool flows; resubmitted 112.

## This round
### What I ran
- `web_lookup` "stratum mining protocol TCP port 3333 monero pool" -> no snippets (3rd attempt); external premise stays UNVERIFIED-external.
- `| stats count by ppa` -> 12 values: NT AUTHORITY\SYSTEM, 8 AzureAD Frothly employees, Unknown, NETWORK SERVICE, '' — no Monero carrier.
- `dp=3333 | stats values(sa/da/pn/ppn/pa/ppa/liuid/ph/pph/fss/fes), values(fes)-values(fss)` -> 1 event: 192.168.70.186→45.77.53.176, powershell.exe (parent powershell.exe), account AzureAD\FyodorMalteskesko (pa=ppa=liuid), hash D3F8FADE...6677 (ph=pph), fss=1534762025, fes=1534762137, duration=112.
- `(sp IN (3333,4444,5555,7777,8888,9999,14433,14443,14444,45700,8333,9333,12222,17777) OR dp IN (...))` -> exactly 1 event: the same dp=3333 flow.

### What it means
FOUND: dp, sp, and ppa are now fully covered. dp is the ONLY field carrying a Monero indicator (port 3333, the standard Monero Stratum pool port); sp carries no pool port on any value; ppa carries only Frothly/NT AUTHORITY accounts. Exactly one flow in the entire feed hits a Monero pool port, and it belongs to 192.168.70.186. Duration = fes-fss = 112 whole seconds, corroborated by fst/fet (10:47:05→10:48:57 = 1m52s).

## Assumptions
- Coverage: dp — full 22-value enumeration, 3333 exactly once, only pool port (VERIFIED); sp — full enumeration + 14-port pool sweep, no pool port (VERIFIED); ppa — full 12-value enumeration, no Monero carrier (VERIFIED); sa/da/pn/ppn/ph/pph/pa/liuid — enumerated on the 3333 flow, chain complete (VERIFIED); fss/fes/fst/fet — duration computed in SPL, corroborated (VERIFIED).
- Selection: 192.168.70.186 is THE endpoint because it owns the only dp=3333 flow; 192.168.24.128 and 192.168.105.214 ruled out (443/80 only to pool IP) (VERIFIED).
- Premise: 3333 = Monero Stratum port — UNVERIFIED externally (web_lookup empty, 3 attempts); in-feed corroboration: powershell.exe, 5,782,875 bytes inbound, dedicated external IP, same process hash as 443 pool flows.

## Ruled out
- sp as Monero carrier (no pool port on any value); ppa as Monero carrier (accounts only); all other pool ports (4444/5555/7777/8888/9999/14433/14443/14444/45700/8333/9333/12222/17777 — zero

_[truncated at 400 words]_

_Coverage check (runner): 20 field(s) of syslog are never named in your Coverage line: dest, dh, ds, dvc, fv, ibc, iid, liuat, mhl, mnl, obc, ppuat, pr, puat, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._
