"""
Splunk CTF Scoreboard client — REST API implementation.

The SA-ctf_scoreboard web controller cannot load on Splunk 9/10 (Windows)
because its bundled splunklib uses the removed `six.moves` module. This
client replicates the controller's logic directly via the Splunk REST API:

  1. Read the correct answer from the ctf_answers KV store (admin app).
  2. Compare using the same rule: submitted.lower().strip() == answer.lower().strip()
  3. Write the submission to index=scoreboard so the dashboard reflects it.

Public API
----------
ScoreboardClient(splunkd_url, username, password)
    .submit(question_number, agent_answer)  -> SubmitResult
    .get_score()                            -> dict
    .get_all_submissions()                  -> list[dict]
"""

import json
import time

import requests

requests.packages.urllib3.disable_warnings()


class SubmitResult:
    def __init__(self, number: int, answer: str, correct: bool,
                 base_points: int, earned: int):
        self.number      = number
        self.answer      = answer
        self.correct     = correct
        self.base_points = base_points
        self.earned      = earned  # points actually awarded

    def __repr__(self):
        status = "CORRECT" if self.correct else "INCORRECT"
        return (f"Q{self.number}: {status}  earned={self.earned}/{self.base_points}pts"
                f"  submitted={self.answer!r}")


class ScoreboardClient:
    """
    Thin REST-API client for the SA-ctf_scoreboard KV stores.

    Uses Splunk session-key auth; no browser session required.
    """

    def __init__(self, splunkd_url: str, username: str, password: str):
        self.base    = splunkd_url.rstrip("/")
        self.user    = username
        self._pass   = password
        self._sess   = requests.Session()
        self._sess.verify  = False
        self._hdr    = None   # set on first call to _ensure_auth()
        self._answers_cache: dict[str, str] = {}   # number -> answer

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _ensure_auth(self):
        if self._hdr:
            return
        r = self._sess.post(
            f"{self.base}/services/auth/login",
            data={"username": self.user, "password": self._pass,
                  "output_mode": "json"},
        )
        r.raise_for_status()
        token = r.json()["sessionKey"]
        self._hdr = {"Authorization": f"Splunk {token}"}

    # ── KV store helpers ──────────────────────────────────────────────────────

    def _kv_get_all(self, app: str, collection: str) -> list[dict]:
        self._ensure_auth()
        r = self._sess.get(
            f"{self.base}/servicesNS/nobody/{app}/storage/collections/data/{collection}",
            headers=self._hdr,
            params={"output_mode": "json", "count": 0},
        )
        if r.status_code == 401:
            # Session token expired mid-run — re-authenticate and retry once.
            self._hdr = None
            self._ensure_auth()
            r = self._sess.get(
                f"{self.base}/servicesNS/nobody/{app}/storage/collections/data/{collection}",
                headers=self._hdr,
                params={"output_mode": "json", "count": 0},
            )
        r.raise_for_status()
        return r.json()

    def _kv_insert(self, app: str, collection: str, record: dict):
        self._ensure_auth()
        r = self._sess.post(
            f"{self.base}/servicesNS/nobody/{app}/storage/collections/data/{collection}",
            headers=self._hdr,
            json=record,
        )
        return r

    # ── Answer lookup ─────────────────────────────────────────────────────────

    def _get_correct_answer(self, number: int) -> str | None:
        """Return the correct answer for a question number (cached)."""
        key = str(number)
        if key not in self._answers_cache:
            rows = self._kv_get_all("SA-ctf_scoreboard_admin", "ctf_answers")
            for row in rows:
                self._answers_cache[row["Number"]] = row["Answer"]
        return self._answers_cache.get(key)

    def _get_base_points(self, number: int) -> int:
        """Return BasePoints for a question number."""
        self._ensure_auth()
        rows = self._kv_get_all("SA-ctf_scoreboard", "ctf_questions")
        for row in rows:
            if row.get("Number") == str(number):
                return int(row.get("BasePoints", 0))
        return 0

    # ── Submission ────────────────────────────────────────────────────────────

    def submit(self, question_number: int, agent_answer: str) -> SubmitResult:
        """
        Submit an answer and return a SubmitResult.

        Uses the same comparison as the original scoreboard controller:
            submitted.lower().strip() == correct.lower().strip()
        """
        self._ensure_auth()

        correct_answer = self._get_correct_answer(question_number)
        base_points    = self._get_base_points(question_number)

        if correct_answer is None:
            return SubmitResult(
                number=question_number, answer=agent_answer,
                correct=False, base_points=0, earned=0,
            )

        # Mirror the controller's exact comparison
        correct = agent_answer.lower().strip() == correct_answer.lower().strip()
        earned  = base_points if correct else 0

        # Log submission to index=scoreboard (mirrors what the controller does)
        self._log_submission(question_number, agent_answer, correct_answer,
                             correct, base_points, earned)

        return SubmitResult(
            number=question_number, answer=agent_answer,
            correct=correct, base_points=base_points, earned=earned,
        )

    def _log_submission(self, number: int, submitted: str, official: str,
                        correct: bool, base_pts: int, earned: int):
        """Write a submission event to index=scoreboard via the REST receivers endpoint."""
        result_str = "Correct" if correct else "Incorrect"
        # Keep answers from corrupting the comma/quote-delimited event format.
        submitted = submitted.replace('"', "'")
        official  = official.replace('"', "'")
        # Format mirrors the original controller log line so the scoreboard
        # dashboard's SPL (which parses these fields) works correctly.
        event_line = (
            f'tcode={int(time.time())},'
            f'user="{self.user}",'
            f'Number={number},'
            f'Result={result_str},'
            f'BasePointsAwarded={earned},'
            f'SpeedBonusAwarded=0,'
            f'AdditionalBonusAwarded=0,'
            f'Penalty=0,'
            f'Answer="{submitted}",'
            f'AnswerOfficial="{official}"'
        )
        # This event IS the scoreboard's scoring record (get_score() sums these),
        # so a failed write must surface, not vanish. Retry once with a fresh
        # session token, then raise.
        for attempt in (1, 2):
            try:
                r = self._sess.post(
                    f"{self.base}/services/receivers/simple",
                    headers=self._hdr,
                    params={"sourcetype": "scoreboard", "index": "scoreboard",
                            "source": "scoreboard_controller"},
                    data=event_line.encode("utf-8"),
                )
                r.raise_for_status()
                return
            except Exception:
                if attempt == 2:
                    raise
                self._hdr = None
                self._ensure_auth()

    # ── Score summary ─────────────────────────────────────────────────────────

    def get_score(self) -> dict:
        """Return current score from the scoreboard index."""
        self._ensure_auth()
        # Use rex-only extraction to avoid issues with special chars in user name
        escaped_user = self.user.replace('"', '\\"')
        spl = (
            'search index=scoreboard sourcetype=scoreboard '
            '| rex field=_raw "user=\\"(?P<user>[^\\"]+)\\"" '
            '| rex field=_raw "Number=(?P<Number>[0-9]+)" '
            '| rex field=_raw "Result=(?P<Result>[^,]+)" '
            '| rex field=_raw "BasePointsAwarded=(?P<pts>[0-9]+)" '
            f'| search user="{escaped_user}" Result=Correct '
            '| dedup Number '
            '| stats sum(pts) as total_points count as correct_count'
        )
        r = self._sess.post(
            f"{self.base}/services/search/jobs/export",
            headers=self._hdr,
            data={"search": spl, "earliest_time": "0", "latest_time": "now",
                  "output_mode": "json"},
        )
        total, count = 0, 0
        for line in r.text.splitlines():
            try:
                obj = json.loads(line)
                if obj.get("result"):
                    total = int(float(obj["result"].get("total_points") or 0))
                    count = int(float(obj["result"].get("correct_count") or 0))
            except Exception:
                pass
        return {"total_points": total, "correct_count": count, "user": self.user}

    def get_all_submissions(self) -> list[dict]:
        """Return all submissions this user has made (from scoreboard index)."""
        self._ensure_auth()
        escaped_user = self.user.replace('"', '\\"')
        spl = (
            'search index=scoreboard sourcetype=scoreboard '
            '| rex field=_raw "user=\\"(?P<user>[^\\"]+)\\"" '
            '| rex field=_raw "Number=(?P<Number>[0-9]+)" '
            '| rex field=_raw "Result=(?P<Result>[^,]+)" '
            '| rex field=_raw "BasePointsAwarded=(?P<BasePointsAwarded>[0-9]+)" '
            f'| search user="{escaped_user}" '
            '| table _time Number Result BasePointsAwarded'
        )
        r = self._sess.post(
            f"{self.base}/services/search/jobs/export",
            headers=self._hdr,
            data={"search": spl, "earliest_time": "0", "latest_time": "now",
                  "output_mode": "json", "count": 0},
        )
        rows = []
        for line in r.text.splitlines():
            try:
                obj = json.loads(line)
                if obj.get("result"):
                    rows.append(obj["result"])
            except Exception:
                pass
        return rows
