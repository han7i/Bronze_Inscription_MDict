# -*- coding: utf-8 -*-
"""Third pass: unencoded-glyph coverage, font mapping, mdict writer API, image conversion cost."""
import json
import os
import re
import sys
import collections
import inspect

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")


def block(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


with open(os.path.join(DATA, "records.json"), encoding="utf-8") as f:
    recs = json.load(f)
with open(os.path.join(DATA, "inline_glyphs.json"), encoding="utf-8") as f:
    inline = json.load(f)
with open(os.path.join(DATA, "meta.json"), encoding="utf-8") as f:
    meta = json.load(f)
with open(os.path.join(DATA, "chars.json"), encoding="utf-8") as f:
    chars = json.load(f)


def is_special(cp):
    return (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0x10FFFF) or cp > 0x323AF


block("special (unencodable) chars in displayed text")
per_plane = collections.Counter()
special = collections.Counter()
special_fields = collections.Counter()
for r in recs:
    for field in ("main", "sub", "title", "source"):
        for ch in str(r.get(field, "")):
            cp = ord(ch)
            if is_special(cp):
                special[ch] += 1
                per_plane[(cp >> 16, field)] += 1
                special_fields[field] += 1
print("distinct special chars:", len(special))
print("occurrences by field:", dict(special_fields))
print("by plane/field:", {f"plane{k[0]:02X}/{k[1]}": v for k, v in sorted(per_plane.items())})

covered = [c for c in special if f"U+{ord(c):X}" in inline]
print(f"covered by inline_glyphs.json: {len(covered)} / {len(special)}")
missing = [c for c in special if f"U+{ord(c):X}" not in inline]
print("uncovered sample:", [(c, f"U+{ord(c):04X}") for c in missing[:10]])

block("pua_chars.tsv coverage")
pua = {}
with open(os.path.join(DATA, "pua_chars.tsv"), encoding="utf-8-sig") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if parts and parts[0]:
            pua[parts[0]] = dict(zip(hdr, parts))
print("pua_chars tokens:", len(pua))
hit = sum(1 for c in special if c in pua)
print("special chars found in pua_chars:", hit)
print("sample rows:",
      [f"{k} -> {v.get('first_main')}/{v.get('first_title')}" for k, v in list(pua.items())[:3]])

block("fonts.css -> codepoint coverage")
css_path = os.path.join(SITE, "assets", "fonts", "fonts.css")
css = open(css_path, encoding="utf-8").read()
faces = re.findall(r"@font-face\s*\{(.*?)\}", css, re.S)
print("font-face blocks:", len(faces))
ranges = []
sample_face = None
for body in faces:
    fam = re.search(r"font-family:\s*'?([^;']+)", body)
    src = re.search(r"url\(['\"]?([^'\")]+)", body)
    ur = re.search(r"unicode-range:\s*([^;]+)", body)
    if ur:
        ranges.append((fam.group(1) if fam else "?", src.group(1) if src else "?", ur.group(1).strip()))
if ranges:
    sample_face = ranges[0]
    print("sample face:", sample_face)


def parse_ur(text):
    out = []
    for part in text.split(","):
        part = part.strip()
        m = re.match(r"U\+([0-9A-Fa-f]+)(?:-([0-9A-Fa-f]+))?$", part)
        if m:
            lo = int(m.group(1), 16)
            hi = int(m.group(2), 16) if m.group(2) else lo
            out.append((lo, hi))
    return out


def font_for(cp):
    for fam, src, ur in ranges:
        for lo, hi in parse_ur(ur):
            if lo <= cp <= hi:
                return fam, src
    return None


resolved = 0
unresolved = []
for c in missing:
    r = font_for(ord(c))
    if r:
        resolved += 1
    else:
        unresolved.append(c)
print(f"uncovered special chars resolvable via fonts.css: {resolved} / {len(missing)}")
print("still unresolved:", [(c, f"U+{ord(c):04X}") for c in unresolved[:12]])

# total coverage
tot_unres = len([c for c in special if font_for(ord(c)) is None and f"U+{ord(c):X}" not in inline])
print("TOTAL special chars with no image and no font:", tot_unres)

block("chars.json coverage of heads")
mains = {r["main"] for r in recs}
have = sum(1 for m in mains if m in chars)
print(f"heads with chars.json entry: {have} / {len(mains)}")
print("heads missing from chars.json sample:", [m for m in list(mains)[:200] if m not in chars][:8])

block("mdict writer API")
import mdict  # noqa: E402
print("mdict file:", mdict.__file__)
print("version:", getattr(mdict, "__version__", "?"))
try:
    from mdict.write import MDictWriter
    print("MDictWriter sig:", inspect.signature(MDictWriter.__init__))
    print("Writer methods:", [n for n in dir(MDictWriter) if not n.startswith("_")])
except Exception as exc:  # noqa: BLE001
    print("write import failed:", exc)
    print("dir(mdict):", [n for n in dir(mdict) if not n.startswith("_")])

block("webp -> png conversion cost (sample 400)")
from PIL import Image
import glob
files = glob.glob(os.path.join(SITE, "assets", "glyphs", "*", "*.webp"))[:400]
w = p = 0
for f in files:
    w += os.path.getsize(f)
    with Image.open(f) as im:
        im = im.convert("L")
        buf = os.path.join(ROOT, "_src", "_tmp.png")
        im.save(buf, "PNG", optimize=True)
    p += os.path.getsize(buf)
print(f"webp {w/1024:.0f} KB -> png(gray,optimize) {p/1024:.0f} KB  ratio {p/w:.2f}")
print("extrapolated png total: %.0f MB" % (p / 1024 / 1024 / len(files) * 35816))
