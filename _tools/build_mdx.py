# -*- coding: utf-8 -*-
"""Build a GoldenDict MDX/MDD of 金文字形 from the jinwen-glyph-search repo data.

Usage:
    python build_mdx.py --out ../_build --limit 30     # smoke test
    python build_mdx.py --out ../_build                # full build
"""
import argparse
import json
import os
import re
import shutil
import sys
import time

from PIL import Image, ImageFont, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "_src", "repo", "jinwen-glyph-search-main", "site")
DATA = os.path.join(SITE, "data")

CSS_BODY = (
    ".jw{font-family:'Microsoft YaHei','SimSun',sans-serif;font-size:13px;color:#222;line-height:1.5}"
    ".jw-h{border-bottom:2px solid #8b5a2b;padding-bottom:6px;margin-bottom:10px}"
    ".jw-ch{font-size:30px;font-weight:bold;color:#5c3a1a;vertical-align:middle}"
    ".jw-ids{font-size:14px;color:#666;margin-left:10px;vertical-align:middle}"
    ".jw-n{font-size:12px;color:#8b5a2b;margin-left:10px;vertical-align:middle}"
    ".jw-c{display:inline-block;width:130px;vertical-align:top;margin:0 8px 12px 0;text-align:center}"
    ".jw-c img.g{width:112px;height:112px;border:1px solid #ddd;background:#fff}"
    ".jw-t{font-size:12px;line-height:1.35;margin-top:3px;word-break:break-all}"
    ".jw-m{font-size:11px;color:#8b5a2b}"
    ".jw-s{font-size:11px;color:#777;word-break:break-all}"
    ".jw-p{font-size:10px;color:#999}"
    ".ig{height:15px;vertical-align:-3px}"
    ".jw-note{font-size:11px;color:#555;background:#faf6ef;border-left:3px solid #c8a97e;padding:3px 6px;margin:3px 0;text-align:left}"
    ".jw-back{font-size:11px;margin-left:10px}"
    ".jw a{color:#8b5a2b;text-decoration:none}"
)


def style_block(*bodies):
    """Wrap CSS bodies in one <style> element.

    Every CSS fragment must go *inside* the same <style> tag; concatenating a
    fragment after the closing tag makes the browser render it as body text.
    """
    return "<style>" + "".join(bodies) + "</style>"

INDEX_KEY = "未編碼字頭一覽"

# ---- 构件（component）检索 ----
# 采用「一级构件」：只取字头 IDS 的第一层操作数（剛 ⿰岡刂 -> 岡、刂）。
# IDS 字串里还挂着异体注记，如 貝(.,J) / #(H)(.) / {一}#(T)(t)，解析前必须剔除，
# 否则 ( ) . , J 之类会被当成构件。
OPS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻")
PAREN = re.compile(r"\([^()]*\)")
BRACE = re.compile(r"\{[^}]*\}")
TAG = re.compile(r"#[A-Za-z]+")
PAGE_SIZE = 20

COMP_CSS = (
    ".jw-cs{border-top:1px dashed #c8a97e;margin-top:16px;padding-top:8px;clear:both}"
    ".jw-cs .hd{font-size:12px;color:#8b5a2b;margin-bottom:4px}"
    ".jw-cl{line-height:1.95}"
    ".jw-cl a{font-size:20px;color:#222;text-decoration:none;display:inline-block;"
    "min-width:24px;text-align:center;padding:0 2px;border-radius:3px}"
    ".jw-cl a:hover{background:#f3e8d8;color:#000}"
    ".jw-pg>input{display:none}"
    ".jw-pg .jw-page{display:none}"
    ".jw-pg .jw-page.p1{display:block}"
    ".jw-nav{margin-top:2px;font-size:11px;line-height:1.9}"
    ".jw-nav label{cursor:pointer;display:inline-block;min-width:18px;text-align:center;"
    "padding:0 5px;margin-right:4px;border:1px solid #ddd;border-radius:3px;color:#777}"
    ".jw-nav label:hover{border-color:#c8a97e;color:#5c3a1a}"
)


def pager_css(max_pages):
    """Pure-CSS pager: hidden radios + labels + :checked sibling selectors.

    Qt4 WebKit has no usable JS for articles, so pagination is done with
    <input type=radio> + <label for>; each page is a sibling shown by a
    generated :checked rule. Falls back to showing page 1 only if the
    selectors are unsupported.
    """
    out = []
    for k in range(1, max_pages + 1):
        sel = f".jw-pg>input:nth-of-type({k}):checked"
        if k == 1:
            out.append(sel + "~.jw-pages>.jw-page.p1{display:block}")
        else:
            out.append(sel + "~.jw-pages>.jw-page.p1{display:none}")
            out.append(sel + f"~.jw-pages>.jw-page:nth-child({k}){{display:block}}")
        out.append(sel + f"~.jw-nav>label:nth-child({k})"
                   "{background:#8b5a2b;color:#fff;border-color:#8b5a2b}")
    return "".join(out)


