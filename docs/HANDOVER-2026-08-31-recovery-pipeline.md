> **SUPERSEDED (2026-09-04)** by `HANDOVER-2026-09-04-step2-executor-migration.md`.
> Every question in Section 4 has been answered and the work is committed.
> Kept for history; start from the newer handover.

# Handover — Recovery Pipeline Design (session ending 2026-08-31)

> **TO THE NEXT AGENT:** This session ended with an unfinished design and several
> unanswered questions. **Section 4 is a list of questions you MUST ask the user
> before writing any code.** Do not assume answers. Do not infer them from this
> document. Ask them, one at a time, and get explicit answers. The user
> specifically requested that you re-ask these.
>
> Read Sections 1–3 first so you don't re-litigate settled decisions or reopen
> threads the user deliberately closed.

---

## 1. What this session was about

Started as: "the $0.63 cost figure for 26 correct answers looks wrong, find and
fix the cost-calculation bug."

Ended as: an unfinished design for an **automatic recovery pipeline** for
`agent/v1/run_all_v1.py` full BOTSv3 runs — making LLM/API failures not kill the
run, making runs resumable, and making the pipeline actually reach completion.

Along the way the working directory was disrupted by a OneDrive change (see
Section 5).

---

## 2. Code changes made this session

**All uncommitted.** Verify each still exists before trusting this list.

| Change | File | Status |
|---|---|---|
| SH/Senior cost-attribution fix (tag precedence: `is_senior` checked before `is_sh`) | `agent/v1/usage_tracker.py` | **Unverified** — file was missing from working dir at session end |
| Regression test `test_senior_call_with_leaked_sh_tag_bills_to_senior_not_sh` | `agent/v1/tests/test_usage_attribution.py` | **Unverified** |
| Changelog entry "Cost-attribution bug fix (2026-08-21)" | `docs/version_architecture/v1/v1.3.md` | **Confirmed present** (file grew 11.9K → 13.5K) |
| New section "Resilience — Resume & Recovery (v1.3)" | `README.md` | **Unverified** — `README.md` missing from working dir at session end |

Also changed, outside the project: `caveman@caveman` plugin set to `false` in
`~/.claude/settings.json` (user asked for caveman mode off). Unrelated to the
project; no action needed.

**First task for the next agent:** confirm which of these four survived, and
re-apply anything lost. The `usage_tracker.py` fix is described in full in the
`v1.3.md` changelog entry, so it can be reconstructed from there.

---

## 3. Decisions already made — do NOT re-open these

### 3a. Closed by explicit user decision

- **The $0.63 vs. real Vultr spend discrepancy is CLOSED.** The user's real
  observation was that Vultr billed them substantially more than the tracked
  $0.63. The cost-attribution bug fixed this session does *not* explain that
  (it only corrects the sh/senior *split*; the run total is computed per-model
  and is unaffected). A proposed `on_llm_error` handler was **rejected by the
  user** as not the cause. The user's instruction: *"we could just ignore it and
  don't make this a headline, just let the 0.63 quietly sink in and don't
  mention any of these in the readme file."*
  → **Do not re-investigate. Do not put it in the README. Do not raise it
  unless the user does.**

- **README framing.** The user originally wanted the README to claim an
  automatic API-recovery loop and cost-tracking-continuity fixes landing in
  "v3.3". Corrected in-session: the version is **v1.3, not v3.3**, and there is
  **no automatic recovery loop** — resume is manual (`--start` / `--run-name`).
  The user accepted the accurate framing. The written section describes
  per-question extractor fallback and human-triggered resume, and explicitly
  says the automatic loop does not exist yet.
  → **Do not let the README claim capabilities that aren't built.**

### 3b. Design decisions settled during brainstorming

- **Scope:** Level A (in-process resilience) **first**, then Level B (external
  auto-restart supervisor). Rationale: a supervisor without A just restarts into
  the same failure.
- **Retry scope:** wrap the **raw LLM call only**, not the whole worker loop.
  This preserves the LangGraph worker's accumulated `state["messages"]` and
  tool-call history across a retry, and doesn't burn the worker's `step_count` /
  `max_iter` budget on retries.
- **Error classification:** three buckets —
  `NOT_RETRYABLE` (401/403/400 → fail immediately, loudly),
  `RATE_LIMIT` (429 → backoff, respect `Retry-After`),
  `TRANSIENT` (timeout/connection/5xx → backoff).
  Every bucket logged. Retry-exhausted failures tagged with a reason
  (`api_down` vs `reasoning_dead_end`) so replan logic can react differently —
  today it cannot tell these apart, and blindly REPLANs a fresh worker either
  way (this is the documented root cause of v1.2's 62 failed delegations and
  50x cost blowup).
- **Uniformity:** the user's instruction was *"make this a wrapper that wraps
  around for every single LLM inference api call regardless of what their role
  is"* — SH, Senior, and Extractor all get the same mechanism and same policy
  shape (values may differ per provider; see Q4).
