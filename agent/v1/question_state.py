#!/usr/bin/env python3
"""
Per-question budget and accounting for the v1.4 conversational loop.

Every number in spec §4 lives here, and nothing here calls a model — the whole
termination story (§4.2) is therefore unit-testable without a run.

Two budgets, independently exhaustible, which is why both are named:
  * ROUNDS  — per senior (v1.4.1). Every senior is granted the tier's full
              round count when it spawns, so a replacement is not left with the
              question's leftovers. Rounds run out for the QUESTION only when
              every spawn slot is used and no active senior has a round left.
  * TURNS   — SH turns. A CLARIFY consumes a turn but no round, so a question
              can run out of turns with rounds left, or the reverse.

Waves (one parallel round of senior work, read by one SH turn, §4.3) are still
counted for reporting, but no longer cap anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ROUND_ITERS = 12         # iterations per senior round (v1.4.1: was 8, ~3-5 SPL searches)
MAX_EXPLORATIONS = 1     # §2.3 — a second scout means the first failed

# base_points -> budget. Read with tier_budget(); the floors are 1000/500/else.
TIERS: dict[int, dict] = {
    1000: {"seniors": 3, "rounds": 8, "sh_turns": 12},
    500:  {"seniors": 2, "rounds": 5, "sh_turns": 8},
    100:  {"seniors": 1, "rounds": 3, "sh_turns": 5},
}


def tier_budget(points: int) -> dict:
    """Budget for a question worth `points`. Unknown/absent points get the base tier."""
    for floor in (1000, 500):
        if (points or 0) >= floor:
            return {"tier": floor, **TIERS[floor], "iters": ROUND_ITERS}
    return {"tier": 100, **TIERS[100], "iters": ROUND_ITERS}


@dataclass
class QuestionState:
    """Mutable accounting for one question. One instance per question, never shared."""

    points: int = 0
    waves_used: int = 0
    turns_used: int = 0
    spawns_used: int = 0
    explorations_used: int = 0
    granted: dict = field(default_factory=dict)      # sid -> rounds granted at spawn
    used: dict = field(default_factory=dict)         # sid -> rounds actually worked
    r2_streak: dict = field(default_factory=dict)    # sid -> consecutive R2 FAILs
    retired: set = field(default_factory=set)
    capped: dict = field(default_factory=dict)       # sid -> last round ran out of iterations

    def __post_init__(self) -> None:
        self.budget = tier_budget(self.points)

    # ── clocks ────────────────────────────────────────────────────────────────
    @property
    def slots_remaining(self) -> int:
        return max(0, self.budget["seniors"] - self.spawns_used)

    @property
    def turns_remaining(self) -> int:
        return max(0, self.budget["sh_turns"] - self.turns_used)

    @property
    def senior_iteration_ceiling(self) -> int:
        """§4.1 — the number the first smoke test has to be measured against."""
        return self.budget["seniors"] * self.budget["rounds"] * ROUND_ITERS

    def record_wave(self) -> None:
        self.waves_used += 1

    def record_turn(self) -> None:
        self.turns_used += 1

    def exhausted(self) -> str:
        """'' while the question can continue; else which budget ran out."""
        if self.turns_remaining <= 0:
            return "turns"
        if self.slots_remaining <= 0 and not any(
                self.is_active(sid) and self.rounds_left_for(sid) > 0 for sid in self.granted):
            return "rounds"
        return ""

    # ── spawn slots ───────────────────────────────────────────────────────────
    def can_spawn_senior(self) -> bool:
        return self.spawns_used < self.budget["seniors"]

    def can_spawn_exploration(self) -> bool:
        return self.explorations_used < MAX_EXPLORATIONS

    def open_senior(self, sid: str) -> int:
        """Consume a slot and grant this senior its rounds. Returns the grant."""
        if not self.can_spawn_senior():
            raise ValueError(f"no senior slots left ({self.spawns_used}/{self.budget['seniors']})")
        self.spawns_used += 1
        grant = self.budget["rounds"]
        self.granted[sid] = grant
        self.used[sid] = 0
        self.r2_streak[sid] = 0
        return grant

    def open_exploration(self, sid: str) -> None:
        """An exploration worker is one-shot, ungraded, and outside the slot economy."""
        if not self.can_spawn_exploration():
            raise ValueError("exploration already used on this question")
        self.explorations_used += 1

    def refund_spawn(self, sid: str) -> None:
        """A transport failure is not a reasoning outcome (§7) — give the slot back."""
        self.spawns_used = max(0, self.spawns_used - 1)
        self.retire(sid)

    # ── per-senior rounds ─────────────────────────────────────────────────────
    def record_round(self, sid: str, *, capped: bool = False) -> None:
        self.used[sid] = self.used.get(sid, 0) + 1
        self.capped[sid] = bool(capped)

    def last_round_capped(self, sid: str) -> bool:
        """Did this senior's most recent round run out of iterations? A capped
        round stopped where the budget ran out, not where the work finished —
        §3.5 blocks an ANSWER sourced from one."""
        return bool(self.capped.get(sid, False))

    def rounds_left_for(self, sid: str) -> int:
        return max(0, self.granted.get(sid, 0) - self.used.get(sid, 0))

    def retire(self, sid: str) -> None:
        self.retired.add(sid)

    def is_active(self, sid: str) -> bool:
        return sid in self.granted and sid not in self.retired

    # ── anti-thrash (§3.4) ────────────────────────────────────────────────────
    def record_r2(self, sid: str, *, failed: bool) -> None:
        self.r2_streak[sid] = (self.r2_streak.get(sid, 0) + 1) if failed else 0

    def continue_blocked(self, sid: str) -> bool:
        return self.r2_streak.get(sid, 0) >= 2
