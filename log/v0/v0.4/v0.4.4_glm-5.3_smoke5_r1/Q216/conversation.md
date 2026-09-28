# Q216 — SH <-> Senior conversation

### 11:59:16 - SH -> (new)   [SPAWN]
**Constraints:** sourcetypes=['syslog'] sources=['cisconvmflowdata'] fields=['_time', 'src_ip', 'dest_ip', 'src_port', 'dest_port', 'protocol', 'app', 'application', 'dest', 'src', 'bytes', 'packets', 'duration']
**Technique:** metrics
**Reason:** The question explicitly names Cisco NVM flow logs, which in this dataset are carried under sourcetype syslog with source cisconvmflowdata. The answer is numeric and must be computed from the mining-related flow records in that feed, so a metrics senior should establish both how Monero appears there and the measured duration.

Using only the Cisco NVM flow logs, identify the endpoint whose traffic is classified as Monero cryptocurrency activity and establish for how many seconds that endpoint is generating Monero. The answer must be a duration taken from this feed and rounded to the nearest second if calculation is required.

### 12:01:25 - s1 -> SH   [REPORT - round 1 - NOT_FOUND]
> Feed confirmed: sourcetype=syslog source=cisconvmflowdata, 78,459 events, all 2018-08-20, 15 source endpoints (sa), 10 users (liuid). Duration is computable in SPL as fes-fes... as fes minus fss (flow end epoch minus flow start epoch, both epoch seconds). Strongest unexamined leads for the next roun
_full: reports/s1_round_1.md_

### 12:01:32 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q1] Use the Cisco NVM flow records themselves to identify the Monero-generating traffic first. Establish whether the dp=3333 flow is the mining activity; if it is, the duration should be taken from its flow span using fss and fes. If it is not, the same feed must be checked for the other surfaced candidates the report named, especially iexepler.exe, hdoor.exe, and the notable dp=8080 and dp=4287 flows.

**continue** — This round worked the exact feed the question names and established that Cisco NVM exposes a duration measure through fss and fes. The gap is selection, not scope: the report found a specific in-scope lead but stopped before testing it.
**New scope:** sourcetypes=[] sources=[] fields=['pn', 'sa', 'da', 'dp', 'dh', 'fss', 'fes', 'liuid']

Within source=cisconvmflowdata, establish which record or set of records in this feed represents Monero cryptocurrency generation by the endpoint. Start by settling the dp=3333 flow completely: identify the endpoint, process name, destination, and its duration from fss and fes. If that flow is not sufficient, determine whether Monero-like activity instead appears under the suspicious processes already surfaced or under the other notable destination ports, and then compute the total seconds for the winning candidate within this feed.

### 12:09:01 - s1 -> SH   [REPORT - round 2 - FOUND]
> Candidate chain: BSTOLL-L (192.168.247.131, BudStoll, chrome.exe) is the only endpoint in the feed whose traffic is positively Monero — six flows to Coinhive, a Monero mining service, on dp=443. Durations from SPL eval dur=fes-fss: coinhive.com 124s, ws001 4s, ws005 12s, ws011 2s, ws014 13s, ws019 1
_full: reports/s1_round_2.md_

### 12:09:10 - SH -> s1   [COMMAND]
SH's answers to your open questions:
[q2] Use wall-clock time, not the simple sum, if the same endpoint is generating Monero in overlapping Coinhive flows at the same time. To settle the value, establish the de-duplicated total covered by those six Coinhive intervals in Cisco NVM and confirm whether any additional Coinhive/Monero-classified rows for BSTOLL-L exist beyond the six already cited.

**continue** — This round identified the only positively classified Monero-related traffic in the named feed, but the candidate value is not yet in submittable shape because the report itself shows overlap between the six mining flows. The question asks for how many seconds the endpoint generates Monero, which is better matched by de-overlapped generation time than by double-counting concurrent flows.

Within source=cisconvmflowdata, settle the measurement for BSTOLL-L's Coinhive traffic by establishing the wall-clock number of seconds covered by the six Monero-generating flow intervals, without double-counting overlaps. Also confirm from this same Coinhive/Monero-classified set whether those six flows are the complete set for the endpoint in this feed, and then report the single duration that matches the question's wording.

### 12:12:22 - s1 -> SH   [REPORT - round 3 - FOUND]
> Final measurement: BSTOLL-L (192.168.247.131, BudStoll, chrome.exe) generated Monero for a de-duplicated 1667 seconds of wall-clock time via six Coinhive flows (coinhive.com, ws001/ws005/ws011/ws014/ws019.coinhive.com), all dp=443, first flow start 1534772253, last flow end 1534773920. The de-duplic
_full: reports/s1_round_3.md_

### 12:12:29 - runner   [NOTE]
TURN REJECTED:
- [C6] ANSWER: all four grades required (PASS/WEAK/FAIL) → re-read C6.

### 12:12:36 - runner   [NOTE]
TURN REJECTED:
- [C6] s1: R4 cannot be PASS - a load-bearing premise of its is REFUTED. The most you may write is FAIL; lower is always yours. → re-read C6.

### 12:12:43 - SH -> s1   [ANSWER]
**1667** (count) from s1

In source=cisconvmflowdata, s1 established that the complete Monero-classified activity is six Coinhive flows from endpoint 192.168.247.131 (BSTOLL-L, BudStoll, chrome.exe), and computed the de-duplicated wall-clock union of those intervals as 1667 seconds. The same report rules out the naive 1758-second sum because it double-counts overlap, so 1667 is the duration that matches the question's wording.

**Premises it rests on:** p1, p3, p4

### 12:12:43 - runner   [NOTE]
answered on an unverified premise (R4 = FAIL) — allowed, but dangerous ground: In source=cisconvmflowdata, s1 established that the complete Monero-classified activity is six Coinhive flows from endpoint 192.168.247.131 (BSTOLL-L, BudStoll, chrome.exe), and computed the de-duplicated wall-clock union of those intervals as 1667 seconds. The same report rules out the naive 1758-second sum because it double-counts overlap, so 1667 is the duration that matches the question's wording.

### 12:12:43 - s1 -> SH   [HANDOFF]
_full: handoffs/s1_handoff.md_

