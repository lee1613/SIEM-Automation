"""
Local scoreboard grader — bypasses Splunk KV store entirely.

KV Store is unavailable on this host (disabled in server.conf, seemingly a
Mac-incompatibility with the mongod bundled in this Splunk build), so
ScoreboardClient (agent/scoreboard_client.py) can't read ctf_answers /
ctf_questions. This module grades answers directly against the official
botsv3content CSVs instead, using the same comparison rule as the real
scoreboard controller:

    submitted.lower().strip() == correct.lower().strip()

Public API mirrors ScoreboardClient so it's a drop-in swap in run_all_v1.py:
    LocalScoreboard(questions_csv, answers_csv, results_path)
        .submit(question_number, agent_answer) -> SubmitResult
        .get_score()                            -> dict
        .get_all_submissions()                  -> list[dict]
"""

import csv
import json
import os
import time

from scoreboard_client import SubmitResult


class LocalScoreboard:
    def __init__(self, questions_csv: str, answers_csv: str, results_path: str,
                 user: str = "local"):
        self.user         = user
        self.results_path = results_path
        self._answers     = self._load_answers(answers_csv)
        self._points      = self._load_points(questions_csv)
        self._submissions: list[dict] = []
        if os.path.exists(results_path):
            with open(results_path, "r", encoding="utf-8") as f:
                self._submissions = json.load(f)

    @staticmethod
    def _load_answers(path: str) -> dict[str, str]:
        with open(path, "r", encoding="utf-8", newline="") as f:
            return {row["Number"]: row["Answer"] for row in csv.DictReader(f)}

    @staticmethod
    def _load_points(path: str) -> dict[str, int]:
        with open(path, "r", encoding="utf-8", newline="") as f:
            return {row["Number"]: int(row["BasePoints"]) for row in csv.DictReader(f)}

    def submit(self, question_number: int, agent_answer: str) -> SubmitResult:
        key            = str(question_number)
        correct_answer = self._answers.get(key)
        base_points    = self._points.get(key, 0)

        if correct_answer is None:
            return SubmitResult(number=question_number, answer=agent_answer,
                                 correct=False, base_points=0, earned=0)

        correct = agent_answer.lower().strip() == correct_answer.lower().strip()
        earned  = base_points if correct else 0

        self._submissions.append({
            "time":            time.time(),
            "number":          question_number,
            "submitted":       agent_answer,
            "official":        correct_answer,
            "correct":         correct,
            "base_points":     base_points,
            "earned":          earned,
        })
        with open(self.results_path, "w", encoding="utf-8") as f:
            json.dump(self._submissions, f, indent=2, ensure_ascii=False)

        return SubmitResult(number=question_number, answer=agent_answer,
                             correct=correct, base_points=base_points, earned=earned)

    def get_score(self) -> dict:
        total = sum(s["earned"] for s in self._submissions if s["correct"])
        count = sum(1 for s in self._submissions if s["correct"])
        return {"total_points": total, "correct_count": count, "user": self.user}

    def get_all_submissions(self) -> list[dict]:
        return list(self._submissions)
