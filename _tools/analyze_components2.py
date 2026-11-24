# -*- coding: utf-8 -*-
"""Compare component semantics: depth-1 (direct) vs full-depth."""
import json
import os
import sys
import collections
import re

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")
OPS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻")

recs = json.load(open(os.path.join(DATA, "records.json"), encoding="utf-8"))
chars = json.load(open(os.path.join(DATA, "chars.json"), encoding="utf-8"))
heads = sorted({r["main"] for r in recs})


def first_ids(value):
    """Return the first IDS expression (the head's own structure)."""
    toks = value.split()
    if len(toks) < 2:
        return ""
    return toks[1]


def direct_children(value):
    ids = first_ids(value)
    out = set()
    for ch in ids:
        if ch in OPS or not ch.isprintable():
            continue
        out.add(ch)
    return out


def all_nodes(value):
    out = set()
    for t in value.split()[1:]:
        if len(t) == 1 and t not in OPS and t.isprintable():
            out.add(t)
    return out


def reverse(fn):
    idx = collections.defaultdict(set)
    for h in heads:
        v = chars.get(h)
        if not v:
            continue
        for c in fn(v):
            idx[c].add(h)
    return idx


for name, fn in (("direct(depth1)", direct_children), ("all-depth", all_nodes)):
    idx = reverse(fn)
    sizes = sorted(len(v) for v in idx.values())
    print(f"\n=== {name} ===")
    print(f"components: {len(idx):,}   lists: n={len(sizes):,} median={sizes[len(sizes)//2]} "
          f"p90={sizes[int(len(sizes)*0.9)]} p95={sizes[int(len(sizes)*0.95)]} max={sizes[-1]}")
    print("bucket:", dict(collections.Counter(
        ("1" if n == 1 else "2-5" if n <= 5 else "6-20" if n <= 20 else "21-50" if n <= 50
         else "51-100" if n <= 100 else ">100") for n in sizes)))
    print("top:", [(c, len(v)) for c, v in sorted(idx.items(), key=lambda kv: -len(kv[1]))[:10]])
    for probe in ("一", "口", "山", "岡", "辶", "金", "木"):
        print(f"   {probe}: {len(idx.get(probe, ()))}")
    comp_only = [c for c in idx if c not in heads]
    print(f"component-only keys: {len(comp_only):,}")
    if name.startswith("direct"):
        dir_idx = idx
    else:
        all_idx = idx

print("\n=== sample direct lists ===")
for probe in ("岡", "刂", "山", "辶"):
    hs = sorted(dir_idx.get(probe, ()))
    print(f"   {probe} ({len(hs)}): {''.join(hs[:40])}")
    print(f"      all-depth adds {len(all_idx.get(probe, ()) - dir_idx.get(probe, set()))} more")

print("\n=== overlap ===")
same = sum(1 for c in dir_idx if dir_idx[c] == all_idx.get(c, set()))
print(f"components where depth1 list == all-depth list: {same:,} / {len(dir_idx):,}")
