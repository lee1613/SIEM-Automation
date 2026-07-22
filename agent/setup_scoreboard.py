#!/usr/bin/env python3
"""
One-time setup script for SA-ctf_scoreboard on local Splunk Enterprise.

Steps performed:
  1. Write scoreboard_controller.config with admin credentials + random VKEY
  2. Create $SPLUNK_HOME/var/log/scoreboard/  log directory
  3. Restart Splunk (so the apps are recognised)
  4. Load questions into ctf_questions KV store  (SA-ctf_scoreboard)
  5. Load answers  into ctf_answers  KV store  (SA-ctf_scoreboard_admin)
  6. Load hints    into ctf_hints    KV store  (SA-ctf_scoreboard_admin)
  7. Create a default CTF EULA entry and accept it for the admin user
  8. Create a ctf_users entry for admin so the scoreboard can track score

Usage:
    python agent/setup_scoreboard.py

Run from project root or agent/ directory after both SA-ctf_scoreboard apps
have been cloned into $SPLUNK_HOME/etc/apps/.
"""

import os, sys, csv, json, time, uuid, subprocess, secrets
import requests
requests.packages.urllib3.disable_warnings()

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, SCRIPT_DIR)
from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

SPLUNK_HOME = r"C:\Program Files\Splunk"
SPLUNK_USER = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS = os.getenv("SPLUNK_PASS", "")
BASE_URL    = "https://localhost:8089"

CONTENT_DIR = os.path.join(PROJECT_ROOT, "datasets", "botsv3")

SESS = requests.Session()
SESS.verify = False


def auth_header():
    r = SESS.post(f"{BASE_URL}/services/auth/login",
                  data={"username": SPLUNK_USER, "password": SPLUNK_PASS, "output_mode": "json"})
    r.raise_for_status()
    token = r.json()["sessionKey"]
    return {"Authorization": f"Splunk {token}"}


def kv_post(app: str, collection: str, records: list, headers: dict):
    """Bulk-insert records into a KV store collection via the REST API."""
    # Clear existing records first
    endpoint = f"{BASE_URL}/servicesNS/nobody/{app}/storage/collections/data/{collection}"
    del_r = SESS.delete(endpoint, headers=headers)
    if del_r.status_code not in (200, 404):
        print(f"  Warning: DELETE {collection} returned {del_r.status_code}")

    ok = 0
    for rec in records:
        r = SESS.post(endpoint, json=rec, headers=headers)
        if r.status_code in (200, 201):
            ok += 1
        else:
            print(f"  ! INSERT failed ({r.status_code}): {r.text[:120]}")
    print(f"  Loaded {ok}/{len(records)} records into {app}/{collection}")
    if ok != len(records):
        # The collection was cleared above; a partial load means missing answers
        # would silently score correct submissions as wrong on every future run.
        sys.exit(f"FATAL: only {ok}/{len(records)} records loaded into "
                 f"{app}/{collection} — re-run setup before using the scoreboard.")


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # Drop _key column — KV store generates its own keys
    for row in rows:
        row.pop("_key", None)
    return rows


# ── Step 1: Write scoreboard_controller.config ────────────────────────────────

def write_config():
    vkey = secrets.token_hex(32)
    cfg_path = os.path.join(
        SPLUNK_HOME, "etc", "apps", "SA-ctf_scoreboard",
        "appserver", "controllers", "scoreboard_controller.config"
    )
    with open(cfg_path, "w") as f:
        f.write("[ScoreboardController]\n")
        f.write(f"USER = {SPLUNK_USER}\n")
        f.write(f"PASS = {SPLUNK_PASS}\n")
        f.write(f"VKEY = {vkey}\n")
    print(f"[1] Config written: {cfg_path}")
    return vkey


# ── Step 2: Create log directory ───────────────────────────────────────────────

def create_log_dir():
    log_dir = os.path.join(SPLUNK_HOME, "var", "log", "scoreboard")
    os.makedirs(log_dir, exist_ok=True)
    print(f"[2] Log directory: {log_dir}")


# ── Step 3: Restart Splunk ─────────────────────────────────────────────────────

