#!/usr/bin/env python3
"""
تولید دیسکریپشن و هشتگ فارسی/انگلیسی با مدل رایگان OpenRouter (DeepSeek).
سه نسخه تولید می‌شود و بهترین انتخاب می‌گردد.
نیاز: OPENROUTER_API_KEY
"""
import os
import sys
import json
import urllib.request

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")
API_KEY = os.environ.get("OPENROUTER_API_KEY")
META_FILE = os.path.join(OUTPUT_DIR, "meta.json")
CAPTION_FILE = os.path.join(OUTPUT_DIR, "caption.json")

MODEL = "deepseek/deepseek-chat-v3-0324:free"

SYSTEM_PROMPT = (
    "تو یک متخصص سوشال مدیا و نجوم هستی. فقط خروجی JSON بده، بدون هیچ متن اضافه، "
    "بدون بک‌تیک مارک‌داون. فرمت خروجی دقیقا: "
    '{"caption": "متن فارسی جذاب کوتاه", "hashtags": ["#..","#.."], "cta": "متن دعوت به اکشن"}'
)


def call_openrouter(prompt):
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    text = data["choices"][0]["message"]["content"].strip()
    text = text.strip("`").replace("json\n", "").strip()
    return json.loads(text)


def score_candidate(c):
    tag_count = len(c.get("hashtags", []))
    caption_len = len(c.get("caption", ""))
    tag_score = 1 if 15 <= tag_count <= 30 else 0
    len_score = 1 if 60 <= caption_len <= 300 else 0
    return tag_score + len_score


def main():
    if not API_KEY:
        print("[ERROR] OPENROUTER_API_KEY تنظیم نشده", file=sys.stderr)
        return 1
    if not os.path.exists(META_FILE):
        print("[ERROR] meta.json پیدا نشد - اول fetch_nasa.py را اجرا کن", file=sys.stderr)
        return 1

    with open(META_FILE) as f:
        meta = json.load(f)

    prompt = (
        f"موضوع ویدیو: {meta['title']}\n"
        f"توضیح ناسا: {meta.get('description', '')[:400]}\n"
        f"برای یک ریل اینستاگرام فارسی درباره‌ی این موضوع فضایی، "
        f"یک کپشن جذاب فارسی (بدون قرار دادن هشتگ داخل کپشن)، "
        f"۲۰ هشتگ ترکیبی فارسی/انگلیسی مرتبط با نجوم و ترند، "
        f"و یک جمله دعوت به اکشن (فالو/کامنت) تولید کن."
    )

    candidates = []
    for _ in range(3):
        try:
            candidates.append(call_openrouter(prompt))
        except Exception as e:
            print(f"[WARN] یک تلاش شکست خورد: {e}", file=sys.stderr)

    if not candidates:
        print("[ERROR] هیچ کپشنی تولید نشد", file=sys.stderr)
        return 1

    best = max(candidates, key=score_candidate)
    with open(CAPTION_FILE, "w") as f:
        json.dump(best, f, ensure_ascii=False, indent=2)

    print(json.dumps(best, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
