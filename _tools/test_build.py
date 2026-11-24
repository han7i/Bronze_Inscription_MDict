# -*- coding: utf-8 -*-
"""Unit checks for the component parser, style block and pager CSS (no rebuild)."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_tools"))
import build_mdx as B  # noqa: E402

chars = json.load(open(os.path.join(B.DATA, "chars.json"), encoding="utf-8"))

ok = True


def check(label, cond, detail=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label + (f"   {detail}" if detail else ""))
    ok = ok and cond


print("--- direct (一级构件) ---")
for ch, want in (("剛", set("岡刂")), ("岡", set("𦉰山")), ("鑄", set("金壽")), ("寶", set("𡩧貝"))):
    got = B.direct_components(chars[ch], ch)
    check(f"{ch} -> {''.join(sorted(got))}", got == want, f"want {''.join(sorted(want))}")

no_junk = all(not (c.isascii() or c in B.OPS) for c in B.direct_components(chars["寶"], "寶"))
check("annotation tokens (.,J) etc. excluded", no_junk)
check("no depth switch left in module", not hasattr(B, "all_components"))

print("--- style block ---")
sb = B.style_block(B.CSS_BODY, B.COMP_CSS + B.pager_css(3))
check("single <style> pair", sb.count("<style>") == 1 and sb.count("</style>") == 1)
check("style ends with </style>", sb.endswith("</style>"))
outside = sb[sb.rindex("</style>") + len("</style>"):]
check("nothing after </style>", outside == "", repr(outside[:40]))
check("component css inside style", sb.index(".jw-cs{") < sb.index("</style>"))
check("pager rule inside style", sb.index("nth-of-type(1)") < sb.index("</style>"))
plain = B.style_block(B.CSS_BODY)
check("plain entry has no component css", ".jw-cs{" not in plain)

print("--- pager css ---")
css = B.pager_css(3)
check("rule for page 1", ".jw-pg>input:nth-of-type(1):checked~.jw-pages>.jw-page.p1{display:block}" in css)
check("hides page 1 on page 2", "nth-of-type(2):checked~.jw-pages>.jw-page.p1{display:none}" in css)
check("shows page 3", "nth-of-type(3):checked~.jw-pages>.jw-page:nth-child(3){display:block}" in css)
check("active label rule", "~.jw-nav>label:nth-child(2){background" in css)

print("--- render ---")
items = [chr(c) for c in range(0x4E00, 0x4E00 + 25)]
html = B.render_component("一", items)
check("25 items -> 2 pages", html.count("<label for=") == 2, f"labels={html.count('<label for=')}")
check("all items present", html.count('href="entry://') == 25)
check("first radio checked", 'id="jwpg4E00-1" checked' in html)
small = B.render_component("岡", list("剛岡犅𬳭"))
check("4 items -> no pager", "<label for=" not in small and small.count('href="entry://') == 4)

print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
