# -*- coding: utf-8 -*-
"""Compare PNG encodings for the 112x112 line-art glyphs, and check colour depth."""
import glob
import io
import json
import os
import sys

from PIL import Image, ImageChops

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
files = glob.glob(os.path.join(SITE, "assets", "glyphs", "*", "*.webp"))[::37][:300]
print("sample:", len(files))


def size_of(im, **kw):
    buf = io.BytesIO()
    im.save(buf, "PNG", **kw)
    return buf.tell()


tot = {"webp": 0, "L": 0, "L1": 0, "P8": 0, "P16": 0, "Lfast": 0}
gray = 0
alphas = 0
for p in files:
    tot["webp"] += os.path.getsize(p)
    with Image.open(p) as im0:
        im = im0.convert("RGB")
        r, g, b = im.split()
        if ImageChops.difference(r, g).getbbox() is None and ImageChops.difference(g, b).getbbox() is None:
            gray += 1
        if im0.mode in ("RGBA", "LA", "P"):
            alphas += 1
        L = im.convert("L")
        tot["L"] += size_of(L, optimize=True)
        tot["Lfast"] += size_of(L)
        tot["L1"] += size_of(L.convert("1"), optimize=True)
        tot["P8"] += size_of(L.convert("P", palette=Image.ADAPTIVE, colors=8), optimize=True)
        tot["P16"] += size_of(L.convert("P", palette=Image.ADAPTIVE, colors=16), optimize=True)

n = len(files)
print(f"all-gray images: {gray}/{n};  with alpha/palette mode: {alphas}")
for k, v in tot.items():
    print(f"{k:>6}: avg {v/n/1024:5.2f} KB  -> 35,816 imgs = {v/n*35816/1048576:6.1f} MB")
