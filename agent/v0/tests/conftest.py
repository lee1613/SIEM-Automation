import os
import sys

AGENT_V1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # agent/v0
AGENT    = os.path.dirname(AGENT_V1)                                    # agent
for p in (AGENT, AGENT_V1):
    if p not in sys.path:
        sys.path.insert(0, p)
