# -*- coding: utf-8 -*-
"""Second pass: head-word alphabet, chars.json semantics, image specs, entry size."""
import json
import os
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")

with open(os.path.join(DATA, "records.json"), encoding="utf-8") as f:
    recs = json.load(f)
with open(os.path.join(DATA, "chars.json"), encoding="utf-8") as f:
    chars = json.load(f)


def block(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def kind(ch):
    cp = ord(ch)
    if 0xE000 <= cp <= 0xF8FF:
        return "PUA"
    if 0x20000 <= cp <= 0x3FFFF:
        return "CJK-ExtB+"
    if 0x3400 <= cp <= 0x4DBF:
        return "CJK-ExtA"
    if 0x4E00 <= cp <= 0x9FFF:
        return "CJK-basic"
    if cp < 0x2E80:
        return "ASCII/punct"
    return f"other(U+{cp:04X})"


block("main head character composition")
c = collections.Counter()
for r in recs:
    m = r["main"]
    if not m:
        c["EMPTY"] += 1
    elif len(m) == 1:
        c[kind(m)] += 1
    else:
        c[f"multi-char(len={len(m)})"] += 1
for k, v in c.most_common():
    print(f"   {k:<22} {v:>7,}")

mains = collections.Counter(r["main"] for r in recs)
heads = list(mains)
print(f"\ndistinct heads: {len(heads)}")
print("single-char heads:", sum(1 for h in heads if len(h) == 1))
print("PUA heads:", sum(1 for h in heads if len(h) == 1 and 0xE000 <= ord(h) <= 0xF8FF))
print("sample PUA heads:", [h for h in heads if len(h) == 1 and 0xE000 <= ord(h) <= 0xF8FF][:8])
print("sample multi heads:", [h for h in heads if len(h) > 1][:12])

block("PUA usage inside text fields")
for field in ("title", "source", "period"):
    n = sum(1 for r in recs if any(0xE000 <= ord(ch) <= 0xF8FF for ch in str(r.get(field, ""))))
    print(f"   {field}: {n:,} records contain PUA chars")

block("chars.json semantics")
print("entries:", len(chars))
diff = [(k, v) for k, v in chars.items() if v != k]
print("value != key:", len(diff))
for k, v in diff[:8]:
    print(f"   {k!r} -> {v!r}")
ids_like = sum(1 for v in chars.values() if any(ch in v for ch in "⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻"))
print("values containing IDS operators:", ids_like)
print("value length histogram:", collections.Counter(len(v) for v in chars.values()).most_common(8))
for probe in ("金", "水", "寶", "鑄", "𩒳"):
    print(f"   {probe!r} -> {chars.get(probe)!r}")

block("componentHead field")
comps = collections.Counter(r["componentHead"] for r in recs)
print("distinct componentHead:", len(comps))
print("sample:", comps.most_common(10))
print("len histogram:", collections.Counter(len(r["componentHead"]) for r in recs).most_common(6))

block("book / head cross-tab")
by_book = collections.Counter(r["book"] for r in recs)
print("records:", dict(by_book))
head_books = collections.defaultdict(set)
for r in recs:
    head_books[r["main"]].add(r["book"])
print("heads appearing in >1 book:", sum(1 for v in head_books.values() if len(v) > 1))

block("glyph image specs")
from PIL import Image
import glob

files = glob.glob(os.path.join(SITE, "assets", "glyphs", "*", "*.webp"))[:5]
for p in files:
    with Image.open(p) as im:
        print(f"   {os.path.basename(p)}  {im.size}  mode={im.mode}  {os.path.getsize(p) / 1024:.1f} KB")
sizes = collections.Counter()
mode = collections.Counter()
for p in glob.glob(os.path.join(SITE, "assets", "glyphs", "*", "*.webp"))[::400]:
    with Image.open(p) as im:
        sizes[im.size] += 1
        mode[im.mode] += 1
print("sampled sizes:", sizes.most_common(5))
print("sampled modes:", mode.most_common(3))

block("estimated MDX entry payload")
heads_sorted = sorted(mains)
tot = 0
big = []
for h in heads_sorted:
    n = mains[h]
    # crude: one table row per glyph + img tag
    est = n * (140 + len(h))
    tot += est
    big.append((n, h))
big.sort(reverse=True)
print(f"rough HTML payload for all heads: {tot / 1048576:.1f} MB")
print("largest heads:", big[:6])
print("records per head: mean=%.1f median=%d" % (
    sum(mains.values()) / len(mains),
    sorted(mains.values())[len(mains) // 2]))
