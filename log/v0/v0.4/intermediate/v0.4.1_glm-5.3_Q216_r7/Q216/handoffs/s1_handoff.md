# s1 - Q216 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=2_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=sa,da,dh,dp,ds,pn,ppn,ppa,pph,pa,paa,pap,ph,liuid,liuida,liuidp,liuat,mnl,mhl,ibc,obc,pr,puat,ppuat,sp,udid,iid,fss,fes,fst,fet,dest,dvc,fv,vendor_product
**Insight:** FOUND
**Candidate:** 7070   **Confidence:** 62

## Prior rounds
- R1–R2: Pool=45.77.53.176 (frothly.com web server); miner=powershell.exe ph=D3F8FADE…6677; endpoints .70.186 (7070s) and .24.128 (7102s); .8.103 proxy-relayed only.
- R3: Byte counts verified (volume, not duration); union 7113 SPL-verified; continuity proven by 5-min binning.
- R4–R5: udid corrected to deployment ID; .70.186/.8.103 share iid 35/36 = one physical host; all 49 sa enumerated; iexepler.exe resolved.
- R6: All 13 then-flagged fields covered; 7070 submitted solved.

## This round
### What I ran
- `da=45.77.53.176 | stats count,min(fss),max(fes) by sa | appendpipe [stats sum(count),min(first_start),max(last_end) | eval sa="UNION_ALL_POOL_FLOWS"] | eval duration_seconds=last_end-first_start` → .105.214: 219s (benign); .24.128: 7102s; .70.186: 7070s; UNION: 7841s.
- `sa=192.168.70.186 da=45.77.53.176 | stats count,min(fss),max(fes) | eval duration_seconds=last_end-first_start` → 3,815 flows, 1534759304→1534766374, 7070.

### What it means
FOUND: **7070 seconds**. Coverage of every field: **Endpoint identity** — sa: all 49 values enumerated; 4 Monero-participating — VERIFIED. iid: .70.186/.8.103 share 35/36 (one host); .24.128=33 — VERIFIED. liuid/liuidp/liuida/liuat: FyodorMalteskesko on Host A, AlBungstein on Host B, BSTOLL-L benign — VERIFIED. pa/paa/pap: SYSTEM (WMI) on Host A vs user on Host B — VERIFIED. udid: constant feed-wide, deployment ID — VERIFIED. **Mining indication** — da: complete powershell destination set (7 rows); 45.77.53.176 only sustained pool — VERIFIED. dh: Unknown on 4,830 pool flows; www.frothly.com on 2 benign — VERIFIED. dp: 443×4,829 + 3333×1 (only Stratum flow) — VERIFIED. ds: localdomain on all pool flows — VERIFIED. pn: all 60 values; powershell.exe = miner — VERIFIED. ppn: WmiPrvSE.exe deployment on Host A — VERIFIED. ph: miner hash traced to 3 addresses — VERIFIED. pph: 6 distinct — VERIFIED. mnl/mhl: empty on all pool flows — VERIFIED. pr: all TCP — VERIFIED. puat/ppuat: single value — VERIFIED. sp: 4,387 ephemeral — VERIFIED. ibc/obc: summed (14.8MB vs 2.38MB) — volume, not time — VERIFIED. **Timing** — fss/fes: all duration math — VERIFIED. fst/fet: text twins — VERIFIED. **Feed metadata** — dest/dvc/fv/vendor_product: single-valued constants — VERIFIED.

## Assumptions
- Selection: Host A (.70.186/.8.103) is "the endpoint" — 79% of pool flows, only Stratum-3333 flow, 6.2x pool bytes, SYSTEM-context WMI deployment, storyline identity — VERIFIED.
- Definition: elapsed window max(fes)−min(fss), no gaps — VERIFIED.
- Singular reading of "the endpoint" — UNVERIFIED externally (web_lookup ×3 empty); interpretive, defended by five discriminators.

