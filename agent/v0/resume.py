#!/usr/bin/env python3
"""Wave-level resume for one in-flight question (v0.4.4).

Before v0.4.4 everything a question held lived in RAM - SH's messages, the
QuestionState, the premise ledger, every senior's thread - so a paused or killed
process re-ran the question from zero and re-paid for every wave already finished.

`run_question` now snapshots at every turn boundary, i.e. at the top of its loop,
after the previous turn and its wave are fully applied. That is the only point where
the state is consistent by construction: mid-wave, some seniors have written to the
ledger and some have not. So there is no separate flush on error - the last boundary
is already on disk, and whatever was in flight when the process died is simply re-run.

Senior threads are exported from each graph's MemorySaver into the snapshot and
written back onto the same thread_id on resume. Moving the checkpointer to SQLite
would persist every step instead, including half-finished rounds that would then need
rolling back to the boundary.

The snapshot holds the conversation, never the prompt: system messages are rebuilt
from the current code on resume. It is removed once the question is recorded.

ponytail: pickle, not JSON. Every object here is already picklable, and a class that
gains a field between the pause and the resume restores without it - delete the
snapshot folder to start that question fresh.
"""

from __future__ import annotations

import os
import pickle
import shutil

_FILE = "snapshot.pkl"


def snapshot_dir(run_dir: str, qid: str) -> str:
    return os.path.join(run_dir, "resume_state", qid)


def _write(path: str, obj) -> None:
    """Atomic: a crash mid-write leaves the previous boundary intact."""
    with open(path + ".tmp", "wb") as fh:
        pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(path + ".tmp", path)


def _read(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return pickle.load(fh)


def save(run_dir: str, qid: str, payload: dict) -> None:
    d = snapshot_dir(run_dir, qid)
    os.makedirs(d, exist_ok=True)
    _write(os.path.join(d, _FILE), payload)


def load(run_dir: str, qid: str) -> dict | None:
    return _read(os.path.join(snapshot_dir(run_dir, qid), _FILE))


def clear(run_dir: str, qid: str) -> None:
    shutil.rmtree(snapshot_dir(run_dir, qid), ignore_errors=True)


def save_history(run_dir: str, history: dict) -> None:
    """SH's cross-question memory, {qid: [messages]}, so a resumed process renders
    the same memory (v0.4.5)."""
    _write(os.path.join(run_dir, "sh_history.pkl"), dict(history))


def load_history(run_dir: str) -> dict:
    """An old flat message list (before v0.4.5) loads as one unnamed segment: it has
    no summary, so it is the first thing the memory swap drops."""
    got = _read(os.path.join(run_dir, "sh_history.pkl")) or {}
    return {"": list(got)} if isinstance(got, list) else got
