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

def send_discord_notification(username, action, model_id, avatar_url=None):
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("No Discord webhook URL configured in config.json", file=sys.stderr)
        sys.exit(1)

    embed = {
        "title": f"Download completed for {username}",
        "description": f"**Action:** {action}\n**Model ID:** {model_id}",
        "color": 0x2ECC71,  # green
    }

    if avatar_url:
        embed["thumbnail"] = {"url": avatar_url}

    payload = {
        "username": "OF-Scraper",
        "embeds": [embed],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "OF-Scraper/1.0"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"Discord notification sent for {username} (HTTP {resp.status})")
    except Exception as e:
        print(f"Failed to send Discord notification: {e}", file=sys.stderr)

def main():
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    raw = sys.stdin.read()
    if not raw.strip():
        print("No input received on stdin", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw)
    username = data.get("username", "Unknown")
    action = data.get("action", "download")
    model_id = data.get("model_id", "N/A")

    userdata = data.get("userdata") or {}
    avatar_url = userdata.get("avatar") if isinstance(userdata, dict) else None

    send_discord_notification(username, action, model_id, avatar_url)

if __name__ == "__main__":
    main()