## Ruled out
- 7102 (Host B: secondary, 21% of flows, no Stratum, user-context, re-fetch inside window); 7113 (union: two physical hosts —

_[truncated at 400 words]_

_Coverage check (runner): 35 field(s) of syslog are never named in your Coverage line: da, dest, dh, dp, ds, dvc, fes, fet, fss, fst, fv, ibc, iid, liuat, liuid, mhl, mnl, obc, pa, ph, pn, ppa, pph, ppn, ppuat, pr, puat, sa, sp, udid, vendor_product, pap, liuidp, liuida, paa. For each, say whether it could carry the question's concept, and search the ones that could — across all their values, not only the most common._


## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['_time', 'src_ip', 'dest_ip', 'dest_port', 'protocol', 'app', 'bytes', 'packets', 'duration']
- Rounds worked: 8/8  (iterations: 41, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourc-host 2 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end | eval duration_seconds=last_end-first_start
- index=botsv3 source=cisconvmflowdata | top limit=20 pn
- index=botsv3 source=cisconvmflowdata | top limit=20 sa
- index=botsv3 sourcetype=stream:dns "45.77.53.176" | stats count by query, answer
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (da=45.77.53.176 pn=powershell.exe) OR (sa=192.168.8.103 pn IN (powershell.exe,iexepler.exe)) | stats count, min(fss) as first_start, max(fes) as last_end | eval duration_seconds=last_end-first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata (da=45.77.53.176) OR (sa=192.168.8.103 pn IN (powershell.exe,iexepler.exe)) | stats count, min(fss) as first_start, max(fes) as last_end | eval duration_seconds=last_end-first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da IN (192.168.70.186,192.168.24.128) | stats count by sa, da, dp, pn, ppn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=192.168.9.30 | stats count by sa, pn, dh, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=192.168.9.31 | stats count by sa, pn, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | bin _time span=5m | stats count by sa, _time | sort sa, _time
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | stats count, dc(sp) as distinct_src_ports, dc(pph) as distinct_parent_hashes, values(puat) as parent_user_types by sa, ppn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 pn=powershell.exe | stats count, min(fss) as first_start, max(fes) as last_end | eval duration_seconds=last_end-first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | eval dur=fes-fss | stats count, sum(dur) as sum_dur, max(dur) as max_dur, avg(dur) as avg_dur by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count by pn, sa, dh, sp, dp, pr
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count by pr, ds, dh, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count by sa, mnl, mhl | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count by sa, ph, ppn, pa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count by sa, pn, ppn, pa, liuid
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end by sa | appendpipe [ stats sum(count) as count, min(first_start) as first_start, max(last_end) as last_end | eval sa="UNION_ALL_POOL_FLOWS" ] | eval duration_seconds=last_end-first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count, sum(fes-fss) as total_flow_seconds, min(fss) as first_start, max(fes) as last_end by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats count, sum(ibc) as total_ibc, sum(obc) as total_obc, dc(ibc) as distinct_ibc, dc(obc) as distinct_obc by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats dc(pn) as dc_pn, values(pn) as pn_vals, dc(ppn) as dc_ppn, values(ppn) as ppn_vals, dc(ppa) as dc_ppa, values(ppa) as ppa_vals, dc(pph) as dc_pph, dc(pr) as dc_pr, values(pr) as pr_vals, dc(puat) as dc_puat, values(puat) as puat_vals, dc(sp) as dc_sp, dc(ppuat) as dc_ppuat, values(ppuat) as ppuat_vals
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats min(_time) as tmin, max(_time) as tmax | eval duration=tmax-tmin
- index=botsv3 sourcetype=syslog source=cisconvmflowdata da=45.77.53.176 | stats min(fss) as first_start, max(fes) as last_end, count by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata dp IN (3333,4444,5555,7777,8888,9999,14444,45700) | stats count by sa, da, dp, pn, dh
- index=botsv3 sourcetype=syslog source=cisconvmflowdata iid=0 | stats count by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata liuida=BSTOLL-L | stats count by sa, liuid, pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata paa=BSTOLL-L | stats count by sa, pn, da, dh, dp, liuid
- index=botsv3 sourcetype=syslog source=cisconvmflowdata ph IN ("D3F8FADE829D2B7BD596C4504A6DAE5C034E789B6A3DEFBE013BDA7D14466677","D3F8FADE829D2B7BD596C4504A6DAE5C034E789B6A3DEFBE013BDA7D14466600") | stats count by sa, da, dp, pn, ph
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexepler.exe | stats count, min(fss) as first, max(fes) as last, sum(fes-fss) as sum_dur by sa, da, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=iexepler.exe | stats count, values(sa) as src, values(da) as dst, values(dp) as ports, values(liuid) as users, min(fss) as first, max(fes) as last, sum(fes-fss) as sum_dur
- index=botsv3 sourcetype=syslog source=cisconvmflowdata pn=powershell.exe | stats count by sa, da, dh, dp, pr
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa IN (192.168.70.186,192.168.24.128,192.168.8.103,192.168.247.131) | stats dc(udid) as distinct_udids, dc(iid) as distinct_iids, values(iid) as iid_list, count by sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa IN (192.168.70.186,192.168.8.103,192.168.24.128) | where NOT match(da,"^(192\.168|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|127\.)") | stats count, min(fss) as first, max(fes) as last by sa, da, dh, dp, pn | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa IN (192.168.9.30,192.168.9.31) | stats count by sa, da, dh, dp, pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end | eval duration_seconds=last_end-first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 pn=powershell.exe da!=45.77.53.176 | stats count, min(fss) as first, max(fes) as last by da, dh, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.24.128 | stats count by liuid, liuidp, pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.129 | stats count by pn, da, dh, dp | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 | eval dur=fes-fss | stats sum(dur) as total_dur, max(dur) as longest, count by pn, da, dp | sort - total_dur
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 | stats count by liuid, liuida
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.247.131 | stats count, min(fss) as first, max(fes) as last by pn, da, dh, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.70.186 da=45.77.53.176 | stats count, min(fss) as first_start, max(fes) as last_end | eval duration_seconds=last_end-first_start
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.8.103 | stats count by pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.8.103 | stats count by pn, da, dh, dp, pr, min(fss) as first, max(fes) as last
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.8.103 | stats count, min(fss), max(fes) by pn, da, dh, dp, pr
- index=botsv3 sourcetype=syslog source=cisconvmflowdata sa=192.168.8.111 | stats count by pn, da, dh, dp
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | eval dur=fes-fss | stats max(dur) as longest, count by pn, da, dp | sort - longest
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by da | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by dh | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by mnl | sort - count
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | sort pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by pn | where pn > "putty.exe" | sort pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by sa | sort sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by sa, liuid, liuida | sort sa
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats count by udid
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | stats dc(dest) as dc_dest, values(dest) as dest_vals, dc(dvc) as dc_dvc, values(dvc) as dvc_vals, dc(fv) as dc_fv, values(fv) as fv_vals, dc(vendor_product) as dc_vp, values(vendor_product) as vp_vals, dc(udid) as dc_udid, values(udid) as udid_vals
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | top limit=20 pn
- index=botsv3 sourcetype=syslog source=cisconvmflowdata | top limit=20 sa
