#!/usr/bin/env python3
"""
آپلود ویدیوی نهایی به عنوان Reel در اینستاگرام از طریق Instagram Graph API.
نیاز: IG_BUSINESS_ID, IG_ACCESS_TOKEN, PUBLIC_VIDEO_URL
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")
IG_BUSINESS_ID = os.environ.get("IG_BUSINESS_ID")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
PUBLIC_VIDEO_URL = os.environ.get("PUBLIC_VIDEO_URL")
CAPTION_FILE = os.path.join(OUTPUT_DIR, "caption.json")

GRAPH_BASE = "https://graph.facebook.com/v21.0"


def api_call(url, data=None, method="POST"):
    if data:
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main():
    missing = [
        name for name, val in [
            ("IG_BUSINESS_ID", IG_BUSINESS_ID),
            ("IG_ACCESS_TOKEN", IG_ACCESS_TOKEN),
            ("PUBLIC_VIDEO_URL", PUBLIC_VIDEO_URL),
        ] if not val
    ]
    if missing:
        print(f"[ERROR] متغیرهای زیر تنظیم نشده: {missing}", file=sys.stderr)
        return 1

    with open(CAPTION_FILE) as f:
        cap = json.load(f)

    full_caption = cap["caption"] + "\n\n" + cap.get("cta", "") + "\n\n" + " ".join(cap["hashtags"])

    container = api_call(
        f"{GRAPH_BASE}/{IG_BUSINESS_ID}/media",
        {
            "media_type": "REELS",
            "video_url": PUBLIC_VIDEO_URL,
            "caption": full_caption,
            "access_token": IG_ACCESS_TOKEN,
        },
    )
    if "id" not in container:
        print(f"[ERROR] ساخت container شکست خورد: {container}", file=sys.stderr)
        return 1
    creation_id = container["id"]

    for attempt in range(20):
        status = api_call(
            f"{GRAPH_BASE}/{creation_id}?fields=status_code&access_token={IG_ACCESS_TOKEN}",
            method="GET",
        )
        code = status.get("status_code")
        print(f"[INFO] وضعیت پردازش: {code} (تلاش {attempt+1}/20)", file=sys.stderr)
        if code == "FINISHED":
            break
        if code == "ERROR":
            print(f"[ERROR] پردازش اینستاگرام fail شد: {status}", file=sys.stderr)
            return 1
        time.sleep(15)
    else:
        print("[ERROR] Timeout در انتظار پردازش ویدیو", file=sys.stderr)
        return 1

    publish = api_call(
        f"{GRAPH_BASE}/{IG_BUSINESS_ID}/media_publish",
        {"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
    )
    if "id" not in publish:
        print(f"[ERROR] پابلیش شکست خورد: {publish}", file=sys.stderr)
        return 1

    print(json.dumps({"status": "published", "media_id": publish["id"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
