# -*- coding: utf-8 -*-
"""Fourth pass: authoritative font cmap coverage + vendor a MDX writer."""
import json
import os
import subprocess
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")
VENDOR = os.path.join(ROOT, "_tools", "vendor")


def block(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


with open(os.path.join(DATA, "records.json"), encoding="utf-8") as f:
    recs = json.load(f)
with open(os.path.join(DATA, "inline_glyphs.json"), encoding="utf-8") as f:
    inline = json.load(f)
with open(os.path.join(DATA, "meta.json"), encoding="utf-8") as f:
    meta = json.load(f)


def is_special(cp):
    return (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0x10FFFF) or cp > 0x323AF


special = collections.Counter()
for r in recs:
    for field in ("main", "sub", "title", "source"):
        for ch in str(r.get(field, "")):
            if is_special(ord(ch)):
                special[ch] += 1

block("font cmap coverage for the %d special chars" % len(special))
try:
    from fontTools.ttLib import TTFont
    have_ft = True
except Exception as exc:  # noqa: BLE001
    have_ft = False
    print("fontTools missing:", exc)

if have_ft:
    fonts = meta["fonts"]
    print("fonts in meta.json:", len(fonts))
    coverage = collections.defaultdict(set)  # cp -> {family}
    for f in fonts:
        p = os.path.join(SITE, f["file"].replace("/", os.sep))
        if not os.path.exists(p):
            print("  missing font file:", p)
            continue
        try:
            tt = TTFont(p, lazy=True)
            cmap = set()
            for table in tt["cmap"].tables:
                cmap.update(table.cmap.keys())
            for ch in special:
                if ord(ch) in cmap:
                    coverage[ord(ch)].add(f["family"])
            tt.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  cannot read {f['family']}: {exc}")
    no_font = [ch for ch in special if ord(ch) not in coverage]
    print(f"special chars covered by some font cmap: {len(special) - len(no_font)} / {len(special)}")
    print("with no font at all:", [(c, f"U+{ord(c):04X}") for c in no_font][:10])
    multi = sum(1 for v in coverage.values() if len(v) > 1)
    print("chars present in >1 font:", multi)

block("install mdict-utils into vendor dir")
os.makedirs(VENDOR, exist_ok=True)
cmd = [sys.executable, "-m", "pip", "install", "--no-input", "--disable-pip-version-check",
       "--target", VENDOR, "mdict-utils"]
print(" ".join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True)
print("exit:", r.returncode)
print((r.stdout or "")[-3000:])
print((r.stderr or "")[-1500:])

sys.path.insert(0, VENDOR)
block("mdict writer API")
try:
    import mdict
    print("mdict:", mdict.__file__)
    try:
        from mdict.write import MDictWriter
        import inspect
        print("MDictWriter.__init__:", inspect.signature(MDictWriter.__init__))
        print("MDictWriter.save:", inspect.signature(MDictWriter.save))
        print("public attrs:", [n for n in dir(MDictWriter) if not n.startswith("_")])
    except Exception as exc:  # noqa: BLE001
        print("writer import failed:", exc)
        print("dir(mdict):", [n for n in dir(mdict) if not n.startswith("_")])
except Exception as exc:  # noqa: BLE001
    print("import failed:", exc)
