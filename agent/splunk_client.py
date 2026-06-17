"""
Splunk REST API client for local Splunk Enterprise.
Connects via the management port (default 8089) using session-key auth.
"""

import time
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

disable_warnings(InsecureRequestWarning)


class SplunkClient:
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip("/")
        self.session = requests.Session()
        self.session.verify = False
        self._login(username, password)

    def _login(self, username: str, password: str) -> None:
        resp = self.session.post(
            f"{self.host}/services/auth/login",
            data={"username": username, "password": password, "output_mode": "json"},
        )
        resp.raise_for_status()
        token = resp.json()["sessionKey"]
        self.session.headers["Authorization"] = f"Splunk {token}"

    def search(
        self,
        query: str,
        earliest: str = "0",
        latest: str = "now",
        max_results: int = 100,
    ) -> dict:
        """Submit a blocking SPL search and return results."""
        # Splunk REST API requires 'search' keyword except for generating commands
        spl = query.strip()
        generating = ("| ", "|metadata", "metadata ", "tstats ", "datamodel ", "inputlookup ", "makeresults")
        if not spl.startswith("search ") and not any(spl.startswith(g) for g in generating):
            spl = f"search {spl}"

        # Create job
        resp = self.session.post(
            f"{self.host}/services/search/jobs",
            data={
                "search": spl,
                "earliest_time": earliest,
                "latest_time": latest,
                "output_mode": "json",
            },
        )
        resp.raise_for_status()
        sid = resp.json()["sid"]

        # Poll until done
        while True:
            status = self.session.get(
                f"{self.host}/services/search/jobs/{sid}",
                params={"output_mode": "json"},
            ).json()
            entry = status["entry"][0]["content"]
            state = entry["dispatchState"]
            if state == "DONE":
                break
            if state == "FAILED":
                return {"error": f"Search failed: {entry.get('messages', '')}"}
            time.sleep(1)

        # Fetch results
        results = self.session.get(
            f"{self.host}/services/search/jobs/{sid}/results",
            params={"output_mode": "json", "count": max_results},
        ).json()

        event_count = entry.get("resultCount", 0)
        results["_meta"] = {
            "total_event_count": event_count,
            "returned": min(max_results, event_count),
            "sid": sid,
        }
        return results

    def list_indexes(self) -> list[str]:
        """Return names of all indexes (excluding internal ones)."""
        resp = self.session.get(
            f"{self.host}/services/data/indexes",
            params={"output_mode": "json", "count": 0},
        )
        resp.raise_for_status()
        return [
            e["name"]
            for e in resp.json()["entry"]
            if not e["name"].startswith("_")
        ]

    def get_sourcetypes(self, index: str = "botsv3", top_n: int = 30) -> dict:
        """Return sourcetypes in an index sorted by event count."""
        return self.search(
            f"index={index} | stats count by sourcetype | sort -count | head {top_n}",
            earliest="0",
            max_results=top_n,
        )

    def get_field_values(self, field: str, index: str = "botsv3", top_n: int = 20) -> dict:
        """Return top values for a field in an index."""
        return self.search(
            f"index={index} | top limit={top_n} {field}",
            earliest="0",
            max_results=top_n,
        )
