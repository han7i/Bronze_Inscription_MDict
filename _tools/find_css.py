# -*- coding: utf-8 -*-
"""List entries whose CSS block looks malformed."""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_tools", "vendor"))
from mdict_utils import reader  # noqa: E402

mdx = os.path.join(ROOT, "金文字形全編.mdx")
keys = list(reader.get_keys(mdx))
for k in keys:
    body = reader.query(mdx, k) or ""
    if body.startswith("@@@LINK="):
        continue
    bad = (body.count("<style>") != 1 or body.count("</style>") != 1
           or not body.startswith("<style>"))
    tail = ""
    if not bad:
        tail = body[body.rindex("</style>") + len("</style>"):]
        bad = "{" in tail or "}" in tail
    if bad:
        print(f"--- {k!r}  style_tags={body.count('<style>')}/{body.count('</style>')} "
              f"starts_ok={body.startswith('<style>')} len={len(body)}")
        if tail:
            i = min(tail.find("{"), tail.find("}")) if ("{" in tail or "}" in tail) else 0
            print("    tail around brace:", repr(tail[max(0, i - 60):i + 60]))
