# Future Work

Deferred items. Each is a deliberate decision to *not* do something yet, with the reason it
was deferred and the condition that should trigger it. Nothing here is a bug — these are
known limits of the current design, recorded so they are not rediscovered.

---

## 1. Dataset setup: make the agent's briefing portable across indexes

**Status:** deferred, 2026-09-15.

The SH agent opens every question with a static briefing of the dataset's sourcetypes and
its busiest sources, generated from `agent/botsv3_fields.json`, which
`agent/build_manifest.py` populates from a live Splunk instance.

This works because BOTSv3 is **static**. The data never changes, so a file generated once
stays correct and no Splunk round-trip is needed per run. That is the right trade for a
fixed CTF dataset and the wrong one for anything else.

**What is missing:** a setup step that, given any index, discovers what it contains and
writes the agent's briefing material. The pieces already exist — `sync_sourcetypes()` and
`sync_sources()` in `build_manifest.py` are index-parameterised and read Splunk's metadata
catalogue rather than scanning events, so they cost ~1s regardless of index size. What is
missing is the surrounding workflow: choosing an index, validating the connection,
regenerating the manifest, and reporting what changed.

**Trigger:** the first time this agent is pointed at an index other than `botsv3`.

**Watch out for:** `| metadata`'s `totalCount` is bucket-derived and unreliable — it
reports `source=lsof` at 103 events where `stats count` reports 322,336. Volume ranking
must come from `stats`; `metadata` is trustworthy only for names and for
`firstTime`/`lastTime`. `build_manifest.py` already splits the two commands on that line.

---

## 2. NIM models are priced at zero, so run costs are understated

**Status:** accepted gap, 2026-09-15.

Every NIM model in `PRICES_PER_1M` (`agent/v1/usage_tracker.py`) is priced at **$0.00**:

| model | role |
|---|---|
| `nvidia/nemotron-3-super-120b-a12b` | extractor, exploration agent |
| `deepseek-ai/DeepSeek-V4-Flash` | available, unused |
| `meta/llama-3.3-70b-instruct` | retired |
| `Nemotron-Cascade-2-30B-A3B` | available, unused |

This is deliberate. NIM carries exactly the roles that are cheap and intentionally
low-reasoning, and zeroing them keeps reported cost focused on the expensive reasoning
models where optimisation actually pays off. Every run total in `docs/scoreboard_result/`
therefore reflects **OpenAI spend only**.

**Why this must change before scaling:** the architecture pushes work *toward* the cheap
tier on purpose — the exploration agent exists precisely so discovery does not run on
`gpt-5.4`. The more that strategy succeeds, the larger the unpriced fraction of the system
becomes, and the more a "cost" figure measures the wrong thing. At 56 questions the error
is tolerable. At scale, a cost model blind to the tier doing most of the work cannot
support any decision about where to spend.

**Trigger:** before any run whose cost figure will be compared against a non-NIM
configuration, or before running at a volume where NIM billing is material.

**To close it:** take real per-1M rates from build.nvidia.com (model → API → pricing),
populate the four rows above, and cross-check one run against the NVIDIA dashboard the way
`usage_tracker.py`'s module docstring already prescribes for OpenAI.

---

## 3. Unmeasured: does the joiner's LLM synthesis step earn its keep?

**Status:** open question, 2026-09-15.

v1.3 cut the verifier, the adjudicator, and 3× self-consistency sampling on evidence (see
`docs/version_architecture/v1/v1.3.md`). The **joiner** survived that cut, but its LLM half
has never been isolated either.

What has receipts is the *deterministic* guard wrapped around it: on run_1.2,
`grounded=True` → 26/45 correct, `grounded=False` → **0/11**. What has no receipts is the
synthesis call itself — nobody has compared "joiner LLM picks from the ledger" against
"take `best_candidate(ledger)` deterministically and skip the call entirely."

**Trigger:** after v1.3's first run produces per-question data. The experiment is cheap:
`best_candidate` already exists and runs on the same ledger, so the second arm is a
one-line substitution.

---

## 4. Confidence is recorded but not calibrated

**Status:** instrument shipped, control loop deferred, 2026-09-15.

v1.3 has SH emit a `confidence` (0–100) per spawn, and `agent/v1/spawn_report.py` tallies
solved-rate by confidence decile. The originally proposed rule — *"decompose whenever
confidence < 50"* — was **not** implemented.

**Why:** routing cost on a number whose calibration is unknown is backwards, and no
confidence value had ever been emitted by this system, so there was not one sample to
calibrate against. Worse, the failure mode is asymmetric: these are hard questions over an
index SH has never queried, so low self-reported confidence is the *expected* output, and
"low confidence → more spawns" degenerates into "always fan out to the 6-task cap." Fan-out
stays governed by that existing cap instead.

**Trigger:** once one run has produced `(confidence, outcome)` pairs. Then set the
threshold from the decile table rather than from 50 being a round number. Note also that
per-spawn confidences do not currently sum to 100 — decide whether they should mean
"independent probability" or "share of belief" before gating on them, because `< 50` has a
fixed point under the second reading and none under the first.

---

## 5. The Cisco NVM add-on is missing, so Q216's official answer is not reproducible here

**Status:** verified against live Splunk, 2026-09-15. Not a code defect — an environment gap.

Q216 asks *"According to the Cisco NVM flow logs, for how many seconds does the endpoint
generate Monero cryptocurrency?"* Official answer: `1666`.

There is **no `cisco:nvm:flowdata` sourcetype in this index**. The NVM data lands as
`sourcetype=syslog, source=cisconvmflowdata` — raw, unparsed syslog, because the Cisco NVM
add-on is not installed. The official answer was computed against the add-on's parsed
fields; locally the agent must hand-derive everything from the payload.

Two traps follow from that, and both are general, not specific to this question:

1. **`fst` and `fet` are human-readable strings, not epochs.** A record reads
   `fss="1534762025" fst="Mon Aug 20 10:47:05 2018" fes="1534762137" fet="Mon Aug 20
   10:48:57 2018"`. The epoch pair is `fss`/`fes`. `| eval duration=fet-fst` returns
   **null with no error** — Splunk drops the column silently, so a worker sees an empty
   result and concludes the data is not there. Two v1.3 workers were on the correct feed
   and both returned empty values this way.

2. **`1666` is not reachable from the local data.** Using `fes-fss` correctly, brute-forced
   across groupings by `sa`, `da`, `dp`, `pn`, `ppn`, `udid` and `liuidp`, with sum, span,
   and interval-union:

   | interpretation | value |
   |---|---|
   | sum(dur), `192.168.70.186 -> 45.77.53.176:443`, `ppn=powershell.exe` | **1660** |
   | sum(dur), same host pair, all ports, `ppn=powershell.exe` | 1772 |
   | interval union, same | 1527 |
   | span `max(fes)-min(fss)` | 7065 |
   | agent's v1.3 answer (`max(_time)-min(_time)`, Sysmon + stream) | 7071 |

   The closest is 1660, six seconds short. The only exact `1666` anywhere in the feed is
   `SearchUI.exe -> 204.79.197.254` — Bing, unrelated.

**Trigger:** install `Splunk_TA_cisco-nvm` (or equivalent) and re-index, then re-check
whether the parsed `duration` field yields 1666. Until then Q216 is not winnable on exact
match, and it should not be read as an agent-reasoning failure. Consider dropping it from
the default hard set for the same reason.