def clean_ids(s):
    for _ in range(6):
        prev = s
        s = PAREN.sub("", s)
        s = BRACE.sub("", s)
        s = TAG.sub("", s)
        if s == prev:
            break
    return s


def direct_components(value, self_char):
    """First-level operands of a chars.json IDS value."""
    toks = value.split()
    if len(toks) < 2:
        return set()
    expr = clean_ids(toks[1])
    return {ch for ch in expr
            if ch not in OPS and not ch.isascii() and ch.isprintable() and ch != self_char}


def render_component(key, items):
    """构件区：key 为构件，items 为含该构件的词头（含自身）。"""
    uid = "jwpg%X" % ord(key)
    n = len(items)
    pages = [items[i:i + PAGE_SIZE] for i in range(0, n, PAGE_SIZE)]
    out = ['<div class="jw-cs">',
           f'<div class="hd">構件「{esc(key)}」· 含此構件的詞頭 {n} 個，點字可跳轉</div>']
    if len(pages) <= 1:
        out.append('<div class="jw-cl">' + "".join(
            f'<a href="entry://{x}">{x}</a>' for x in items) + '</div>')
    else:
        out.append('<div class="jw-pg">')
        for i in range(len(pages)):
            checked = " checked" if i == 0 else ""
            out.append(f'<input type="radio" name="{uid}" id="{uid}-{i+1}"{checked}>')
        out.append('<div class="jw-pages">')
        for i, pg in enumerate(pages):
            cls = "jw-page p1" if i == 0 else "jw-page"
            out.append(f'<div class="{cls}"><div class="jw-cl">' + "".join(
                f'<a href="entry://{x}">{x}</a>' for x in pg) + '</div></div>')
        out.append('</div><div class="jw-nav">')
        for i in range(len(pages)):
            out.append(f'<label for="{uid}-{i+1}">{i+1}</label>')
        out.append('</div></div>')
    out.append('</div>')
    return "".join(out)


def has_special(s):
    for ch in s:
        cp = ord(ch)
        if (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0x10FFFF) or cp > 0x323AF:
            return True
    return False

CHUNK = 300


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class GlyphText:
    """Turns text containing unencodable codepoints into HTML with inline PNGs."""

    def __init__(self, inline, fonts_meta):
        self.inline = inline
        self.font_by_cp = {}
        for f in fonts_meta:
            fam, path = f["family"], os.path.join(SITE, f["file"].replace("/", os.sep))
            for cp in f.get("_cmap", []):
                self.font_by_cp.setdefault(cp, (fam, path))
        self.rendered = {}

    @staticmethod
    def is_special(cp):
        return (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0x10FFFF) or cp > 0x323AF

    def html(self, text, staging):
        out = []
        for ch in str(text or ""):
            cp = ord(ch)
            if not self.is_special(cp):
                out.append(esc(ch))
                continue
            name = f"ig/{cp:X}.png"
            dst = os.path.join(staging, "ig", f"{cp:X}.png")
            if os.path.exists(dst):
                out.append(f'<img class="ig" src="{name}" alt="{cp:X}">')
                continue
            key = f"U+{cp:X}"
            src = self.inline.get(key)
            if src:
                shutil.copyfile(os.path.join(SITE, src.replace("/", os.sep)), dst)
                out.append(f'<img class="ig" src="{name}" alt="{cp:X}">')
                continue
            if self.render_from_font(cp, dst):
                out.append(f'<img class="ig" src="{name}" alt="{cp:X}">')
                continue
            out.append(esc(ch))
        return "".join(out)

    def render_from_font(self, cp, dst):
        hit = self.font_by_cp.get(cp)
        if not hit:
            return False
        _, path = hit
        try:
            font = ImageFont.truetype(path, 48)
            img = Image.new("L", (64, 64), 255)
            draw = ImageDraw.Draw(img)
            draw.text((8, 4), chr(cp), font=font, fill=0)
            bbox = img.point(lambda v: 255 if v < 255 else 0).getbbox()
            if bbox:
                img = img.crop(bbox)
            img.save(dst, "PNG", optimize=True)
            return True
        except Exception:  # noqa: BLE001
            return False


