"""
Splunk REST API client for local Splunk Enterprise.
Connects via the management port (default 8089) using session-key auth.
"""

import re
import time

import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

disable_warnings(InsecureRequestWarning)


def _scope(sourcetype: str = "", source: str = "") -> str:
    """Build the shared ` sourcetype="x" source="y"` filter.

    Two axes, not one. BOTSv3 hides whole feeds under a generic sourcetype -
    78,459 Cisco NVM flow events sit under sourcetype=syslog and are reachable
    only by source="cisconvmflowdata" - so every discovery helper has to be able
    to name either axis, or both.
    """
    parts = []
    if sourcetype:
        parts.append('sourcetype="%s"' % sourcetype.replace('"', ""))
    if source:
        parts.append('source="%s"' % source.replace('"', ""))
    return (" " + " ".join(parts)) if parts else ""


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
        generating = ("|", "metadata ", "tstats ", "datamodel ", "inputlookup ", "makeresults")
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

        # Poll until done. raise_for_status so an expired session surfaces as
        # HTTPError (the pool's 401-retry catches it) instead of a KeyError;
        # the deadline stops a QUEUED/PAUSED job from holding a pool slot forever.
        deadline = time.time() + 600
        while True:
            r = self.session.get(
                f"{self.host}/services/search/jobs/{sid}",
                params={"output_mode": "json"},
            )
            r.raise_for_status()
            entry = r.json()["entry"][0]["content"]
            state = entry["dispatchState"]
            if state == "DONE":
                break
            if state == "FAILED":
                return {"error": f"Search failed: {entry.get('messages', '')}"}
            if time.time() > deadline:
                return {"error": f"Search timed out after 600s (state={state}, sid={sid})"}
            time.sleep(1)

        # Fetch results
        r = self.session.get(
            f"{self.host}/services/search/jobs/{sid}/results",
            params={"output_mode": "json", "count": max_results},
        )
        r.raise_for_status()
        results = r.json()

        event_count = entry.get("resultCount", 0)
        results["_meta"] = {
            "total_event_count": event_count,
            "returned": min(max_results, event_count),
            "sid": sid,
        }
        return results


    def get_field_values(self, field: str, index: str = "botsv3", top_n: int = 20,
                         sourcetype: str = "", source: str = "") -> dict:
        """Return top values for a field, optionally scoped to a sourcetype and/or source."""
        field = re.sub(r'["|]', "", field)          # keep LLM args inside the SPL term
        st_filter = _scope(sourcetype, source)
        return self.search(
            f"index={index}{st_filter} | top limit={top_n} {field}",
            earliest="0",
            max_results=top_n,
        )

    def get_sourcetype_fields(self, sourcetype: str = "", index: str = "botsv3",
                              min_count: int = 1, source: str = "") -> dict:
        """Return all fields in a sourcetype and/or source ranked by event count —
        equivalent to SQL INFORMATION_SCHEMA. Either axis may be given."""
        return self.search(
            f'index={index}{_scope(sourcetype, source)} | fieldsummary maxvals=3 '
            f'| where count >= {min_count} '
            f'| table field, count, distinct_count, values | sort -count',
            earliest="0",
            max_results=200,
        )

    def sample_events(self, sourcetype: str = "", index: str = "botsv3", keyword: str = "",
                      count: int = 3, source: str = "") -> dict:
        """Return raw events from a sourcetype and/or source, optionally keyword-filtered."""
        keyword = re.sub(r'["|]', " ", keyword).strip()   # keep LLM args inside the SPL term
        kw = f' "{keyword}"' if keyword else ""
        return self.search(
            f'index={index}{_scope(sourcetype, source)}{kw} | head {count} | table _time _raw',
            earliest="0",
            max_results=count,
        )

    def get_sources(self, index: str = "botsv3", sourcetype: str = "",
                    keyword: str = "", top_n: int = 100) -> dict:
        """Enumerate `source` values with their sourcetype and event count.

        Returned with counts and paired sourcetypes rather than as a bare list:
        a flat dump of every source is both larger and harder to navigate than
        the same data ranked by volume.
        """
        keyword = re.sub(r'["|]', " ", keyword).strip()
        kw = f" *{keyword}*" if keyword else ""
        return self.search(
            f"index={index}{_scope(sourcetype)}{kw} "
            f"| stats count by source, sourcetype | sort -count | head {top_n}",
            earliest="0",
            max_results=top_n,
        )