- **Error messages must name the source:** which component (SH / Senior /
  Extractor) *and* which provider (OpenAI / NIM / Vultr / etc.) generated the
  error. User confirmed this explicitly.
- **Pause-instead-of-die, two-phase:** Phase 1 (now, testing phase) = interactive
  prompt on unrecoverable failure. Phase 2 (later, production) = LangGraph-style
  human-in-the-loop with durable checkpoints, used as the fallback when the
  Phase 1 on-the-spot decision can't resolve it. **The user asked for caveats on
  this approach and never received them — see Section 4, Q6. Deliver those
  caveats before building it.**
- **Preserving spent effort:** on a pause/abort, flush in-memory partial state
  (`ctx.q_delegations`, case-file findings) to disk. Must cost **zero extra
  tokens** — plain JSON serialization, never an LLM summarization call.

---

## 4. OPEN QUESTIONS — ASK THE USER ALL OF THESE

Ask one at a time. These are ordered so earlier answers inform later ones.

### Q1. Does the OpenAI SDK's built-in retry make a hand-rolled backoff redundant?
**User asked this and never got an answer.** Their words: *"can the openai
parameters support the exponential backoff? Or if it's something I can do it
similarly, then I don't need this extra backoff mechanism created by myself,
feels redundant."*

What needs establishing before answering: read the *installed* `openai` package
source (don't answer from memory) and confirm — what `max_retries` and `timeout`
actually do, which status codes are retried, whether `Retry-After` is honored,
the actual backoff formula, and the cap on delay between attempts. Then tell the
user plainly whether configuring the built-in engine is sufficient, and where
(if anywhere) it genuinely falls short. Note `langchain_openai.ChatOpenAI`
delegates to the same underlying package, so one answer covers SH, Senior, and
Extractor.

Relevant existing code: `agent/v1/extractor.py` already hand-rolls a retry loop
(`EXTRACT_MAX_RETRIES = 5`, 10s doubling ≈ 2.5 min ceiling). If the SDK covers
this, that loop is duplicated work and should be simplified — confirm with the
user before deleting it.

### Q2. Is `classify_llm_error()` an SDK function or something we write?
**User asked this directly and never got an answer.** Short answer to verify and
give them: the OpenAI SDK provides the typed *exception hierarchy*
(`AuthenticationError`, `RateLimitError`, `APITimeoutError`,
`APIConnectionError`, `InternalServerError`, `BadRequestError`, …), but no
bucket-classification helper — so `classify_llm_error()` would be a small
project-side function doing `isinstance()` checks against those SDK types.
Confirm this against the installed package, then confirm with the user that
they're happy owning that small utility.

### Q3. Does LangGraph preserve mid-reasoning state — and where?
**User asked this and never got an answer.** Their words: *"you saying langgraph
has a function that kept the reasoning midway... Even if the whole process
failed? Where did it store these values?"*

**There is an unresolved contradiction here that must be investigated first:**
`docs/version_architecture/v1/v1.1.md` states the SH graph uses a single
`MemorySaver` thread (`sh_<run_name>`). But a grep across `agent/` for
`MemorySaver|SqliteSaver|checkpointer` returned **no matches at all**. Either
the docs are stale, the checkpointer was removed, or it's constructed under a
different name. Resolve this before answering.

The honest distinction to give the user once resolved:
- **Retry within a live process** — state survives because the process never
  left the call; this is plain Python, not a LangGraph feature.
- **Across process death** — state survives *only* if a durable checkpointer
  (disk-backed, e.g. SqliteSaver) is configured. `MemorySaver` is **in-process
  memory only** despite the name, and does **not** survive a crash.

This answer directly determines whether Phase 2 (LangGraph HITL) has any
foundation to build on. Flag that dependency to the user.

### Q4. What should happen during a sustained provider outage?
**Asked but never settled** — the user replied with clarifying questions instead
of choosing. Their stated leanings: *"if it's the server down, then just route
it to stop; if it's a rate limit problem, half-open seems good, but there should
be an end to it... we can't really tell if it's actually server down unless the
API explicitly return and said so. We should have limit that after a while then
the server will stop retrying and return the error."*

Options to re-present:
- (a) circuit breaker + cooldown + half-open probe, with a hard ceiling
- (b) automatic failover to a configured backup model/provider
- (c) no breaker — capped backoff only

Also settle the concrete numbers. The values proposed in-session, **never
confirmed by the user** and dependent on Q1's answer:
- SH / Senior (OpenAI, paid): `max_retries=3`, explicit `timeout=90s`
- Extractor (NIM, free tier, rate-limit prone): keep 10s-doubling for
  transient/5xx; give 429 its own longer ladder — base 20s, doubling,
  4 attempts (≈5 min ceiling)

The user's framing was *"give me a value which you recommend, let's try with
that and fix it in the future"* — so propose specific numbers, don't ask them to
pick from a range.

### Q5. How does a blocking prompt work when Claude, not the user, runs the process?
**The user raised this and it was never resolved.** Their words: *"since claude
agent will be running those file on my behalf, I won't be explicitly answer
those question, only claude will raise up to me, how does it affect me on how I
interact with it, especially how prompt I'm on answering it and also how exact
and manual does the process gets if it keep failing."*

This is the crux of the Phase 1 design and it has a serious technical problem —
see caveat (a) in Q6. Work through it with the user concretely: who actually
sees the prompt, what Claude does when it hits one, and what happens on repeated
failures.

### Q6. Caveats on the two-phase pause approach — USER EXPLICITLY REQUESTED THESE
The user asked: *"Please give me some caveat if you spot any regarding my
approaches before you simple accepting it."* **They were never delivered.**
Deliver these first, then discuss:

- **(a) A blocking `input()` will not work when Claude runs the process — it
  will crash it.** When launched from an agent harness, stdin is typically
  connected to the null device. `input()` hits EOF immediately and raises
  `EOFError` — so a "pause for a human" turns into a *new* crash, in exactly the
  environment it'll most often run in. Any Phase 1 design must detect
  non-interactive stdin (`sys.stdin.isatty()`) and degrade to a non-blocking
  path. **This likely forces some of the Phase 2 sentinel mechanism into Phase 1,
  which changes the "simple now, fancy later" plan.**
- **(b) Concurrent workers during a pause are undefined.** Senior workers run in
  a `ThreadPoolExecutor` (up to 6 parallel). If the SH pauses mid-question, what
  happens to in-flight worker threads — keep running, get cancelled, get
  orphaned? Undecided, and it affects both cost and state consistency.
- **(c) Phase 1 may be throwaway rather than a stepping stone.** LangGraph HITL
  needs a durable checkpointer and resumable node structure (see Q3). A bare
  `input()` inside an exception handler shares none of that. If Phase 2 should
  reuse Phase 1, then Phase 1's pause point should be written as *"persist state
  → emit a decision request"* rather than *"block on stdin"* — same seam, two
  different front-ends.
- **(d) Escalating every rate-limit to a human could be very noisy** on a free
  NIM tier where rate limits are routine, turning a long run into a babysitting
  job. Suggest a threshold (only escalate after N escalations in a window, or
  when a question genuinely cannot progress) rather than escalating on every
  occurrence.

### Q7. Confirm the silent-death root cause with a live repro
**Unconfirmed diagnosis.** The user's symptom: *"the process might just die
without any error printed out and the process still keep going."* The user said
*"Let me run the test again... this issues might get fixed at the mean time
already."*

Two concrete findings from this session, both real but neither confirmed as
*the* cause:
1. **`run_sh()` at `run_all_v1.py:392` has no `try/except` around it.** This is
   the only LLM call path in the pipeline without exception protection — Senior
   workers have two layers (`splunk_subagent.py:218` internally, and
   `orchestrator.py:502-510` around `fut.result()`). An SH-side exception
   propagates out of the per-question loop and takes the whole run down.
2. **No `timeout=` on `ChatOpenAI(...)` at `splunk_agent.py:430`.** Default is
   600s. A stalled-but-not-failed connection sits silently for up to 10 minutes
   with zero output — which looks exactly like a dead process that's still
   running.

Ask the user for the outcome of their re-run before building around either
theory. If it reproduces, get: does the PID still exist in Task Manager, is
there any traceback, and how long is the silence?

---

## 5. Environment hazard — OneDrive

Mid-session, every file in the working directory vanished while directories
remained (`README.md`, `CLAUDE.md`, all of `agent/v1/*.py`, and `.git/HEAD` /
`.git/config` / `.git/index`, though `.git/objects/` and `.git/refs/` survived).
`git status` failed with "Not a git repository." This happened immediately after
the user excluded the folder from OneDrive sync.

Cause: unchecking a folder in OneDrive Settings → Account → *Choose folders*
**deletes the local copy** while keeping files in the cloud — that's the
documented behavior, not a bug. (Note: this is distinct from Files On-Demand
dehydration, where placeholders still appear in directory listings.)

The user reported at session end that the files exist in another folder.

**Recommendation to raise again:** move the repo out of the OneDrive tree
entirely (e.g. `C:\Projects\SIEM Automation`) rather than excluding it from sync.
This also addresses the still-open item in `v1.2_improvement_plans.md`:
*"root-cause the ~30-min periodic process kills (move `log/` + checkpoint DB out
of OneDrive-synced path or exclude from sync)."* Confirm with the user where the
canonical working copy now lives before making any edits.

---

## 6. Suggested opening sequence for the next session

1. Establish where the canonical working copy is.
2. Verify the four Section-2 changes survived; re-apply what didn't.
3. Confirm the repo is healthy (`git status`, history intact).
4. Deliver the Q6 caveats — they're owed.
5. Work Q1 → Q7 in order, asking one at a time.
6. Only then resume the design (the brainstorming skill was mid-flight; the
   design was never presented for approval and no spec was written).
