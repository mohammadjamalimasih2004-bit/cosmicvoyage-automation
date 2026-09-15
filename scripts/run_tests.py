#!/usr/bin/env python3
"""
مجموعه تست خودکار پایپ‌لاین. هر مرحله قبل از رفتن به مرحله بعد اعتبارسنجی می‌شود.
استفاده: python run_tests.py --stage <fetch|edit|caption|preflight>
"""
import os
import sys
import json
import subprocess
import argparse

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name} {('- ' + detail) if detail and not condition else ''}")
    return condition


def test_fetch():
    results = []
    src = os.path.join(OUTPUT_DIR, "source.mp4")
    meta = os.path.join(OUTPUT_DIR, "meta.json")

    results.append(check("فایل source.mp4 وجود دارد", os.path.exists(src)))
    if os.path.exists(src):
        size = os.path.getsize(src)
        results.append(check(f"حجم فایل معقول است ({size} bytes)", size > 500_000))

    results.append(check("meta.json وجود دارد", os.path.exists(meta)))
    if os.path.exists(meta):
        with open(meta) as f:
            data = json.load(f)
        results.append(check("meta شامل nasa_id است", "nasa_id" in data))
        results.append(check("meta شامل title است", bool(data.get("title"))))

    if os.path.exists(src):
        results.append(check("فایل صفر بایت نیست", os.path.getsize(src) != 0))

    return all(results)


def test_edit():
    results = []
    final = os.path.join(OUTPUT_DIR, "final.mp4")
    results.append(check("فایل final.mp4 ساخته شده", os.path.exists(final)))
    if not os.path.exists(final):
        return False

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", final],
        capture_output=True, text=True,
    )
    results.append(check("ffprobe بدون خطا فایل را می‌خواند", probe.returncode == 0, probe.stderr[:200]))
    if probe.returncode != 0:
        return False

    info = json.loads(probe.stdout)
    duration = float(info["format"].get("duration", 0))
    results.append(check(f"مدت زمان زیر ۳۰ ثانیه است ({duration:.1f}s)", 0 < duration <= 30))

    video_streams = [s for s in info["streams"] if s["codec_type"] == "video"]
    results.append(check("حداقل یک استریم ویدیو دارد", len(video_streams) >= 1))
    if video_streams:
        w, h = video_streams[0].get("width"), video_streams[0].get("height")
        results.append(check(f"نسبت تصویر ۹:۱۶ است ({w}x{h})", w == 1080 and h == 1920))

    return all(results)


def test_caption():
    results = []
    cap_file = os.path.join(OUTPUT_DIR, "caption.json")
    results.append(check("caption.json وجود دارد", os.path.exists(cap_file)))
    if not os.path.exists(cap_file):
        return False

    with open(cap_file) as f:
        cap = json.load(f)

    results.append(check("فیلد caption غیرخالی است", bool(cap.get("caption", "").strip())))
    tags = cap.get("hashtags", [])
    results.append(check(f"تعداد هشتگ منطقی است ({len(tags)})", 5 <= len(tags) <= 30))
    results.append(check(
        "همه هشتگ‌ها با # شروع می‌شوند",
        all(t.startswith("#") for t in tags), str([t for t in tags if not t.startswith("#")])
    ))
    results.append(check("هشتگ تکراری وجود ندارد", len(tags) == len(set(tags))))

    return all(results)


def test_preflight():
    results = []
    required_env = ["IG_BUSINESS_ID", "IG_ACCESS_TOKEN", "PUBLIC_VIDEO_URL"]
    for var in required_env:
        results.append(check(f"متغیر محیطی {var} ست شده", bool(os.environ.get(var))))

    final = os.path.join(OUTPUT_DIR, "final.mp4")
    cap_file = os.path.join(OUTPUT_DIR, "caption.json")
    results.append(check("فایل نهایی ویدیو آماده است", os.path.exists(final)))
    results.append(check("کپشن نهایی آماده است", os.path.exists(cap_file)))

    if os.path.exists(cap_file):
        with open(cap_file) as f:
            cap = json.load(f)
        full_len = len(cap.get("caption", "")) + sum(len(t) for t in cap.get("hashtags", []))
        results.append(check(f"طول کل کپشن زیر سقف اینستاگرام است ({full_len})", full_len < 2200))

    return all(results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=["fetch", "edit", "caption", "preflight"])
    args = parser.parse_args()

    stage_map = {
        "fetch": test_fetch,
        "edit": test_edit,
        "caption": test_caption,
        "preflight": test_preflight,
    }
    passed = stage_map[args.stage]()
    print(f"\n=== نتیجه مرحله {args.stage}: {'موفق' if passed else 'ناموفق'} ===")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
