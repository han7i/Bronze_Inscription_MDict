# -*- coding: utf-8 -*-
"""Final stats, a sample entry dump, and workspace cleanup."""
import glob
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_tools", "vendor"))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")
from mdict_utils import reader  # noqa: E402

recs = json.load(open(os.path.join(DATA, "records.json"), encoding="utf-8"))
meta = json.load(open(os.path.join(DATA, "meta.json"), encoding="utf-8"))

print("== corpus ==")
heads = {}
for r in recs:
    heads.setdefault(r["main"], []).append(r)
print(f"records={len(recs):,} heads={len(heads):,} books={len(meta['books'])} periods={len(meta['periods'])}")
n = sorted(len(v) for v in heads.values())
print(f"glyphs/head: min=1 median={n[len(n)//2]} mean={sum(n)/len(n):.2f} max={n[-1]}  heads with 1 glyph={sum(1 for x in n if x==1):,}")
for b in meta["books"]:
    rr = [r for r in recs if r["book"] == b]
    print(f"  {b:<8} records={len(rr):>6,}  heads={len({r['main'] for r in rr}):>5,}")

print("\n== assets ==")
for sub in ("glyphs", "inline-glyphs", "fonts"):
    d = os.path.join(SITE, "assets", sub)
    c = s = 0
    for dp, _, fs in os.walk(d):
        for f in fs:
            c += 1
            s += os.path.getsize(os.path.join(dp, f))
    print(f"  {sub:<14} {c:>7,} files {s/1048576:8.1f} MB")

print("\n== build artifacts ==")
base = os.path.join(ROOT, "金文字形全編")
print(f"  mdx {os.path.getsize(base+'.mdx')/1048576:.2f} MB")
print(f"  mdd {os.path.getsize(base+'.mdd')/1048576:.1f} MB")
keys = list(reader.get_keys(base + ".mdx"))
print(f"  entries {len(keys):,}")
ig = os.path.join(ROOT, "_build", "staging", "ig")
print(f"  inline glyph pngs staged: {len(os.listdir(ig)):,}")

print("\n== sample entry ==")
body = reader.query(base + ".mdx", "一")
print(f"  '一' -> {len(body or ''):,} chars, {body.count('<img')} images")
open(os.path.join(ROOT, "_src", "sample_一.html"), "w", encoding="utf-8").write(body.replace("\x00", ""))
body = reader.query(base + ".mdx", "寶")
print(f"  '寶' -> {len(body or ''):,} chars, {body.count('<img')} images")
body = reader.query(base + ".mdx", "未編碼字頭一覽")
print(f"  index -> {len(body or ''):,} chars, {body.count('<img')} thumbs")
body = reader.query(base + ".mdx", "㕊")
print(f"  alias '㕊' -> {body!r}"[:120])

print("\n== cleanup ==")
for p in [os.path.join(ROOT, "_src", "repo.zip"),
          os.path.join(ROOT, "_build", "staging"),
          os.path.join(ROOT, "_build_smoke"),
          os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", ".github")]:
    if os.path.exists(p):
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
        print("  removed", os.path.relpath(p, ROOT))
for p in glob.glob(os.path.join(ROOT, "_src", "_tmp.png")):
    os.remove(p)

print("\n== folder size ==")
tot = 0
for dp, _, fs in os.walk(ROOT):
    for f in fs:
        tot += os.path.getsize(os.path.join(dp, f))
print(f"  {tot/1048576:.0f} MB total in workspace")
for d in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, d)
    if os.path.isdir(p):
        s = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(p) for f in fs)
        print(f"    {d:<16} {s/1048576:8.1f} MB")