def build(out_dir, limit=None, convert_workers=1):
    t0 = time.time()
    records = load_json("records.json")
    meta = load_json("meta.json")
    inline = load_json("inline_glyphs.json")
    chars = load_json("chars.json")
    annotations = load_json("annotations.json")

    # cmap only for chars we may need to render ourselves
    needed = set()
    for r in records:
        for field in ("main", "sub", "title", "source"):
            for ch in str(r.get(field, "")):
                cp = ord(ch)
                if GlyphText.is_special(cp) and f"U+{cp:X}" not in inline:
                    needed.add(cp)
    if needed:
        from fontTools.ttLib import TTFont
        for f in meta["fonts"]:
            p = os.path.join(SITE, f["file"].replace("/", os.sep))
            try:
                tt = TTFont(p, lazy=True)
                have = set()
                for table in tt["cmap"].tables:
                    have.update(table.cmap.keys())
                got = sorted(needed & have)
                if got:
                    f["_cmap"] = got
                tt.close()
            except Exception:  # noqa: BLE001
                pass
        print(f"[font] {len(needed)} chars need font rendering")

    staging = os.path.join(out_dir, "staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    os.makedirs(os.path.join(staging, "glyph"), exist_ok=True)
    os.makedirs(os.path.join(staging, "ig"), exist_ok=True)

    gt = GlyphText(inline, meta["fonts"])

    # group records by main head
    heads = {}
    for r in records:
        heads.setdefault(r["main"], []).append(r)
    order = sorted(heads)
    if limit:
        order = order[:limit]
    print(f"[data] {len(records):,} records -> {len(heads):,} heads, building {len(order):,}")

    # ---- component reverse index (一级构件) ----
    built = set(order)
    comp_of_head = {}
    for h in order:
        v = chars.get(h)
        if not v:
            continue
        cs = direct_components(v, h)
        if cs:
            comp_of_head[h] = cs
    rev = {}
    for h, cs in comp_of_head.items():
        for c in cs:
            rev.setdefault(c, set()).add(h)
    comp_keys = sorted(rev)

    def comp_items(c):
        items = set(rev.get(c, ()))
        if c in built:
            items.add(c)          # 等于该构件的词头也算
        return sorted(items)

    comp_only = [c for c in comp_keys if c not in built and not has_special(c)]
    max_items = max((len(comp_items(c)) for c in comp_keys), default=0)
    max_pages = max(1, (max_items + PAGE_SIZE - 1) // PAGE_SIZE)
    COMP = COMP_CSS + pager_css(max_pages)
    print(f"[comp] {len(comp_keys):,} components, {len(comp_only):,} component-only keys, "
          f"largest list {max_items} -> {max_pages} pages")

    # ---- convert glyph images (only for built heads) ----
    todo = []
    for h in order:
        for r in heads[h]:
            src = os.path.join(SITE, r["image"].replace("/", os.sep))
            dst = os.path.join(staging, "glyph", r["id"] + ".png")
            if not os.path.exists(dst):
                todo.append((src, dst))
    print(f"[img ] converting {len(todo):,} webp -> png")
    done = 0
    for src, dst in todo:
        with Image.open(src) as im:
            im.convert("L").save(dst, "PNG", optimize=True)
        done += 1
        if done % 5000 == 0:
            print(f"       {done:,}/{len(todo):,}  {time.time()-t0:.0f}s")

    # ---- build article text ----
    txt_path = os.path.join(out_dir, "source.txt")
    ann = annotations.get("records", {})
    entries = 0
    with open(txt_path, "w", encoding="utf-8", newline="\n") as out:
        for h in order:
            rows = sorted(heads[h], key=lambda r: (r.get("pdfPage") or 0, r.get("group") or "", r["id"]))
            n = len(rows)
            ids = ""
            entry = chars.get(h)
            if entry:
                bits = entry.split()
                if len(bits) > 1:
                    # chars.json 的 IDS 带着异体注记与「;」分隔的备选结构，
                    # 表头只显示第一种、去掉 {…} (…) #XX 之后的干净写法。
                    cand = clean_ids(bits[1]).split(";")[0].strip()
                    if cand and cand[0] in "⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻":
                        ids = cand
            is_comp = h in rev
            parts = [style_block(CSS_BODY, COMP if is_comp else ""), '<div class="jw">']
            back = ""
            if has_special(h):
                back = f' <a class="jw-back" href="entry://{INDEX_KEY}">↑ {INDEX_KEY}</a>'
            parts.append(
                f'<div class="jw-h"><span class="jw-ch">{gt.html(h, staging)}</span>'
                f'<span class="jw-ids">{esc(ids)}</span>'
                f'<span class="jw-n">{n} 個字形</span>{back}</div>'
            )
            for r in rows:
                sub = "" if r.get("sub") == h else r.get("sub") or ""
                page = []
                if r.get("book"):
                    page.append(r["book"])
                if r.get("group"):
                    page.append("第%s組" % r["group"])
                page.append("PDF%d" % (r.get("pdfPage") or 0))
                if r.get("printPage"):
                    page.append("頁%s" % r["printPage"])
                card = [
                    '<div class="jw-c">',
                    f'<img class="g" src="glyph/{r["id"]}.png" alt="{esc(r.get("title"))}">',
                ]
                title = gt.html(r.get("title"), staging)
                card.append(f'<div class="jw-t">{title}</div>')
                if sub:
                    card.append(f'<div class="jw-m">〔{gt.html(sub, staging)}〕</div>')
                if r.get("period"):
                    card.append(f'<div class="jw-m">{esc(r["period"])}</div>')
                if r.get("source"):
                    card.append(f'<div class="jw-s">{gt.html(r["source"], staging)}</div>')
                card.append(f'<div class="jw-p">{esc(" · ".join(page))}</div>')
                a = ann.get(r["id"])
                if a:
                    bits = []
                    if a.get("xieshengDomain"):
                        bits.append("諧聲域 " + a["xieshengDomain"])
                    if a.get("phoneticInitials"):
                        bits.append("聲首 " + "、".join(
                            p.get("primary", "") for p in a["phoneticInitials"] if p.get("primary")))
                    if a.get("semanticComponents"):
                        bits.append("義符 " + "、".join(a["semanticComponents"]))
                    if a.get("words"):
                        bits.append("詞義 " + "；".join(
                            "：".join(x for x in (w.get("meaning"), w.get("example")) if x)
                            for w in a["words"][:2]))
                    if a.get("note"):
                        bits.append("備註 " + a["note"])
                    if bits:
                        card.append(f'<div class="jw-note">{esc("；".join(bits))}</div>')
                card.append("</div>")
                parts.append("".join(card))
            if is_comp:
                parts.append(render_component(h, comp_items(h)))
            parts.append("</div>")
            body = "".join(parts).replace("\n", " ")
            out.write(h + "\n")
            out.write(body + "\n")
            out.write("</>\n")
            entries += 1
    print(f"[txt ] {entries:,} entries -> {txt_path} ({os.path.getsize(txt_path)/1048576:.1f} MB)")

    # ---- component-only entries: 构件存在但没有字头正文 ----
    comp_path = os.path.join(out_dir, "component.txt")
    with open(comp_path, "w", encoding="utf-8", newline="\n") as out:
        for c in comp_only:
            items = comp_items(c)
            parts = [
                style_block(CSS_BODY, COMP),
                '<div class="jw">',
                f'<div class="jw-h"><span class="jw-ch">{c}</span>'
                f'<span class="jw-n">構件 · 無字頭正文</span></div>',
                render_component(c, items),
                "</div>",
            ]
            out.write(c + "\n")
            out.write("".join(parts).replace("\n", " ") + "\n")
            out.write("</>\n")
    print(f"[txt ] {len(comp_only):,} component-only entries -> {comp_path}")

    # aliases for distinct sub heads that differ from main
    comp_only_set = set(comp_only)
    alias_path = os.path.join(out_dir, "alias.txt")
    al = 0
    with open(alias_path, "w", encoding="utf-8", newline="\n") as out:
        seen = set(order) | comp_only_set
        for h in order:
            for r in heads[h]:
                s = r.get("sub") or ""
                if s and s != h and s not in seen and not has_special(s):
                    out.write(s + "\n@@@LINK=" + h + "\n</>\n")
                    seen.add(s)
                    al += 1
    print(f"[txt ] {al:,} alias entries -> {alias_path}")

    # index of heads whose own key cannot be typed (contains unencodable glyphs)
    special_heads = [h for h in order if has_special(h)]
    index_path = os.path.join(out_dir, "index.txt")
    with open(index_path, "w", encoding="utf-8", newline="\n") as out:
        parts = [style_block(CSS_BODY), '<div class="jw">']
        parts.append(
            f'<div class="jw-h"><span class="jw-ch">未編碼字頭</span>'
            f'<span class="jw-n">{len(special_heads)} 個字頭含未編碼字形，字頭本身無法輸入，'
            f'請由此點擊進入</span></div>'
        )
        for h in special_heads:
            r = heads[h][0]
            href = esc(h).replace('"', "&quot;")
            parts.append(
                '<div class="jw-c">'
                f'<a href="entry://{href}"><img class="g" src="glyph/{r["id"]}.png" alt=""></a>'
                f'<div class="jw-t">{gt.html(r.get("title"), staging)}</div>'
                f'<div class="jw-m">{esc(r.get("period"))}</div>'
                f'<div class="jw-p">{len(heads[h])} 形</div></div>'
            )
        parts.append("</div>")
        out.write(INDEX_KEY + "\n")
        out.write("".join(parts).replace("\n", " ") + "\n")
        out.write("</>\n")
    print(f"[txt ] index entry with {len(special_heads):,} heads -> {index_path}")

    print(f"[done] staging {staging}")
    print(f"[size] images {sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(staging) for f in fs)/1048576:.1f} MB")
    print(f"[time] {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "_build"))
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    build(a.out, a.limit)