def restart_splunk():
    print("[3] Restarting Splunk via REST API...")
    try:
        headers = auth_header()
        r = SESS.post(f"{BASE_URL}/services/server/control/restart",
                      headers=headers, data={"output_mode": "json"})
        print(f"    Restart triggered: HTTP {r.status_code}")
    except Exception as e:
        print(f"    Restart request error (expected during shutdown): {e}")

    print("    Polling until Splunk is back up (up to 120s)...")
    for i in range(40):
        time.sleep(3)
        try:
            r = SESS.get(f"{BASE_URL}/services/server/info",
                         params={"output_mode": "json"}, timeout=5)
            if r.status_code == 200:
                print(f"    Splunk is up (after ~{(i+1)*3}s).")
                return
        except Exception:
            pass
        if i % 5 == 0:
            print(f"    ... still waiting ({(i+1)*3}s)")
    print("    Warning: Splunk may not be fully up yet. Continuing anyway.")


# ── Step 4-6: Load KV store data ──────────────────────────────────────────────

def load_kv_data(headers: dict):
    # Questions -> SA-ctf_scoreboard
    questions = load_csv(os.path.join(CONTENT_DIR, "ctf_questions.csv"))
    print(f"[4] Loading {len(questions)} questions -> SA-ctf_scoreboard/ctf_questions")
    kv_post("SA-ctf_scoreboard", "ctf_questions", questions, headers)

    # Answers -> SA-ctf_scoreboard_admin
    answers = load_csv(os.path.join(CONTENT_DIR, "ctf_answers.csv"))
    print(f"[5] Loading {len(answers)} answers -> SA-ctf_scoreboard_admin/ctf_answers")
    kv_post("SA-ctf_scoreboard_admin", "ctf_answers", answers, headers)

    # Hints -> SA-ctf_scoreboard_admin
    hints = load_csv(os.path.join(CONTENT_DIR, "ctf_hints.csv"))
    print(f"[6] Loading {len(hints)} hints -> SA-ctf_scoreboard_admin/ctf_hints")
    kv_post("SA-ctf_scoreboard_admin", "ctf_hints", hints, headers)


# ── Step 7: Create EULA and acceptance ────────────────────────────────────────

def setup_eula(headers: dict):
    eula_id  = "botsv3"
    eula_rec = {
        "EulaId":      eula_id,
        "EulaName":    "BOTSv3 Competition Rules",
        "EulaDefault": "true",
        "EulaContent": "By participating you agree to use the data for educational purposes only.",
    }
    kv_post("SA-ctf_scoreboard", "ctf_eulas", [eula_rec], headers)

    accepted_rec = {
        "EulaId":          eula_id,
        "EulaName":        "BOTSv3 Competition Rules",
        "EulaUsername":    SPLUNK_USER,
        "EulaDateAccepted": str(int(time.time())),
    }
    kv_post("SA-ctf_scoreboard", "ctf_eulas_accepted", [accepted_rec], headers)
    print(f"[7] EULA accepted for user '{SPLUNK_USER}'")


# ── Step 8: Create ctf_users entry ────────────────────────────────────────────

def setup_user(headers: dict):
    user_rec = {
        "Username":        SPLUNK_USER,
        "FirstName":       "SIEM",
        "LastName":        "Agent",
        "DisplayUsername": "siem_agent",
        "Team":            "AutoAgent",
        "Email":           "",
        "Event":           "BOTSv3",
    }
    kv_post("SA-ctf_scoreboard", "ctf_users", [user_rec], headers)
    print(f"[8] CTF user entry created for '{SPLUNK_USER}'")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not SPLUNK_PASS:
        sys.exit("SPLUNK_PASS not set in .env")

    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-restart", action="store_true",
                    help="Skip Splunk restart (use if already restarted)")
    ns = ap.parse_args()

    write_config()
    create_log_dir()
    if not ns.skip_restart:
        restart_splunk()
    else:
        print("[3] Skipping restart (--skip-restart)")

    print("Authenticating to Splunk REST API...")
    headers = auth_header()
    print("  Authenticated.\n")

    load_kv_data(headers)
    setup_eula(headers)
    setup_user(headers)

    print("\nSetup complete.")
    print(f"  Scoreboard UI : http://localhost:8000/en-US/app/SA-ctf_scoreboard/")
    print(f"  Admin UI      : http://localhost:8000/en-US/app/SA-ctf_scoreboard_admin/")


if __name__ == "__main__":
    main()
