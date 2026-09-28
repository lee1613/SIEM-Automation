# s1 - Q216 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=4_
**Scope:** sourcetype=syslog | source=cisconvmflowdata | fields=pn, sa, da, dp, fss, fes, ibc, obc, dh, iid, liuidp, ph, sp
**Insight:** FOUND
**Candidate:** 112   **Confidence:** 65

## Prior rounds
- R1: Feed located (78,459 events); no miner-named process; 45.77.53.176 = only large unattributed dest; one dp=3333 flow from 192.168.70.186.
- R2: Raw record verified (fss=1534762025, fes=1534762137 = 112s); three measures computed (112/3564/7070); .24.128 ruled out (no pool flow).
- R3: Byte direction calibrated; 443 rate unchanged around the 3333 session; no Monero text in feed; BSTOLL-L ruled out.
- R4: Rival scan (dur>45s) found no mining-like rival; 443 polling proven intermittent (33% coverage); endpoint tied to FYODOR-L.froth.ly via iid=35.

## This round
### What I ran
- `sp=3333 | stats ...` -> 0 events: port 3333 never appears as a source port.
- `sa=45.77.53.176 | stats ...` -> 0 events: the server never initiates flows.
- `da=45.77.53.176 pn=powershell.exe | stats dc(ph), values(mnl/mhl) by sa,dp` -> 3 rows: the 3333 flow's hash (...6677) is the same process as all 1,015 flows on .24.128 and 3,621 on .70.186; module lists empty.
- `sa=192.168.70.186 da=45.77.53.176 | stats ... by ph,dp` -> 3 rows: hash 6677 = 2h of 443 polling + the 112s 3333 session; hash 6600 = separate 193-flow 443 burst, 10:23-10:28 only.

### What it means
FOUND: 112 seconds. The premise is now settled and stated plainly: the dataset contains NO case-internal identifier tying 45.77.53.176:3333 to Monero — no text, no hostname, no modules, no process name. What the records do show, on every axis the feed offers: port 3333 is used exactly once in 78,459 events (never as source port); the server never initiates; its full client set is the implant's powershell.exe on two hosts plus one browser fetch of www.frothly.com; and the 3333 session was made by the same self-parented powershell process (hash 6677, user FyodorMalteskesko) that runs the 443 polling on both hosts. So the row's uniqueness and behavior make it the dataset's sole Monero representation, while the only link to "Monero" specifically is the question's wording plus the port-3333 stratum convention. Duration = fes-fss = 1534762137-1534762025 = 112.

## Assumptions
- Coverage: Monero generation as process name (0), pool-port flow (1: the 3333 session), sustained bulk external transfer (only the 3333 session), explicit text (none) — VERIFIED.
- Selection: the 3333 session over 443 polling (intermittent, 33% coverage, same process on a non-mining host), over the 6600-hash burst (5 min, small bytes, 443 only), over leeholmes.com/internal scans — VERIFIED.
- Definition: duration = fes-fss of the pool session — VERIFIED.
- Port 3333 = Monero stratum — UNVERIFIED: no dataset-internal evidence; web_lookup empty twice; rests on the question's premise and port convention, stated as such.

## Ruled out
- 443 polling as generation — intermittent, duplicated on .24.128, made by the same implant process as the C2 channel.
- Hash-6600 443 burst — 5 minutes, 442KB, no pool port.
- BSTOLL-L (192.168.247.131) — no powershell.exe, no 45.77.53.176 traffic.
- Reverse/server-initiated or source-port-3333 traffic — 0 events on both.

## Open questions for SH
- None; the remaining gap (port convention + question wording as the only Monero tie) is stated plainly above and cannot be closed from inside this feed.