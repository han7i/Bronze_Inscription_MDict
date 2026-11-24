# -*- coding: utf-8 -*-
"""Inspect the component sections of a few entries."""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_tools", "vendor"))
from mdict_utils import reader  # noqa: E402

mdx = os.path.join(ROOT, "金文字形全編.mdx")
for probe in ("岡", "辶", "剛", "一", "山", "寳"):
    body = reader.query(mdx, probe)
    if body is None:
        print(f"{probe}: <not a key>")
        continue
    body = body.replace("\x00", "")
    sec = body[body.find('class="jw-cs"'):] if 'class="jw-cs"' in body else ""
    pages = body.count("<label for=")
    items = len(re.findall(r'href="entry://', sec))
    print(f"\n=== {probe} ===")
    print(f"  正文卡片: {body.count('class=\"jw-c\"')}   构件区: {'有' if sec else '无'}   "
          f"分页标签: {pages}   列表链接: {items}")
    if sec:
        head = sec[:sec.find("</div>") + 6]
        print("  " + head.replace("<div class=\"jw-cs\">", "").replace("</div>", "")[:160])
        first = re.findall(r'<a href="entry://([^"]+)">([^<]+)</a>', sec)
        print("  前 24 项: " + " ".join(x[1] for x in first[:24]))
        if pages:
            print("  第 2 页首项: " + (first[20][1] if len(first) > 20 else "-"))
