import json
import os
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = r"C:\Users\cedri\.config\ofscraper\config.json"

def load_env():
    """Load .env file from the same folder as this script."""
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

def get_webhook_url():
    load_env()
    url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if url:
        return url
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("discord", "")

def build_field(name, processed, unprocessed):
    total = len(processed) + len(unprocessed)
    if total == 0:
        return None
    success = len(processed)
    failed = len(unprocessed)
    value = f"{success} done"
    if failed:
        value += f" / {failed} failed"
    if processed:
        value += f"\n{', '.join(processed)}"
    return {"name": name, "value": value, "inline": False}

def main():
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    raw = sys.stdin.read()
    if not raw.strip():
        print("No input received on stdin", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw)
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("No Discord webhook URL configured", file=sys.stderr)
        sys.exit(1)

    fields = []
    for label, key_prefix in [
        ("Downloads", "download"),
        ("Likes", "like"),
        ("Unlikes", "unlike"),
        ("Paid Scrapes", "scrape_paid"),
    ]:
        processed = data.get(f"{key_prefix}_processed_users", [])
        unprocessed = data.get(f"{key_prefix}_unprocessed_users", [])
        field = build_field(label, processed, unprocessed)
        if field:
            fields.append(field)

    if not fields:
        description = "No models were processed this run."
    else:
        description = "Here's a summary of everything that ran."

    embed = {
        "title": "OF-Scraper run complete",
        "description": description,
        "color": 0x3498DB,  # blue
        "fields": fields,
    }

    payload = {
        "username": "OF-Scraper",
        "embeds": [embed],
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=req_data,
        headers={"Content-Type": "application/json", "User-Agent": "OF-Scraper/1.0"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"Discord summary sent (HTTP {resp.status})")
    except Exception as e:
        print(f"Failed to send Discord summary: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
