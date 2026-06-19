import sys
import json
import requests
import os
import urllib3

# Disable insecure request warnings for self-signed Splunk certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration (can be overridden by environment variables)
# Default to localhost Splunk
SPLUNK_URL = os.environ.get("SPLUNK_URL", "https://localhost:8089")
SPLUNK_USER = os.environ.get("SPLUNK_USER", "admin")
SPLUNK_PASS = os.environ.get("SPLUNK_PASS", "")  # Set this!

def main():
    if not SPLUNK_PASS and "SPLUNK_PASS" not in os.environ:
        print("Error: SPLUNK_PASS environment variable or config not set.", file=sys.stderr)
        # We don't exit here because the LLM might be able to help fix it
    
    session = requests.Session()
    session.verify = False 
    
    # Standard MCP stdio loop
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue # Ignore malformed lines
            
            # Forward to Splunk MCP endpoint
            # Note: /services/mcp is the endpoint defined in the Splunk_MCP_Server app
            try:
                resp = session.post(
                    f"{SPLUNK_URL.rstrip('/')}/services/mcp",
                    json=request,
                    auth=(SPLUNK_USER, SPLUNK_PASS),
                    params={"output_mode": "json"},
                    timeout=120
                )
                
                if resp.status_code == 200:
                    # The Splunk persistent handler returns the JSON-RPC response directly
                    print(json.dumps(resp.json()), flush=True)
                else:
                    error_msg = f"Splunk error {resp.status_code}"
                    try:
                        error_detail = resp.json()
                        if 'error' in error_detail:
                            error_msg += f": {error_detail['error']}"
                    except:
                        error_msg += f": {resp.text[:100]}"
                        
                    error_resp = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32000,
                            "message": error_msg
                        }
                    }
                    print(json.dumps(error_resp), flush=True)
            except requests.exceptions.RequestException as e:
                error_resp = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Connection error: {str(e)}"
                    }
                }
                print(json.dumps(error_resp), flush=True)
                
        except EOFError:
            break
        except Exception as e:
            error_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Unexpected bridge error: {str(e)}"
                }
            }
            print(json.dumps(error_resp), flush=True)

if __name__ == "__main__":
    main()
