#!/usr/bin/env python3
"""
دانلود موزیک رایگان و بدون کپی‌رایت از Pixabay Music API.
نیاز: PIXABAY_API_KEY
"""
import os
import sys
import json
import random
import urllib.request
import urllib.parse

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")
API_KEY = os.environ.get("PIXABAY_API_KEY")

MOODS = ["space ambient", "cinematic epic", "calm ambient", "documentary"]


def main():
    if not API_KEY:
        print("[ERROR] PIXABAY_API_KEY تنظیم نشده", file=sys.stderr)
        return 1

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    mood = random.choice(MOODS)
    params = {"key": API_KEY, "q": mood, "audio_type": "music"}
    url = f"https://pixabay.com/api/videos/music/?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"[ERROR] Pixabay API failed: {e}", file=sys.stderr)
        print("[FALLBACK] از موزیک پشتیبان محلی استفاده کن", file=sys.stderr)
        return 2

    hits = data.get("hits", [])
    if not hits:
        return 2

    track = random.choice(hits)
    dest = os.path.join(OUTPUT_DIR, "music.mp3")
    urllib.request.urlretrieve(track["audio_url"], dest)
    print(json.dumps({"music_file": dest, "mood": mood}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
