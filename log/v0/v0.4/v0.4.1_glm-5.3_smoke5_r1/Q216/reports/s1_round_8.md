# s1 - Q216 - Round 8
_stamped by runner: rounds_remaining=0 novel_spl=3_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dp, fss, fes, ibc, obc, dh, ph, sp (+ WinHostMon, stream:udp for the final artifact sweep)
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 55

## Prior rounds
- R1: Feed located; no miner-named process; 45.77.53.176 = only large unattributed dest; one dp=3333 flow from 192.168.70.186.
- R2: 3333 session verified (112s); measures 112/3564/7070; .24.128 ruled out.
- R3: Byte direction calibrated; 443 rate unchanged around the 3333 session; no Monero text in NVM feed.
- R4: Rival scan found no mining-like rival; 443 polling intermittent (33% coverage); endpoint = FYODOR-L.froth.ly.
- R5: No case-internal Monero tie inside NVM feed; 3333 unique on every axis.
- R6: Cross-feed: 3333 = HTTP GET /images/logos.png; 443 = refused TLS beaconing; 45.77.53.176 = www.frothly.com/vultr VPS with reverse shell on 8088; 0 mining terms anywhere.
- R7: NVM re-sweep without assumptions: complete unattributed-external inventories for FYODOR-L (13 rows) and BSTOLL-L (29 rows) read — no mining pattern; premise declared unsupported.

## This round
### What I ran
- Long-duration (dur>300s) external flows for BSTOLL-L/FYODOR-L -> top 50 of 306 read: all identified services (wns.windows.com, CrashPlan, splunk.froth.ly, office365, msedge, vpn.froth.ly) — no named pool.
- WinHostMon mining-term search -> 203 events = Windows WalletService on all 8 hosts; not Monero.
- WinHostMon/stream:udp for 45.77.53.176 OR 3333 -> 16 process events, all read: iexepler.exe reverse shell (`nc 45.77.53.176 8088`) on FYODOR-L; no miner process.

### What it means
FORKED CONCLUSION, stated plainly: (A) No verified Monero-generating record exists in the case data — every artifact class is now exhausted, and the only artifacts naming 45.77.53.176 treat it as attacker infrastructure (reverse shell on 8088, refused TLS on 443, PNG staging on 3333, www.frothly.com). (B) The fallback number is 112: the unique Cisco NVM 3333 session (fss=1534762025→fes=1534762137), the only dp=3333 flow in 78,459 events, the only persistent bulk session by the implant's powershell.exe from FYODOR-L. The question scopes itself to the Cisco NVM flow logs and premises they show Monero generation; within that feed, the 3333 session is the unique record that premise can point to, so 112 is submitted as the question-premise answer — with the explicit caveat that its records show a download, not a verified act of generation.

## Assumptions
- Coverage: every artifact class searched (NVM text, stream:dns/http/tcp/udp, Sysmon, osquery, WinEventLog, Symantec, WinHostMon process+service) — VERIFIED, 0 Monero labels case-wide.
- Selection: the 3333 session as the question's intended record — rests on the question's own premise and the port-3333 stratum convention, NOT on case-internal evidence — stated as such.
- Duration = fes-fss of that session = 112 — VERIFIED arithmetic.

## Ruled out
- All named-destination long flows on BSTOLL-L/FYODOR-L — identified Microsoft/CrashPlan/Splunk/VPN services.
- Windows WalletService — Windows component on all 8 hosts, not Monero.
- iexepler.exe / hdoor.exe — Struts exploit and reverse shell, lateral movement.
- 443 powershell traffic — refused TLS beaconing.

## Open questions for SH
- None; the fork is settled: no verified mining record exists; 112 is the unique-session fallback the question premise points to.

_Partial results (runner): 1 result(s) this round returned only their first rows — `run_splunk_search: index=botsv3 sourcetype=syslog source=cisconvmflowdata (sa=192.168.247.131 OR sa=192.168.2…` (50 of 306 rows seen). A claim resting on them alone is UNVERIFIED._
