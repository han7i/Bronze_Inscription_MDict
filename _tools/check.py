# -*- coding: utf-8 -*-
"""Validate the packed dictionary: images, entry:// links, aliases, sizes, HTML balance."""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_tools", "vendor"))

from mdict_utils import reader  # noqa: E402

base = os.path.join(ROOT, "金文字形全編")
mdx, mdd = base + ".mdx", base + ".mdd"

img_re = re.compile(r'<img[^>]+src="([^"]+)"')
link_re = re.compile(r'href="entry://([^"]+)"')

keys = list(reader.get_keys(mdx))
keys_set = set(keys)
res = set(reader.get_keys(mdd))
print(f"entries: {len(keys):,}   resources: {len(res):,}")


def special(s):
    return [c for c in s if 0xE000 <= ord(c) <= 0xF8FF or ord(c) > 0x323AF]


bad_keys = [k for k in keys if special(k)]
print(f"keys with unencodable codepoints: {len(bad_keys):,}")

missing, link_bad = {}, {}
sizes = []
img_total = link_total = 0
comp_sections = comp_only = pager_max = 0
aliases = alias_bad = div_bad = css_bad = 0
for k in keys:
    body = reader.query(mdx, k) or ""
    sizes.append(len(body))
    if body.startswith("@@@LINK="):
        aliases += 1
        tgt = body.split("=", 1)[1].replace("\x00", "").strip()
        if tgt not in keys_set:
            alias_bad += 1
        continue
    # CSS must be wrapped in exactly one <style>; a rule left after it renders as text
    if body.count("<style>") != 1 or body.count("</style>") != 1 or not body.startswith("<style>"):
        css_bad += 1
    else:
        tail = body[body.rindex("</style>") + len("</style>"):]
        if re.search(r"\.[A-Za-z][\w-]*\s*\{", tail):
            css_bad += 1
    for s in img_re.findall(body):
        img_total += 1
        key = "\\" + s.replace("/", "\\")
        if key not in res:
            missing[s] = missing.get(s, 0) + 1
    for t in link_re.findall(body):
        link_total += 1
        if t not in keys_set:
            link_bad[t] = link_bad.get(t, 0) + 1
    if 'class="jw-cs"' in body:
        comp_sections += 1
        if "無字頭正文" in body:
            comp_only += 1
        pager_max = max(pager_max, body.count("<label for="))
    if body.count("<div") != body.count("</div>"):
        div_bad += 1

print(f"img tags: {img_total:,}   missing resources: {len(missing):,}  e.g. {list(missing)[:3]}")
print(f"entry:// links: {link_total:,}   unresolved: {len(link_bad):,}  e.g. {list(link_bad)[:3]}")
print(f"component sections: {comp_sections:,} (component-only entries: {comp_only:,})")
print(f"max pager labels in one entry: {pager_max}")
print(f"alias entries: {aliases:,}  broken targets: {alias_bad}")
print(f"div imbalance entries: {div_bad}")
print(f"entries with leaked/malformed CSS: {css_bad}")
sizes.sort()
print(f"entry size: median {sizes[len(sizes)//2]/1024:.1f} KB  p95 "
      f"{sizes[int(len(sizes)*0.95)]/1024:.1f} KB  max {sizes[-1]/1024:.1f} KB")
print(f"mdx {os.path.getsize(mdx)/1048576:.2f} MB   mdd {os.path.getsize(mdd)/1048576:.1f} MB")
