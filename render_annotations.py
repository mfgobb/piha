#!/usr/bin/env python3
"""Render plant annotations from the session SQLite DB onto garden photos."""
import sqlite3
import os
from PIL import Image, ImageDraw, ImageFont

DB_PATH = "/home/node/.copilot/session-state/389b3882-1f3e-4120-b0e5-3a8c41678155/session.db"
SRC_DIR = "/workspaces/terminal-test"
OUT_DIR = "/workspaces/terminal-test/annotated"

os.makedirs(OUT_DIR, exist_ok=True)

try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
except Exception:
    FONT = ImageFont.load_default()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT image, label, l, t, r, b, color FROM annotations ORDER BY image, id")
rows = cur.fetchall()

by_image = {}
for image, label, l, t, r, b, color in rows:
    by_image.setdefault(image, []).append((label, l, t, r, b, color))

print(f"Found {len(by_image)} images with {len(rows)} annotations total")

processed = 0
for image, anns in sorted(by_image.items()):
    src_path = os.path.join(SRC_DIR, image)
    if not os.path.exists(src_path):
        print(f"MISSING SOURCE: {src_path}")
        continue
    im = Image.open(src_path).convert("RGB")
    w, h = im.size
    draw = ImageDraw.Draw(im)
    for label, l, t, r, b, color in anns:
        x0, y0, x1, y1 = int(l * w), int(t * h), int(r * w), int(b * h)
        draw.rectangle([x0, y0, x1, y1], outline=color, width=8)
        bbox = draw.textbbox((0, 0), label, font=FONT)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        ty = max(0, y0 - th - 20)
        tx = max(0, min(x0, w - tw - 20))
        draw.rectangle([tx - 5, ty - 5, tx + tw + 15, ty + th + 15], fill=color)
        draw.text((tx + 5, ty), label, fill="black", font=FONT)
    out_name = os.path.splitext(image)[0] + "_annotated.jpg"
    out_path = os.path.join(OUT_DIR, out_name)
    im.save(out_path, quality=90)
    processed += 1

print(f"Rendered {processed} annotated images into {OUT_DIR}")
