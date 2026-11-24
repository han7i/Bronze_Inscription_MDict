# -*- coding: utf-8 -*-
"""Pack the staged text + images into MDX/MDD and verify by reading them back."""
import argparse
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_tools", "vendor"))

from mdict_utils.writer import MDictWriter, pack_mdx_txt, pack_mdd_file  # noqa: E402


def pack_mdx(sources, out, title, desc):
    items = []
    for s in sources:
        items.extend(pack_mdx_txt(s, encoding="utf-8"))
    print(f"[mdx ] {len(items):,} entries")
    w = MDictWriter(items, title=title, description=desc,
                    key_size=131072, record_size=262144, encoding="utf-8")
    t0 = time.time()
    with open(out, "wb") as f:
        w.write(f)
    print(f"[mdx ] {out} {os.path.getsize(out)/1048576:.1f} MB in {time.time()-t0:.1f}s")


def pack_mdd(img_dir, out, title, desc):
    items = pack_mdd_file(img_dir)
    print(f"[mdd ] {len(items):,} resources")
    w = MDictWriter(items, title=title, description=desc,
                    key_size=131072, record_size=262144, encoding="utf-8", is_mdd=True)
    t0 = time.time()
    with open(out, "wb") as f:
        w.write(f)
    print(f"[mdd ] {out} {os.path.getsize(out)/1048576:.1f} MB in {time.time()-t0:.1f}s")


def verify(base, sample=None):
    from mdict_utils import reader
    mdx = base + ".mdx"
    print("\n[chk ] meta:", reader.meta(mdx))
    keys = list(reader.get_keys(mdx))
    print(f"[chk ] keys: {len(keys):,}  first: {keys[:3]}  last: {keys[-3:]}")
    probe = sample if sample in keys else keys[0]
    rec = reader.query(mdx, probe)
    print(f"[chk ] query {probe!r}: {len(rec or '')} chars")
    if rec:
        print("       head:", rec[:220].replace("\n", " "))
    print(f"[chk ] images in mdd: {len(list(reader.get_keys(base + '.mdd'))) if os.path.exists(base + '.mdd') else 0:,}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", action="append", required=True)
    ap.add_argument("--img", required=True)
    ap.add_argument("--out", required=True, help="output basename without extension")
    ap.add_argument("--title", default="金文字形全編")
    ap.add_argument("--desc", default="")
    ap.add_argument("--no-verify", action="store_true")
    a = ap.parse_args()
    pack_mdx(a.src, a.out + ".mdx", a.title, a.desc)
    if os.path.isdir(a.img) and os.listdir(a.img):
        pack_mdd(a.img, a.out + ".mdd", a.title, a.desc)
    if not a.no_verify:
        verify(a.out, "寶")
