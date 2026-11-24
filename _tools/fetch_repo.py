# -*- coding: utf-8 -*-
"""Download the jinwen-glyph-search repo archive and unpack it locally.

Only used to inspect file structure / data schema, and later as the source
for an MDX prototype. Writes everything under <workspace>/_src.
"""
import os
import ssl
import sys
import time
import zipfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_src")
ARCHIVE = os.path.join(SRC, "repo.zip")
EXTRACT = os.path.join(SRC, "repo")

URLS = [
    "https://codeload.github.com/fangquinlan/jinwen-glyph-search/zip/refs/heads/main",
    "https://github.com/fangquinlan/jinwen-glyph-search/archive/refs/heads/main.zip",
]


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:,.1f} {unit}"
        n /= 1024.0


def make_opener():
    """Build a urllib opener, tolerating this machine's TLS interception."""
    # 1) OS trust store via truststore (handles corporate/AV MITM roots)
    try:
        import truststore  # type: ignore
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        print("[tls ] truststore (Windows cert store)")
        return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    except Exception as exc:  # noqa: BLE001
        print(f"[tls ] truststore unavailable: {exc}")
    # 2) plain default, then 3) unverified as last resort
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request("https://codeload.github.com/", headers={"User-Agent": "probe"})
        urllib.request.urlopen(req, timeout=30, context=ctx).close()
        print("[tls ] system default (verified)")
        return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    except Exception as exc:  # noqa: BLE001
        print(f"[tls ] verified default failed: {exc}")
    ctx = ssl._create_unverified_context()  # noqa: SLF001
    print("[tls ] WARNING falling back to unverified TLS (read-only public data)")
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))


def download():
    opener = make_opener()
    os.makedirs(SRC, exist_ok=True)
    if os.path.exists(ARCHIVE) and os.path.getsize(ARCHIVE) > 1_000_000:
        print(f"[skip] archive already present: {human(os.path.getsize(ARCHIVE))}")
        return True
    last = None
    for url in URLS:
        try:
            print(f"[get ] {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (mdx-feasibility-check)"})
            t0 = time.time()
            with opener.open(req, timeout=120) as r, open(ARCHIVE, "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                got = 0
                last_pct = -1
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    got += len(chunk)
                    if total:
                        pct = got * 100 // total
                        if pct // 10 != last_pct // 10:
                            print(f"       {pct:3d}%  {human(got)} / {human(total)}")
                            last_pct = pct
            print(f"[ok  ] {human(os.path.getsize(ARCHIVE))} in {time.time() - t0:.1f}s")
            return True
        except Exception as exc:  # noqa: BLE001
            last = exc
            print(f"[fail] {url}: {exc}")
            if os.path.exists(ARCHIVE):
                os.remove(ARCHIVE)
    print(f"[dead] {last}")
    return False


def extract():
    if os.path.isdir(EXTRACT) and os.listdir(EXTRACT):
        print(f"[skip] already extracted: {EXTRACT}")
        return True
    print("[unzip] ...")
    os.makedirs(EXTRACT, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE) as zf:
        names = zf.namelist()
        top = names[0].split("/")[0] + "/"
        zf.extractall(EXTRACT)
    inner = os.path.join(EXTRACT, top)
    print(f"[ok  ] {len(names):,} entries -> {inner}")
    return True


def inventory():
    print("\n=== top level of site/ ===")
    site = os.path.join(EXTRACT, "jinwen-glyph-search-main", "site")
    if not os.path.isdir(site):
        for cand in os.listdir(EXTRACT):
            p = os.path.join(EXTRACT, cand, "site")
            if os.path.isdir(p):
                site = p
                break
    print(site)
    for dirpath, dirnames, filenames in os.walk(site):
        rel = os.path.relpath(dirpath, site)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        size = sum(os.path.getsize(os.path.join(dirpath, f)) for f in filenames)
        print(f"{rel:<24} files={len(filenames):>6}  size={human(size):>12}")
        if depth >= 0 and rel != "." and len(filenames) > 40:
            dirnames[:] = []
    print("\n=== root files ===")
    root = os.path.dirname(site)
    for f in sorted(os.listdir(root)):
        p = os.path.join(root, f)
        if os.path.isfile(p):
            print(f"{f:<24} {human(os.path.getsize(p))}")


if __name__ == "__main__":
    if not download():
        sys.exit(1)
    extract()
    inventory()
