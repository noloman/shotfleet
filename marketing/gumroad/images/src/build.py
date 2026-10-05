#!/usr/bin/env python3
"""Builds thumbnail-600.png and cover-1..4.png for the Gumroad product page.

    python3 marketing/gumroad/images/src/build.py

Pillow only. Everything is drawn at 2x and downsampled (LANCZOS) for crisp edges.
Fonts: Geist Mono (site/public/fonts, SIL OFL) for all text; Hiragino Sans (macOS) for the one Japanese word.
Screenshots: only the real ones in site/public/img (see README.md next to this folder).
Palette: the tokens of site/public/site.css.
icon-*.png and icon.svg come from ../icon.svg with rsvg-convert (see README.md).
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
IMG = os.path.join(REPO, "site/public/img")
FONTS = os.path.join(REPO, "site/public/fonts")
S = 2  # supersampling

INK, BLUE, YELLOW, PAPER = "#0b1220", "#1b3fd1", "#f5c400", "#f1f2f4"
LINE, MUTED, WHITE = "#cfd5de", "#55627a", "#ffffff"
RED, PASS = "#c8281c", "#17693a"                    # light-theme tokens
RED_D, PASS_D = "#ff6b5e", "#4ed17a"                # dark-theme tokens (for use on INK)
TERM_TEXT, TERM_DIM = "#dbe6f3", "#7f93ab"
HIRAGINO = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"

_fc = {}


def _face(kind, size, weight):
    key = (kind, size, weight)
    if key not in _fc:
        if kind == "ja":
            f = ImageFont.truetype(HIRAGINO, int(size * S))
        else:
            f = ImageFont.truetype(os.path.join(FONTS, f"geist-mono-{kind}.woff2"), int(size * S))
            f.set_variation_by_axes([weight])
        _fc[key] = f
    return _fc[key]


def _kind(ch):
    o = ord(ch)
    if 0x0100 <= o <= 0x024F:
        return "latin-ext"   # for example the Turkish dotted capital I
    if o >= 0x3000:
        return "ja"
    return "latin"


def _segments(s):
    segs = []
    for ch in s:
        k = _kind(ch)
        if segs and segs[-1][0] == k:
            segs[-1][1] += ch
        else:
            segs.append([k, ch])
    return segs


def width(s, size, weight=400):
    return sum(_face(k, size, weight).getlength(t) for k, t in _segments(s)) / S


def wrap(s, size, weight, maxw):
    lines, cur = [], ""
    for w in s.split(" "):
        t = (cur + " " + w).strip()
        if width(t, size, weight) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h, self.bg = w, h, bg
        self.im = Image.new("RGB", (w * S, h * S), bg)
        self.d = ImageDraw.Draw(self.im)

    def text(self, x, y, s, size, weight=400, fill=INK, anchor="l"):
        """y is the baseline. anchor l, m or r on x."""
        wd = width(s, size, weight)
        x0 = x - (wd / 2 if anchor == "m" else wd if anchor == "r" else 0)
        for k, t in _segments(s):
            f = _face(k, size, weight)
            self.d.text((x0 * S, y * S), t, font=f, fill=fill, anchor="ls")
            x0 += f.getlength(t) / S
        return wd

    def para(self, x, y, s, size, weight, fill, maxw, lh):
        lines = wrap(s, size, weight, maxw)
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, size, weight, fill)
        return y + len(lines) * lh

    def rrect(self, box, r, fill=None, outline=None, w=1):
        x0, y0, x1, y1 = [v * S for v in box]
        self.d.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), r * S, fill=fill, outline=outline, width=int(w * S))

    def shadow(self, box, r, blur=14, dy=10, color=(11, 18, 32), alpha=70):
        pad = blur * 3
        x0, y0, x1, y1 = box
        sw, sh = int((x1 - x0 + 2 * pad) * S), int((y1 - y0 + 2 * pad) * S)
        m = Image.new("L", (sw, sh), 0)
        ImageDraw.Draw(m).rounded_rectangle((pad * S, pad * S, (pad + x1 - x0) * S, (pad + y1 - y0) * S), r * S, fill=alpha)
        m = m.filter(ImageFilter.GaussianBlur(blur * S / 2))
        layer = Image.new("RGB", (sw, sh), color)
        self.im.paste(layer, (int((x0 - pad) * S), int((y0 + dy - pad) * S)), m)

    def mark(self, x, y, w, fill):
        """The shotfleet glyph (24-unit path M3 4h18l-4.5 8L21 20H3z), bbox 18 x 16, scaled to width w, top-left at x, y."""
        k = w / 18 * S
        pts = [(0, 0), (18, 0), (13.5, 8), (18, 16), (0, 16)]
        self.d.polygon([(x * S + px * k, y * S + py * k) for px, py in pts], fill=fill)

    def shot(self, name, x, y, w, bezel=4, stamp=None, flat_border=None, crop_h=None):
        """A screenshot in a simple rounded device-like frame. Returns (w, h)."""
        im = Image.open(os.path.join(IMG, name)).convert("RGB")
        h = round(w * im.height / im.width)
        vis = h if crop_h is None else min(h, crop_h)
        ri = max(8, round(w * 0.11))
        if flat_border is None:
            ro = ri + bezel
            outer = (x - bezel, y - bezel, x + w + bezel, y + vis + (bezel if crop_h is None else 0))
            self.shadow(outer, ro)
            self.rrect(outer, ro, fill=INK)
            inner = (x, y)
        else:
            col, bw = flat_border
            outer = (x - bw, y - bw, x + w + bw, y + vis + bw)
            ri = 6
            self.rrect(outer, ri + bw, fill=col)
            inner = (x, y)
        sc = im.resize((w * S, h * S), Image.LANCZOS)
        if crop_h is not None:
            sc = sc.crop((0, 0, w * S, vis * S))
        mask = Image.new("L", sc.size, 0)
        md = ImageDraw.Draw(mask)
        if crop_h is None:
            md.rounded_rectangle((0, 0, sc.width - 1, sc.height - 1), ri * S, fill=255)
        else:  # bleeds off the bottom: round the top corners only
            md.rounded_rectangle((0, 0, sc.width - 1, sc.height + ri * S), ri * S, fill=255)
        self.im.paste(sc, (inner[0] * S, inner[1] * S), mask)
        if stamp:
            cx, cy, r = x + w - 2, y + 2, 12
            self.d.ellipse(((cx - r - 3) * S, (cy - r - 3) * S, (cx + r + 3) * S, (cy + r + 3) * S), fill=self.bg)
            self.d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=stamp)
            pts = [(cx - 5.5, cy + 0.5), (cx - 1.5, cy + 4.5), (cx + 6, cy - 4)]
            self.d.line([(px * S, py * S) for px, py in pts], fill=WHITE, width=int(2.6 * S), joint="curve")
        return w, h

    def chip(self, x, y, s, size, fg, bg, weight=700, padx=10, pady=6, anchor="l", outline=None):
        wd = width(s, size, weight)
        x0 = x - (wd + 2 * padx) / 2 if anchor == "m" else x
        self.rrect((x0, y, x0 + wd + 2 * padx, y + size + 2 * pady), 4, fill=bg, outline=outline, w=1.5)
        self.text(x0 + padx, y + pady + size * 0.8, s, size, weight, fg)
        return x0 + wd + 2 * padx

    def brand(self, x, y, size, color_mark, color_word, anchor="l"):
        mw = size * 0.95
        word = width("shotfleet", size, 700)
        total = mw + size * 0.32 + word
        x0 = x - total if anchor == "r" else x
        self.mark(x0, y + size * 0.1, mw, color_mark)
        self.text(x0 + mw + size * 0.32, y + size * 0.82, "shotfleet", size, 700, color_word)

    def save(self, name):
        out = self.im.resize((self.w, self.h), Image.LANCZOS)
        out.save(os.path.join(OUT, name), "PNG", optimize=True)
        print("wrote", name, out.size)


# --------------------------------------------------------------------------- thumbnail
def thumbnail():
    c = Canvas(600, 600, INK)
    p = 56
    mw = 124
    c.mark(p, 112, mw, YELLOW)
    c.text(p, 112 + mw * 16 / 18 + 78, "shotfleet", 76, 700, WHITE)
    promise = ["Store screenshots", "in every language", "your app ships."]
    y = 112 + mw * 16 / 18 + 78 + 62
    for i, ln in enumerate(promise):
        c.text(p, y + i * 56, ln, 42, 500, TERM_TEXT)
    c.save("thumbnail-600.png")


# --------------------------------------------------------------------------- cover 1: hero
HERO = ["train_ar", "train_de", "train_fr", "train_es", "train_ja", "train_ko", "train_ru"]


def cover1():
    c = Canvas(1280, 720, PAPER)
    L, TW = 64, 520
    c.brand(L, 52, 30, BLUE, INK)
    c.chip(L, 142, "Mac command-line tool · Apple silicon", 15, WHITE, BLUE, 600)
    y = 232
    for i, ln in enumerate(["Store screenshots", "in every language", "your app ships."]):
        c.text(L, y + i * 62, ln, 48, 700, INK)
    y = c.para(L, y + 3 * 62 + 14, "One English Maestro flow, every language, iOS and Android.", 22, 400, INK, TW, 32)
    c.para(L, y + 10, "shotfleet captures them all and checks every screenshot.", 22, 700, INK, TW, 32)
    c.para(L, 654, "Seven of 72 screenshots from one run on my app, WOD Tracker: 18 languages × 4 screens on an M1 Pro.", 14, 400, MUTED, TW + 20, 21)
    w, gap = 129, 18
    x0 = 1280 - 64 - (4 * w + 3 * gap)
    cell_h = 280 + 30
    y0 = (720 - (2 * cell_h + 14)) // 2 + 8
    for i in range(8):
        x = x0 + (i % 4) * (w + gap)
        y = y0 + (i // 4) * (cell_h + 14)
        if i < 7:
            nm = HERO[i]
            c.shot(nm + ".jpg", x, y, w, stamp=PASS)
            c.text(x + w / 2, y + 280 + 24, nm[-2:], 15, 700, INK, "m")
        else:
            c.shadow((x - 4, y - 4, x + w + 4, y + 284), 25)
            c.rrect((x - 4, y - 4, x + w + 4, y + 284), 25, fill=INK)
            c.text(x + w / 2, y + 128, "+11", 44, 700, YELLOW, "m")
            c.text(x + w / 2, y + 160, "more languages", 13, 400, TERM_TEXT, "m")
            c.text(x + w / 2, y + 178, "in the same run", 13, 400, TERM_TEXT, "m")
    c.save("cover-1.png")


# --------------------------------------------------------------------------- cover 2: the problem
def cover2():
    c = Canvas(1280, 720, INK)
    pw = 330
    px, py = 96, 44
    w, h = c.shot("bug_zh.jpg", px, py, pw, bezel=5)
    c.chip(px + pw / 2, py + h - 24, "zh · Next is off-screen", 16, WHITE, RED, 700, anchor="m", pady=7)
    X, TW = 540, 676
    c.brand(1216, 38, 24, YELLOW, WHITE, anchor="r")
    c.text(X, 140, "THE PROBLEM", 16, 700, RED_D)
    y = 200
    for i, ln in enumerate(["A flow that taps “Next”", "only works in English."]):
        c.text(X, y + i * 50, ln, 40, 700, WHITE)
    y = c.para(X, y + 2 * 50 + 12, "Japanese, Korean, Chinese and Arabic all got stuck on one onboarding page of my app: Next was below the bottom of a small phone. English fit, so nobody noticed.", 21, 400, TERM_TEXT, TW, 31)
    ly = 468
    c.d.line((X * S, ly * S, (X + TW) * S, ly * S), fill="#243449", width=2 * S)
    c.text(X, ly + 50, "THE FIX", 16, 700, YELLOW)
    c.para(X, ly + 102, "shotfleet reads the translations compiled into your build and rewrites every text selector.", 28, 700, WHITE, TW, 40)
    c.save("cover-2.png")


# --------------------------------------------------------------------------- cover 3: one flow, every language
def card(c, box, title):
    c.shadow(box, 8, blur=10, dy=8, alpha=40)
    c.rrect(box, 8, fill=INK)
    c.text(box[0] + 22, box[1] + 30, title, 14, 400, TERM_DIM)


def cover3():
    c = Canvas(1280, 720, PAPER)
    L = 64
    c.text(L, 96, "One flow, every language.", 48, 700, INK)
    c.brand(1216, 56, 24, BLUE, INK, anchor="r")
    c.text(L, 140, "Your flow says Next. Each language gets its own word.", 22, 400, MUTED)
    top, bot = 176, 404
    # flow.yaml
    ax1 = 430
    card(c, (L, top, ax1, bot), "flow.yaml")
    for i, ln in enumerate(['- tapOn: "Next"', '- tapOn: "Log"', "- takeScreenshot: 02_log"]):
        c.text(L + 22, top + 78 + i * 34, ln, 20, 500, TERM_TEXT)
    c.text(L + 22, top + 184, "(English, once)", 14, 400, TERM_DIM)
    # shotfleet.toml
    bx0, bx1 = ax1 + 16, ax1 + 16 + 250
    card(c, (bx0, top, bx1, bot), "shotfleet.toml")
    c.text(bx0 + 22, top + 78, "[ios]", 20, 500, TERM_TEXT)
    c.text(bx0 + 22, top + 112, 'app = "', 20, 500, TERM_TEXT)
    wv = width('app = "', 20, 500)
    c.text(bx0 + 22 + wv, top + 112, "MyApp.app", 20, 500, YELLOW)
    c.text(bx0 + 22 + wv + width("MyApp.app", 20, 500), top + 112, '"', 20, 500, TERM_TEXT)
    c.text(bx0 + 22, top + 184, "(two lines)", 14, 400, TERM_DIM)
    # arrow
    ax = bx1 + 12
    cy = (top + bot) / 2
    c.d.line((ax * S, cy * S, (ax + 36) * S, cy * S), fill=BLUE, width=5 * S)
    c.d.polygon([((ax + 52) * S, cy * S), ((ax + 32) * S, (cy - 14) * S), ((ax + 32) * S, (cy + 14) * S)], fill=BLUE)
    # per-language selectors
    cx0, cx1 = ax + 64, 1216
    card(c, (cx0, top, cx1, bot), "what each language runs")
    rows = [("German", [("tapOn: '", False), ("(Nächste|Weiter)", True), ("'", False)]),
            ("Japanese", [("tapOn: '", False), ("次へ", True), ("'", False)]),
            ("Turkish", [("tapOn: '", False), ("İleri", True), ("'", False)])]
    for i, (lang, parts) in enumerate(rows):
        yy = top + 86 + i * 46
        c.text(cx0 + 22, yy - 22, lang, 13, 400, TERM_DIM)
        x = cx0 + 22
        for t, hl in parts:
            x += c.text(x, yy + 4, t, 20, 500, YELLOW if hl else TERM_TEXT)
    c.text(cx0 + 22, bot - 12, "Warning before the run: it also means “Advanced”.", 12, 400, TERM_DIM)
    # screenshots bleeding off the bottom
    w, gap = 150, 17
    x0 = (1280 - (7 * w + 6 * gap)) // 2
    ty = 442
    for i, nm in enumerate(HERO):
        x = x0 + i * (w + gap)
        c.text(x + w / 2, ty - 8, nm[-2:], 15, 700, INK, "m")
        c.shot(nm + ".jpg", x, ty, w, bezel=4, crop_h=720 - ty + 8)
    c.save("cover-3.png")


# --------------------------------------------------------------------------- cover 4: the check
def cover4():
    c = Canvas(1280, 720, PAPER)
    L = 64
    c.text(L, 96, "Then every screenshot is checked.", 44, 700, INK)
    c.brand(1216, 40, 24, BLUE, INK, anchor="r")
    c.text(L, 140, "Every image is read back and compared with your app’s own strings.", 22, 400, MUTED)
    order = ["train_ar", "train_de", "train_fr", "train_fr", "train_ja", "train_ko", "train_ru"]  # 4th slot is es: the French image, planted
    codes = ["ar", "de", "fr", "es", "ja", "ko", "ru"]
    w, gap = 138, 28
    x0 = (1280 - (7 * w + 6 * gap)) // 2
    ty = 238
    for i, (nm, code) in enumerate(zip(order, codes)):
        x = x0 + i * (w + gap)
        planted = code == "es"
        c.text(x + w / 2, ty - 14, code, 16, 700, RED if planted else INK, "m")
        c.shot(nm + ".jpg", x, ty, w, flat_border=(RED, 5) if planted else (LINE, 2))
        if planted:
            px, bottom = x + w / 2, ty + round(w * 782 / 360) + 5
    # callout under the planted tile
    cy = bottom + 18
    c.d.line((px * S, bottom * S, px * S, cy * S), fill=RED, width=3 * S)
    c.chip(px, cy, "planted to test the check", 22, WHITE, RED, 700, anchor="m", padx=14, pady=8)
    c.text(px, cy + 70, "The Spanish slot holds the French image. Copies: the same image in two languages.", 15, 400, INK, "m")
    c.text(L, 680, "check", 19, 700, BLUE)
    x = L + width("check", 19, 700)
    x += c.text(x, 680, " is free for everyone. ", 19, 400, INK)
    c.text(x, 680, "run", 19, 700, BLUE)
    x += width("run", 19, 700)
    c.text(x, 680, " is free for up to 2 languages.", 19, 400, INK)
    c.rrect((L, 168, L + 22, 190), 4, outline=RED, w=3)
    c.text(L + 34, 186, "Problems are outlined in red.", 17, 400, INK)
    c.save("cover-4.png")


if __name__ == "__main__":
    thumbnail()
    cover1()
    cover2()
    cover3()
    cover4()
