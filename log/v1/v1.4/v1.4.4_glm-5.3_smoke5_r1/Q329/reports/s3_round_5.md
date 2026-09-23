# s3 - Q329 - Round 5
_stamped by runner: rounds_remaining=3 novel_spl=4_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "From: [^<]*<(?<from_addr>[^>]+)>" | rex field=_raw "Content-Transfer-Encoding: base64(?<b64>.{1300})" | rex field=_raw "quoted-printable(?<qp>.{1300})" | stats count by from_addr, substr(b64,1,1300), substr(qp,1,1300)
- index=botsv3 sourcetYpe=stream:smtp "All your datas belong to us" | rex field=_raw "quoted-printable(?<qp>.{1300})" | stats count by substr(qp,1,1300)
- index=botsv3 sourcetype=stream:smtp "All your datas belong to us" | rex field=_raw "boundary=[\\\\\"-]+(?<bnd>[A-Za-z0-9_=-]+)" | stats count by bnd
- index=botsv3 sourcetype=stream:smtp "MWHPR17MB124780ACE6F28E61609F84EABF2B0" | rex field=_raw "namp_(?<fwd>.{1500})" | stats count by substr(fwd,1,1500)
### What it means
Intention: The rex window keeps failing on the escaped raw. Use a different approach: search the forward's raw for the ransom-note body text directly — quoted-printable encodes only special chars, so common ransom phrases would still be searchable if present.
