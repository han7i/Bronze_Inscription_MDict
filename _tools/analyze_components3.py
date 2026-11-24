# -*- coding: utf-8 -*-
"""Compare component semantics with annotation-aware IDS parsing."""
import json
import os
import re
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")
OPS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻")

recs = json.load(open(os.path.join(DATA, "records.json"), encoding="utf-8"))
chars = json.load(open(os.path.join(DATA, "chars.json"), encoding="utf-8"))
heads = sorted({r["main"] for r in recs})

PAREN = re.compile(r"\([^()]*\)")
BRACE = re.compile(r"\{[^}]*\}")
TAG = re.compile(r"#[A-Za-z]+")


def clean(ids):
    s = ids
    for _ in range(6):
        prev = s
        s = PAREN.sub("", s)
        s = BRACE.sub("", s)
        s = TAG.sub("", s)
        if s == prev:
            break
    return s


def operands(expr):
    return {ch for ch in clean(expr) if ch not in OPS and not ch.isascii() and ch.isprintable()}


def direct(value):
    toks = value.split()
    return operands(toks[1]) if len(toks) > 1 else set()


def alldepth(value):
    toks = value.split()
    out = set()
    for t in toks[1:]:
        out |= {ch for ch in clean(t) if ch not in OPS and not ch.isascii() and ch.isprintable()}
    return out


for name, fn in (("direct(depth1)", direct), ("all-depth", alldepth)):
    idx = collections.defaultdict(set)
    for h in heads:
        v = chars.get(h)
        if not v:
            continue
        for c in fn(v):
            if c != h:
                idx[c].add(h)
    sizes = sorted(len(v) for v in idx.values())
    print(f"\n=== {name} ===")
    print(f"components: {len(idx):,}  median={sizes[len(sizes)//2]} p90={sizes[int(len(sizes)*0.9)]} "
          f"p95={sizes[int(len(sizes)*0.95)]} max={sizes[-1]}")
    print("bucket:", dict(collections.Counter(
        ("1" if n == 1 else "2-5" if n <= 5 else "6-20" if n <= 20 else "21-50" if n <= 50
         else "51-100" if n <= 100 else ">100") for n in sizes)))
    print("top:", [(c, len(v)) for c, v in sorted(idx.items(), key=lambda kv: -len(kv[1]))[:12]])
    for p in ("一", "口", "山", "岡", "辶", "金", "木", "人"):
        print(f"   {p}: {len(idx.get(p, ()))}")
    print(f"component-only keys: {len([c for c in idx if c not in heads]):,}")
    if name.startswith("direct"):
        DIR = idx
    else:
        ALL = idx

print("\n=== sanity ===")
for p in ("寶", "剛", "岡", "鑄"):
    v = chars.get(p)
    if v:
        print(f"   {p}: ids={v.split()[1]!r} -> direct={''.join(sorted(direct(v)))}")
for p in ("岡", "刂", "山", "辶", "一"):
    print(f"   {p}: direct {len(DIR.get(p, ()))} / all {len(ALL.get(p, ()))}")
    print(f"      {' '.join(sorted(DIR.get(p, ()))[:30])}")
