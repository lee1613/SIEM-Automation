#!/usr/bin/env python3
"""
Official BOTSv3 hint book. A hint costs HintCost points; a hint-assisted
correct answer scores base - cost (75-990) — strictly better than a wrong 0.
97 hints sat unused through runs 1.0-1.2.
"""

from __future__ import annotations

import csv
from collections import defaultdict


class HintBook:
    def __init__(self, hints_csv: str) -> None:
        self._by_q: dict[int, list[dict]] = defaultdict(list)
        with open(hints_csv, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    num  = int(row["Number"])
                    hnum = int(row["HintNumber"])
                    cost = int(row["HintCost"])
                except (ValueError, KeyError, TypeError):
                    continue
                self._by_q[num].append(
                    {"number": num, "hint_number": hnum,
                     "text": (row.get("Hint") or "").strip(), "cost": cost})
        for lst in self._by_q.values():
            lst.sort(key=lambda h: h["hint_number"])

    def get_hint(self, number: int, hint_number: int) -> dict | None:
        for h in self._by_q.get(number, []):
            if h["hint_number"] == hint_number:
                return h
        return None

    def count_for(self, number: int) -> int:
        return len(self._by_q.get(number, []))
