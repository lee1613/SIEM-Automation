# s1 - Q213 - Round 1
_stamped by runner: rounds_remaining=2 novel_spl=7_
**Scope:** sourcetype=symantec:ep:risk:file, symantec:ep:security:file, symantec:ep:agent:file, symantec:ep:behavior:file | fields=signature/"Risk name", Computer_Name, user, dest, file_name
**Insight:** partial
**Candidate:** Very Low   **Confidence:** 45

## Prior rounds
- Q212 (prior question, carried in): SEP coin-miner detections = JSCoinminer on BTUN-L. Not re-verified this round.

## This round
### What I ran
- get_source_types -> 102 sourcetypes; 9 symantec:ep:* feeds exist.
- index=botsv3 sourcetype="symantec:ep:risk:file" | stats count by Signature, ComputerName, Risk_Action, Severity -> 0 events (field names wrong for this feed).
- get_sourcetype_fields symantec:ep:risk:file -> 91 fields over exactly 1 event: Backdoor.PsEmpire, BGIST-L, BruceGist, "Bruce Birthday Happy Hour Pics.lnk", 2018-08-20 09:58:20, Cleaned by deletion/Quarantined. No severity field, no coin miner.
- "coinminer" keyword in symantec:ep:security:file -> 0; symantec:ep:agent:file -> 0; symantec:ep:behavior:file -> 0.

### What it means
Partial, not verified. The question needs (a) the exact SEP threat-name string from the data and (b) Symantec's website severity for that name. I reached neither: the risk feed holds only Backdoor.PsEmpire, and my keyword searches used the token "coinminer", which Splunk cannot match against the single-token term "JSCoinminer" — so those three 0-result searches are non-probative, not evidence of absence. web_lookup was not reached before tools were withdrawn. The candidate "Very Low" is recalled from Symantec's published JSCoinminer writeup (Risk Level 1: Very Low) and is offered as a partial candidate only; it is not backed by a query this round.

## Ruled out
- symantec:ep:risk:file as the coin-miner feed — 1 event total, Backdoor.PsEmpire (a backdoor, not a miner), no severity field.
- Backdoor.PsEmpire as "the coin miner threat" — wrong category and wrong host (BGIST-L vs Q212's BTUN-L).
- Search term "coinminer" — tokenization makes it unable to match "JSCoinminer"; all three 0-result keyword searches must be redone with the exact token "JSCoinminer".

Next round: search "JSCoinminer" across symantec:ep:security:file, agent:file, behavior:file, agt_system:file, scm_system:file, packet:file, traffic:file; read the raw event for the full threat-name string; web_lookup Symantec's Security Center writeup for that exact name; return the severity verbatim.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
