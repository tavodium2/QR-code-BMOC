import json
import os
import time
import urllib.request
import urllib.error

API_URL = "https://api.monday.com/v2"


def _load_token():
    # Prefer a real environment variable (e.g. set in Render's dashboard).
    env_token = os.environ.get("MONDAY_API_TOKEN")
    if env_token:
        return env_token
    # Fall back to a local .env file for local development.
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.startswith("MONDAY_API_TOKEN="):
                    return line.strip().split("=", 1)[1]
    raise RuntimeError("MONDAY_API_TOKEN not found in environment or .env")


TOKEN = _load_token()


def gql(query, variables=None, max_retries=5):
    body = {"query": query}
    if variables is not None:
        body["variables"] = variables
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Authorization": TOKEN, "Content-Type": "application/json"},
    )
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            result = json.loads(e.read().decode())
        if "errors" in result:
            msg = json.dumps(result["errors"])
            if "Complexity" in msg or "rate limit" in msg.lower() or "minute" in msg.lower():
                wait = 15 * (attempt + 1)
                print(f"  rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            raise RuntimeError(msg)
        return result["data"]
    raise RuntimeError("Max retries exceeded")
