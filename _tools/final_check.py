# -*- coding: utf-8 -*-
"""Last checks: residual unrenderable glyphs, and HTML artefacts in every entry."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_tools", "vendor"))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")
from mdict_utils import reader  # noqa: E402

recs = json.load(open(os.path.join(DATA, "records.json"), encoding="utf-8"))
inline = json.load(open(os.path.join(DATA, "inline_glyphs.json"), encoding="utf-8"))
staged = set(os.listdir(os.path.join(ROOT, "_build", "staging", "ig"))) if os.path.isdir(
    os.path.join(ROOT, "_build", "staging", "ig")) else set()

NO_IMG = [0x4C8EE, 0x45160]
hits = [r for r in recs if any(chr(cp) in (r["title"] + r["sub"] + r["main"]) for cp in NO_IMG)]
print(f"records referencing the 2 unrenderable codepoints: {len(hits)}")
for r in hits[:5]:
    print(f"   {r['main']!r} / {r['title']!r} / {r['source']!r}")

print("\nentries scan:")
base = os.path.join(ROOT, "金文字形全編")
keys = list(reader.get_keys(base + ".mdx"))
bad = 0
no_img_entries = 0
for k in keys:
    body = reader.query(base + ".mdx", k) or ""
    if "None" in body or "nan" == body[:3] or "<img class=\"ig\" src=\"ig/" not in body and "None" in body:
        bad += 1
    if any(chr(cp) in body for cp in NO_IMG):
        no_img_entries += 1
print(f"  entries with 'None' text: {bad}")
print(f"  entries still containing the 2 dead codepoints: {no_img_entries}")
print(f"  total entries: {len(keys):,}")
