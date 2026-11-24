# -*- coding: utf-8 -*-
"""Pick an RGB-faithful but small PNG encoding for the glyph thumbnails."""
import glob
import io
import os
import sys

from PIL import Image, ImageChops, ImageStat

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
files = glob.glob(os.path.join(SITE, "assets", "glyphs", "*", "*.webp"))[::37][:200]
print("sample:", len(files))


def enc(im, **kw):
    buf = io.BytesIO()
    im.save(buf, "PNG", **kw)
    return buf.tell(), buf.getvalue()


def fidelity(a, b):
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    st = ImageStat.Stat(d)
    return sum(st.mean) / 3, max(st.extrema[i][1] for i in range(3))


variants = {
    "RGB": lambda im: (im, {"optimize": True}),
    "P16": lambda im: (im.convert("P", palette=Image.ADAPTIVE, colors=16), {"optimize": True}),
    "P32": lambda im: (im.convert("P", palette=Image.ADAPTIVE, colors=32), {"optimize": True}),
    "P64": lambda im: (im.convert("P", palette=Image.ADAPTIVE, colors=64), {"optimize": True}),
    "P128": lambda im: (im.convert("P", palette=Image.ADAPTIVE, colors=128), {"optimize": True}),
}
tot = {k: 0 for k in variants}
diff_mean = {k: 0.0 for k in variants}
diff_max = {k: 0 for k in variants}
sat = []
for p in files:
    with Image.open(p) as im0:
        im = im0.convert("RGB")
        st = ImageStat.Stat(im.convert("HSV"))
        sat.append(st.mean[1])
        for k, fn in variants.items():
            out, kw = fn(im)
            n, raw = enc(out, **kw)
            tot[k] += n
            if k != "RGB":
                mb = Image.open(io.BytesIO(raw))
                m, mx = fidelity(im, mb)
                diff_mean[k] += m
                diff_max[k] = max(diff_max[k], mx)

n = len(files)
print(f"mean saturation (HSV S, 0-255): {sum(sat)/n:.1f}")
for k in variants:
    print(f"{k:>5}: avg {tot[k]/n/1024:5.2f} KB -> 35,816 = {tot[k]/n*35816/1048576:6.1f} MB"
          + ("" if k == "RGB" else f"   mean_diff={diff_mean[k]/n:.2f} max_diff={diff_max[k]}"))

# also: how much does RGB->L hurt?
gl = 0.0
for p in files:
    with Image.open(p) as im0:
        im = im0.convert("RGB")
        g = im.convert("L").convert("RGB")
        m, _ = fidelity(im, g)
        gl += m
print(f"RGB->L mean colour error: {gl/n:.2f}")
