# -*- coding: utf-8 -*-
"""Profile component (构件) data before designing the component section."""
import json
import os
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")

OPS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻")


def block(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


recs = json.load(open(os.path.join(DATA, "records.json"), encoding="utf-8"))
chars = json.load(open(os.path.join(DATA, "chars.json"), encoding="utf-8"))

heads = sorted({r["main"] for r in recs})
print(f"heads: {len(heads):,}   chars.json entries: {len(chars):,}")

for probe in ("寶", "剛", "岡", "鑄"):
    print(f"\n{probe} -> {chars.get(probe)!r}"[:400])


def components_of(value):
    """chars.json values flatten the whole IDS tree: 'char IDS comp subids ...'."""
    toks = value.split()
    out = set()
    for t in toks[1:]:
        if len(t) != 1:
            continue
        if t in OPS:
            continue
        if not t.isprintable():
            continue
        out.add(t)
    return out


block("parsed components")
comp_of_head = {}
for h in heads:
    v = chars.get(h)
    if not v:
        continue
    comp_of_head[h] = components_of(v)

print(f"single-char heads with IDS: {len(comp_of_head):,}")
for probe in ("寶", "剛", "岡", "鑄"):
    if probe in comp_of_head:
        print(f"   {probe}: {''.join(sorted(comp_of_head[probe]))}  ({len(comp_of_head[probe])})")

# reverse index
containing = collections.defaultdict(set)
for h, comps in comp_of_head.items():
    for c in comps:
        containing[c].add(h)

print(f"\ndistinct components: {len(containing):,}")
counts = sorted((len(v), c) for c, v in containing.items())
print("components by #heads:", collections.Counter(
    ("1" if n == 1 else "2-5" if n <= 5 else "6-20" if n <= 20 else "21-100" if n <= 100 else ">100")
    for n, _ in counts))

block("top components")
for n, c in sorted(counts, reverse=True)[:20]:
    print(f"   {c}  {n:>4} heads   (is head: {c in heads})")

block("the 辶 / 辵 case")
for c in ("辶", "辵", "辶", "⻌", "⻍"):
    print(f"   {c!r}: heads={len(containing.get(c, ()))}  is_head={c in heads}")
for c in ("岡", "刂", "山", "金", "口", "木"):
    print(f"   {c!r}: heads={len(containing.get(c, ()))}  is_head={c in heads}  sample={sorted(containing.get(c, ()))[:8]}")

block("entry inventory after adding components")
comp_only = [c for c in containing if c not in heads]
print(f"components that are not heads (new key-only entries): {len(comp_only):,}")
print("sample:", comp_only[:20])
print(f"heads that are components: {sum(1 for h in heads if h in containing):,}")
print(f"heads with neither IDS nor as component: "
      f"{sum(1 for h in heads if h not in comp_of_head and h not in containing):,}")

block("rendering cost estimate")
# each item: <a href="entry://X">X</a> ~ 28 bytes + 20/page pager
for label, n in [("median list", sorted(len(v) for v in containing.values())[len(containing)//2]),
                 ("p95 list", sorted(len(v) for v in containing.values())[int(len(containing)*0.95)]),
                 ("max list", max(len(v) for v in containing.values()))]:
    print(f"   {label:<12} {n:>4} items -> ~{n*30/1024:.1f} KB html")
print(f"   total items across all component pages: {sum(len(v) for v in containing.values()):,}")
