#!/usr/bin/env python3
"""
دانلود ویدیوی HD رایگان از NASA Image and Video Library API.
منبع: images-api.nasa.gov (بدون نیاز به کلید API، ۱۰۰٪ رایگان و رسمی)
"""
import os
import sys
import json
import random
import urllib.request
import urllib.parse

NASA_SEARCH_URL = "https://images-api.nasa.gov/search"
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")
DOWNLOAD_LOG = os.path.join(OUTPUT_DIR, "used_ids.json")

TOPICS = [
    "galaxy", "nebula", "black hole", "supernova", "mars surface",
    "jupiter", "saturn rings", "solar flare", "earth from space",
    "milky way", "moon surface", "astronaut spacewalk", "exoplanet"
]


def load_used_ids():
    if os.path.exists(DOWNLOAD_LOG):
        with open(DOWNLOAD_LOG, "r") as f:
            return set(json.load(f))
    return set()


def save_used_id(nasa_id, used_ids):
    used_ids.add(nasa_id)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(DOWNLOAD_LOG, "w") as f:
        json.dump(sorted(used_ids), f, ensure_ascii=False, indent=2)


def search_nasa_videos(topic):
    params = {"q": topic, "media_type": "video", "year_start": "2015"}
    url = f"{NASA_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return data.get("collection", {}).get("items", [])


def get_video_asset_url(nasa_id):
    asset_url = f"https://images-api.nasa.gov/asset/{nasa_id}"
    with urllib.request.urlopen(asset_url, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    items = data.get("collection", {}).get("items", [])
    mp4_candidates = [i["href"] for i in items if i["href"].endswith(".mp4")]
    if not mp4_candidates:
        return None
    mp4_candidates.sort(key=lambda h: ("orig" not in h and "large" not in h))
    return mp4_candidates[0]


def download_file(url, dest_path):
    urllib.request.urlretrieve(url, dest_path)
    return os.path.getsize(dest_path)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    used_ids = load_used_ids()

    random.shuffle(TOPICS)
    for topic in TOPICS:
        items = search_nasa_videos(topic)
        random.shuffle(items)
        for item in items:
            nasa_id = item["data"][0]["nasa_id"]
            title = item["data"][0].get("title", topic)
            if nasa_id in used_ids:
                continue
            video_url = get_video_asset_url(nasa_id)
            if not video_url:
                continue
            dest = os.path.join(OUTPUT_DIR, "source.mp4")
            print(f"[OK] در حال دانلود: {title} ({nasa_id})", file=sys.stderr)
            size = download_file(video_url, dest)
            if size < 500_000:
                os.remove(dest)
                continue
            save_used_id(nasa_id, used_ids)
            meta = {
                "nasa_id": nasa_id,
                "title": title,
                "topic": topic,
                "description": item["data"][0].get("description", ""),
                "source_file": dest,
            }
            with open(os.path.join(OUTPUT_DIR, "meta.json"), "w") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print(json.dumps(meta, ensure_ascii=False))
            return 0

    print("[ERROR] هیچ ویدیوی جدیدی پیدا نشد", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
