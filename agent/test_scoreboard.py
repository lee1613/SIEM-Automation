"""Quick smoke test: login to scoreboard and submit Q1 answer (splunk)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()
from scoreboard_client import ScoreboardClient

SPLUNKD  = "https://localhost:8089"
USER     = os.getenv("SPLUNK_USER")
PASSWORD = os.getenv("SPLUNK_PASS")

print(f"Connecting as {USER}...")
sb = ScoreboardClient(SPLUNKD, USER, PASSWORD)

print("Submitting Q1 answer 'splunk'...")
result = sb.submit(1, "splunk")
print(f"  {result}")

print("\nSubmitting Q200 correct answer 'bstoll,btun,splunk_access,web_admin'...")
result2 = sb.submit(200, "bstoll,btun,splunk_access,web_admin")
print(f"  {result2}")

print("\nSubmitting Q200 wrong answer...")
result3 = sb.submit(200, "wrong_answer")
print(f"  {result3}")

print("\nScore summary:")
print(f"  {sb.get_score()}")
