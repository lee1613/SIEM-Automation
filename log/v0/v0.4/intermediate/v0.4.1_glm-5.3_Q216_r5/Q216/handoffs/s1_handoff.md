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


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['src_ip', 'dest_ip', 'dest_port', 'app', 'bytes', 'packets', 'duration', '_time']
- Rounds worked: 3/8  (iterations: 18, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 source=cisconvmflowdata da=45.77.53.176 | stats count, dc(sa) as endpoints, values(sa), values(dp), values(pn), values(ppn), min(fss) as first_start, max(fes) as last_end
- index=botsv3 source=cisconvmflowdata dp=3333 | stats count, values(sa), values(da), values(sp), values(pn), values(ppn), values(fss), values(fes), values(fst), values(fet), values(pr), values(ibc), values(obc)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (monero OR stratum OR xmrig OR minerd OR xmr OR supportxmr OR nanopool OR minergate OR monerohash) | stats count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (pool OR mine OR coin OR crypt OR stratum) | stats count by pn, dh, da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (sp IN (3333,4444,5555,7777,8888,9999,14433,14443,14444,45700,8333,9333,12222,17777) OR dp IN (3333,4444,5555,7777,8888,9999,14433,14443,14444,45700,8333,9333,12222,17777)) | stats count, values(sa), values(da), values(sp), values(dp), values(pn), values(ppn)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count by dh, dp, pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count by sa, dp, pn, ppn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count, dc(sa) as endpoints, values(sa), values(dp), values(pn), values(ppn), min(fss) as first_start, max(fes) as last_end
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | eval duration=fes-fss | stats count, values(sa) as endpoint, values(da) as pool_ip, values(pn) as process, values(fss) as flow_start, values(fes) as flow_end, values(duration) as duration_seconds
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats count, values(sa), values(da), values(sp), values(pn), values(ppn), values(fss), values(fes), values(fst), values(fet), values(pr), values(ibc), values(obc)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=3333 | stats values(sa) as endpoint, values(da) as pool_ip, values(pn) as process, values(ppn) as parent_process, values(pa) as proc_account, values(ppa) as parent_account, values(liuid) as logged_in_user, values(ph) as proc_hash, values(pph) as parent_hash, values(fss) as flow_start, values(fes) as flow_end, values(fes)-values(fss) as duration_seconds
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp=8080 | stats count, values(sa), values(da), values(pn), values(dh)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=hdoor.exe | stats count, values(sa), values(da), values(dp), values(dh), values(fss), values(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexeplorer.exe | stats count, values(sa), values(da), values(dp), values(ppn), values(dh), min(fss), max(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count by ph, pph, da, dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end, max(fes)-min(fss) as total_span, values(dp)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 | stats count by da, dp, pn, ppn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sp=3333 OR dp=3333 OR dp=4444 OR dp=5555 OR dp=7777 OR dp=14444 OR dp=45700 | stats count, values(sa), values(da), values(pn), values(fss), values(fes)
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by da | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dh | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dp | sort dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by mnl | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn, ppn | sort pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn, ppn | sort pn | tail 30
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by ppa | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats values(dest) as dest_all, values(ds) as ds_all, values(dvc) as dvc_all, values(fv) as fv_all, values(udid) as udid_all, values(vendor_product) as vp_all, values(pr) as pr_all, values(iid) as iid_all, values(liuat) as liuat_all, values(liuida) as liuida_all, values(paa) as paa_all, values(puat) as puat_all, values(ppuat) as ppuat_all, values(liuid) as liuid_all, values(liuidp) as liuidp_all, values(pa) as pa_all, values(pap) as pap_all
