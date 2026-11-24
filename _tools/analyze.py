# -*- coding: utf-8 -*-
"""Profile jinwen-glyph-search data files to judge MDX feasibility."""
import json
import os
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")


def load(name):
    p = os.path.join(DATA, name)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def show(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def describe(v, depth=0):
    if isinstance(v, dict):
        return f"dict[{len(v)}] keys={list(v)[:8]}"
    if isinstance(v, list):
        return f"list[{len(v)}] first={type(v[0]).__name__ if v else '-'}"
    if isinstance(v, str):
        return f"str({len(v)}) {v[:60]!r}"
    return f"{type(v).__name__} {v!r}"


# ---------------------------------------------------------------- records
show("records.json")
rec_doc = load("records.json")
print("top type:", type(rec_doc).__name__)
if isinstance(rec_doc, dict):
    print("top keys:", list(rec_doc)[:10])

records = rec_doc.get("records", rec_doc) if isinstance(rec_doc, dict) else rec_doc
if isinstance(records, dict):
    items = list(records.items())
    print(f"records: dict with {len(items):,} entries")
    sample_id, sample = items[0]
    print("sample id:", sample_id)
    print("sample keys:", list(sample))
    for k, v in sample.items():
        print(f"   {k:<12} {describe(v)}")
    recs = [dict(v, _id=k) for k, v in items]
else:
    print(f"records: list with {len(rec_doc):,} items")
    print("sample keys:", list(rec_doc[0]))
    for k, v in rec_doc[0].items():
        print(f"   {k:<12} {describe(v)}")
    recs = rec_doc

n = len(recs)
print(f"\nTOTAL RECORDS: {n:,}")

# field coverage
print("\n-- field coverage --")
keys = collections.Counter()
for r in recs:
    for k in r:
        keys[k] += 1
for k, c in keys.most_common():
    print(f"   {k:<12} {c:>7,}  ({c * 100 / n:5.1f}%)")

# value distributions
for field in ("book", "period", "group", "main", "sub"):
    vals = collections.Counter(str(r.get(field, "")) for r in recs)
    print(f"\n-- {field}: {len(vals):,} distinct --")
    for v, c in vals.most_common(12):
        print(f"   {v!r:<28} {c:>7,}")

# headword structure
mains = collections.Counter(str(r.get("main", "")) for r in recs)
subs = collections.Counter((str(r.get("main", "")), str(r.get("sub", ""))) for r in recs)
print(f"\ndistinct main heads: {len(mains):,}")
print(f"distinct main+sub:   {len(subs):,}")
print("top main heads:", mains.most_common(15))
per_head = collections.Counter(mains.values())
print("records per main head histogram (head_count: num_heads):",
      dict(sorted(per_head.items())))
print(f"max glyphs under one main head: {max(mains.values()):,}")

# image refs
imgs = [str(r.get("image", "")) for r in recs]
missing = [p for p in imgs if not p or not os.path.exists(os.path.join(SITE, p.replace("/", os.sep)))]
print(f"\nimage refs: {len(imgs):,}  empty: {sum(1 for p in imgs if not p):,}  missing on disk: {len(missing):,}")
print("sample image paths:", imgs[:3])

# text length profile
for field in ("title", "source"):
    lens = [len(str(r.get(field, ""))) for r in recs]
    print(f"{field}: max_len={max(lens)} avg={sum(lens) / len(lens):.1f} sample={recs[0].get(field)!r}")

# cid placeholders inside text
cid = sum(1 for r in recs if "(cid:" in json.dumps(r, ensure_ascii=False))
print(f"records containing '(cid:' anywhere: {cid:,}")

# ---------------------------------------------------------------- other files
show("meta.json")
meta = load("meta.json")
print("top type:", type(meta).__name__, list(meta)[:10] if isinstance(meta, dict) else len(meta))
if isinstance(meta, dict):
    for k, v in list(meta.items())[:10]:
        print(f"   {k:<16} {describe(v)}")
        if isinstance(v, list) and v and isinstance(v[0], dict):
            print("      first item:", json.dumps(v[0], ensure_ascii=False)[:300])

show("chars.json")
chars = load("chars.json")
print("top type:", type(chars).__name__)
if isinstance(chars, dict):
    ks = list(chars)[:5]
    print("sample keys:", ks)
    for k in ks:
        print(f"   {k!r} -> {json.dumps(chars[k], ensure_ascii=False)[:240]}")
    print("count:", len(chars))
else:
    print("count:", len(chars))
    print(json.dumps(chars[0], ensure_ascii=False)[:400])

show("annotations.json")
ann = load("annotations.json")
print("top keys:", list(ann) if isinstance(ann, dict) else type(ann).__name__)
if isinstance(ann, dict):
    for k, v in ann.items():
        print(f"   {k:<16} {describe(v)}")

show("inline_glyphs.json / cid_glyphs.json")
inl = load("inline_glyphs.json")
cidg = load("cid_glyphs.json")
print("inline_glyphs:", type(inl).__name__, len(inl))
print("sample:", json.dumps(list(inl.items())[:3] if isinstance(inl, dict) else inl[:3], ensure_ascii=False)[:400])
print("cid_glyphs:", json.dumps(cidg, ensure_ascii=False)[:400])

show("pua tsv")
for name in ("pua_chars.tsv", "pua_ids.tsv"):
    p = os.path.join(DATA, name)
    with open(p, encoding="utf-8") as f:
        lines = f.read().splitlines()
    print(f"{name}: {len(lines):,} lines")
    for ln in lines[:5]:
        print("   ", ln[:160])

show("asset totals")
for sub in ("glyphs", "inline-glyphs", "cid-glyphs", "fonts"):
    d = os.path.join(SITE, "assets", sub)
    cnt = size = 0
    ext = collections.Counter()
    for dp, _, fns in os.walk(d):
        for fn in fns:
            cnt += 1
            size += os.path.getsize(os.path.join(dp, fn))
            ext[os.path.splitext(fn)[1].lower()] += 1
    print(f"{sub:<14} files={cnt:>7,}  size={size / 1048576:8.1f} MB  {dict(ext)}")
