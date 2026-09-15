#!/usr/bin/env python3
"""
ادیت خودکار ویدیو با ffmpeg:
- کراپ به فرمت ۹:۱۶ (ریلز/استوری)
- برش به حداکثر ۳۰ ثانیه
- افزودن موزیک با فید این/اوت
"""
import os
import sys
import subprocess
import shlex

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")
SOURCE = os.path.join(OUTPUT_DIR, "source.mp4")
MUSIC = os.path.join(OUTPUT_DIR, "music.mp3")
FINAL = os.path.join(OUTPUT_DIR, "final.mp4")
MAX_DURATION = 28


def run(cmd):
    print(f"[RUN] {cmd}", file=sys.stderr)
    result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed: {cmd}")
    return result


def get_duration(path):
    cmd = (
        f'ffprobe -v error -show_entries format=duration '
        f'-of default=noprint_wrappers=1:nokey=1 "{path}"'
    )
    result = run(cmd)
    return float(result.stdout.strip())


def main():
    if not os.path.exists(SOURCE):
        print("[ERROR] فایل منبع پیدا نشد", file=sys.stderr)
        return 1

    duration = get_duration(SOURCE)
    clip_len = min(MAX_DURATION, duration)
    has_music = os.path.exists(MUSIC)

    vf = (
        "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',"
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920"
    )

    if has_music:
        cmd = (
            f'ffmpeg -y -i "{SOURCE}" -i "{MUSIC}" '
            f'-t {clip_len} -vf "{vf}" '
            f'-filter:a "afade=t=in:st=0:d=1,afade=t=out:st={clip_len-1}:d=1" '
            f'-map 0:v:0 -map 1:a:0 -shortest '
            f'-c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k '
            f'"{FINAL}"'
        )
    else:
        cmd = (
            f'ffmpeg -y -i "{SOURCE}" -t {clip_len} -vf "{vf}" '
            f'-c:v libx264 -preset medium -crf 20 -an "{FINAL}"'
        )

    run(cmd)

    final_size = os.path.getsize(FINAL)
    if final_size < 200_000:
        print("[ERROR] فایل خروجی خیلی کوچک است، احتمالا ادیت خراب شده", file=sys.stderr)
        return 1

    print(f"[OK] ویدیوی نهایی ساخته شد: {FINAL} ({final_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
