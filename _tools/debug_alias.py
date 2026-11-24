# -*- coding: utf-8 -*-
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_tools", "vendor"))
from mdict_utils import reader  # noqa: E402

base = os.path.join(ROOT, "金文字形全編")
mdx = base + ".mdx"
keys = list(reader.get_keys(mdx))

# find entries whose body starts with @@@LINK=
shown = 0
for k in keys:
    body = reader.query(mdx, k)
    if body and "@@@LINK=" in body:
        print(f"key={k!r} body={body!r}")
        tgt = body.strip().split("@@@LINK=")[-1]
        print(f"   target={tgt!r}  in keys={tgt in keys}")
        shown += 1
        if shown >= 5:
            break

print("\nalias.txt first lines:")
p = os.path.join(ROOT, "_build", "alias.txt")
with open(p, encoding="utf-8") as f:
    for _ in range(9):
        print("   ", repr(f.readline()))
