#!/usr/bin/env python3
"""Build marketing/gumroad/video/shotfleet-product.mp4 and poster.png.

Everything on screen is read at build time from real files in this repo (images, log lines, flow and config lines,
llms.txt wording); nothing is retyped here except the captions, which are listed in README.md with their source.
Needs: python3 + Pillow, ffmpeg (libx264), rsvg-convert. Run: bash marketing/gumroad/video/src/build.sh
Env: PRICE=0 leaves out the price line on the end card (use it if the sale is not live).
"""
import os, subprocess, sys, functools
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)                      # marketing/gumroad/video
ROOT = os.path.abspath(os.path.join(OUT, "../../.."))
P = lambda *a: os.path.join(ROOT, *a)

W, H, FPS = 1920, 1080, 30
INK, YEL = (11, 18, 32), (245, 196, 0)
PAPER, TERM_BG, TERM_TXT, DIM = (241, 242, 244), (6, 12, 20), (219, 230, 243), (127, 147, 171)
LINE, PASS = (36, 52, 73), (78, 209, 122)
GEIST = P("site/public/fonts/geist-mono-latin.woff2")
JP = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
PRICE = os.environ.get("PRICE", "1") != "0"

# ---------------------------------------------------------------- fonts / text
@functools.lru_cache(None)
def geist(size, weight=400):
    f = ImageFont.truetype(GEIST, size); f.set_variation_by_axes([weight]); return f
@functools.lru_cache(None)
def jp(size): return ImageFont.truetype(JP, size)
def fnt(ch, size, weight): return geist(size, weight) if ord(ch) < 0x250 or ch in "…—·×" else jp(size)
def tw(s, size, weight=400): return sum(fnt(c, size, weight).getlength(c) for c in s)
def text(d, x, y, s, size, fill, weight=400):
    """Draw s with baseline at y; Geist Mono for Latin, Hiragino Sans (system font) for Japanese."""
    for c in s:
        f = fnt(c, size, weight); d.text((x, y), c, font=f, fill=fill, anchor="ls"); x += f.getlength(c)
    return x
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def wrap(s, size, weight, maxw):
    out, cur = [], ""
    for w_ in s.split(" "):
        t = (cur + " " + w_).strip()
        if tw(t, size, weight) <= maxw: cur = t
        else: out.append(cur); cur = w_
    return out + [cur]

def real_lines(path, a, b):
    with open(P(path), encoding="utf-8") as f: ls = f.read().split("\n")
    return ls[a - 1:b]
def shorten(line, keep_start, keep_end):
    return line[:keep_start] + "…" + line[len(line) - keep_end:]

# ---------------------------------------------------------------- assets
def load_img(rel): return Image.open(P(rel)).convert("RGB")
def favicon(px):
    tmp = os.path.join(HERE, ".fav.png")
    subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px), "-o", tmp, P("site/public/favicon.svg")], check=True)
    im = Image.open(tmp).convert("RGBA"); im.load(); os.remove(tmp); return im
FAV = {s: favicon(s) for s in (48, 140)}

def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), r, fill=255)
    out = im.convert("RGBA"); out.putalpha(m); return out

# ---------------------------------------------------------------- shared chrome
def base():
    img = Image.new("RGB", (W, H), INK); return img, ImageDraw.Draw(img)
def brand(img, d):
    img.paste(FAV[48], (60, 34), FAV[48]); text(d, 124, 70, "shotfleet", 34, PAPER, 700)

CAP_Y0 = 840
def caption_band(img, d, caps, t, src):
    d.rectangle((0, CAP_Y0, W, H), fill=INK); d.line((0, CAP_Y0, W, CAP_Y0), fill=LINE, width=2)
    for (a, b, s) in caps:
        if not (a <= t < b): continue
        k = min(1.0, (t - a) / 0.25, (b - t) / 0.2)       # short fade between captions
        col = lerp(INK, PAPER, max(0.0, k))
        lines = wrap(s, 46, 700, 1640); assert len(lines) <= 2, s
        y = 905
        d.rectangle((92, y - 40, 100, y - 40 + 62 * len(lines) - 14), fill=lerp(INK, YEL, max(0.0, k)))
        for ln in lines: text(d, 128, y, ln, 46, col, 700); y += 62
    assert tw(src, 24) <= 1700, src
    text(d, 92, 1052, src, 24, DIM)

def card(d, x, y, w, h, title=None):
    d.rounded_rectangle((x, y, x + w, y + h), 14, fill=TERM_BG, outline=LINE, width=2)
    if title:
        text(d, x + 32, y + 46, title, 24, DIM); d.line((x + 2, y + 72, x + w - 2, y + 72), fill=LINE, width=2)

def code_block(d, x, y, lines, numbers, size, hi=()):
    """Verbatim code lines with a dim gutter; substrings in hi are drawn yellow."""
    adv = int(size * 1.55)
    for i, (n, ln) in enumerate(zip(numbers, lines)):
        by = y + i * adv
        text(d, x, by, f"{n:>2}", size, DIM)
        cx = x + tw("00  ", size)
        pos = 0; spans = []
        for h_ in hi:
            j = ln.find(h_)
            if j >= 0: spans.append((j, j + len(h_)))
        spans.sort()
        for (a, b) in spans:
            cx = text(d, cx, by, ln[pos:a], size, TERM_TXT); cx = text(d, cx, by, ln[a:b], size, YEL, 700); pos = b
        text(d, cx, by, ln[pos:], size, TERM_TXT)

# ---------------------------------------------------------------- scene 1: the problem
BUG = load_img("site/public/img/bug_zh.jpg")
S1_CAPS = [(0.3, 3.0, "Chinese, small Android phone: Next is off-screen."),
           (3.0, 5.8, "Japanese, Korean, Chinese and Arabic all got stuck here."),
           (5.8, 8.8, "English fit, so nobody noticed.")]
def scene1(t):
    img, d = base(); brand(img, d)
    vw, vh, top = 400, 710, 110
    p = ease(t / 8.8); s = 1.111 * (1 + 0.12 * p)
    im = BUG.resize((round(360 * s), round(640 * s)), Image.LANCZOS)
    view = Image.new("RGB", (vw, vh), (250, 250, 250))
    view.paste(im, ((vw - im.size[0]) // 2, vh - im.size[1]))     # anchored at the bottom: zooms toward the empty end
    vx = (W - vw) // 2
    img.paste(rounded(view, 22), (vx, top), rounded(view, 22))
    d.rounded_rectangle((vx, top, vx + vw, top + vh), 22, outline=LINE, width=3)
    text(d, 150, 330, "zh", 150, YEL, 700); text(d, 154, 390, "Android, small phone", 36, PAPER, 400)
    k = ease((t - 3.0) / 0.5)
    if k > 0:                                                    # annotation (not part of the screenshot)
        c = lerp(INK, YEL, k); by = top + vh
        d.line((vx + vw + 30, by - 90, vx + vw + 30, by - 10), fill=c, width=5)
        d.line((vx + vw + 16, by - 10, vx + vw + 30, by - 10), fill=c, width=5)
        text(d, vx + vw + 56, by - 52, "Next should be down here.", 36, c, 700)
        text(d, vx + vw + 56, by - 14, "(annotation, not part of the screenshot)", 24, lerp(INK, DIM, k))
    caption_band(img, d, S1_CAPS, t, "Real screenshot: site/public/img/bug_zh.jpg")
    return img

# ---------------------------------------------------------------- scene 2: one flow, short config, rewritten per language
FLOW_F = "examples/crossfittracker/ios.yaml"
TOML_F = "research/experiments-2026-10-04/C/shotfleet.toml"
C_DIR = "research/experiments-2026-10-04/C/"
def scene2a(t):
    img, d = base(); brand(img, d)
    ls = real_lines(FLOW_F, 26, 29)
    x, y, w, h = 210, 190, 1500, 420
    card(d, x, y, w, h, f"{FLOW_F}   lines 26-29")
    code_block(d, x + 40, y + 170, ls, range(26, 30), 40, hi=['"Next"'])
    caption_band(img, d, [(0.3, 3.2, "You write one flow, in English.")], t,
                 f"A real flow: {FLOW_F}, lines 26-29 (excerpt)")
    return img
def scene2b(t):
    img, d = base(); brand(img, d)
    raw = real_lines(TOML_F, 1, 4)
    ls = [raw[0], shorten(raw[1], 15, 22), shorten(raw[2], 14, 12), raw[3]]
    x, y, w, h = 160, 190, 1600, 480
    card(d, x, y, w, h, f"{TOML_F}   lines 1-4")
    code_block(d, x + 40, y + 160, ls, range(1, 5), 40)
    caption_band(img, d, [(0.3, 3.2, "Plus a short config: your app and your languages.")], t,
                 "A real config, long paths shortened with the … sign: " + TOML_F)
    return img
def scene2c(t):
    img, d = base(); brand(img, d)
    blocks = [("English, the flow you write", C_DIR + "flow.yaml", 4, 5, real_lines(C_DIR + "flow.yaml", 4, 5), 0.2),
              ("German, written by shotfleet", C_DIR + "translated-de.yaml", 11, 12, real_lines(C_DIR + "translated-de.yaml", 11, 12), 1.1),
              ("Japanese, written by shotfleet", C_DIR + "translated-ja.yaml", 11, 12, real_lines(C_DIR + "translated-ja.yaml", 11, 12), 2.0)]
    x, w = 210, 1500
    for i, (name, f, a, b, ls, t0) in enumerate(blocks):
        k = ease((t - t0) / 0.4)
        if k <= 0: continue
        y = 120 + i * 232 + int((1 - k) * 24)
        lay = img.copy(); ld = ImageDraw.Draw(lay)
        card(ld, x, y, w, 214, None)
        text(ld, x + 32, y + 42, f"{name}   {f.split('/')[-1]} lines {a}-{b}", 24, DIM)
        code_block(ld, x + 40, y + 108, ls, range(a, b + 1), 36)
        img = Image.blend(img, lay, k) if k < 1 else lay
        d = ImageDraw.Draw(img)
    brand(img, d)
    caption_band(img, d, [(0.3, 4.2, "shotfleet rewrites the text for every language.")], t,
                 "Same real run: " + C_DIR + "flow.yaml, translated-de.yaml, translated-ja.yaml")
    return img

# ---------------------------------------------------------------- scene 3: real run output, replayed
RUN_F = C_DIR + "run.log"
RUN = real_lines(RUN_F, 1, 7)
RUN_START = [0.6, 1.6, 2.5, 3.0, 4.6, None, 5.8]          # when each line starts typing; line 6 is blank
CPS = 80
S3_CAPS = [(0.3, 4.2, "Then shotfleet run captures every language."),
           (4.2, 8.4, "And reads each screenshot back to check it.")]
def scene3(t):
    img, d = base(); brand(img, d)
    x, y, w, h = 150, 120, 1620, 620
    card(d, x, y, w, h, None)
    d.rectangle((x + 2, y + 2, x + w - 2, y + 96), fill=(16, 26, 44))
    text(d, x + 36, y + 46, "OUTPUT OF A REAL RUN, REPLAYED FROM A SAVED LOG. NOT LIVE.", 28, YEL, 700)
    text(d, x + 36, y + 82, "2 languages, 1 simulator, a sample app. Replayed fast: the real run took 394 s.", 24, DIM)
    by = y + 170; last = None
    for i, ln in enumerate(RUN):
        st = RUN_START[i]
        if st is None:
            if t >= RUN_START[i + 1]: by += 62            # the empty line 6 of the log
            continue
        if t < st: continue
        n = min(len(ln), int((t - st) * CPS) + 1)
        shown = ln[:n]
        if shown.startswith("ok "):
            x2 = text(d, x + 48, by, "ok", 40, PASS, 700); text(d, x2, by, shown[2:], 40, TERM_TXT)
        else: text(d, x + 48, by, shown, 40, TERM_TXT)
        if i == 6 and n == len(ln) and t > st + len(ln) / CPS + 0.3:
            j = ln.index("0 problem(s)"); x0 = x + 48 + tw(ln[:j], 40); x1 = x0 + tw("0 problem(s)", 40)
            d.rectangle((x0 - 6, by - 38, x1 + 6, by + 14), outline=PASS, width=4)
        last = (i, n, len(ln), by)
        by += 62
    if last and (int(t * 2) % 2 == 0 or last[1] < last[2]):                    # blinking block cursor
        cx = x + 48 + tw(RUN[last[0]][:last[1]], 40)
        d.rectangle((cx + 4, last[3] - 34, cx + 24, last[3] + 6), fill=TERM_TXT)
    caption_band(img, d, S3_CAPS, t, f"Real output, verbatim: {RUN_F}, lines 1-7 (line 6 is empty)")
    return img

# ---------------------------------------------------------------- scene 4: grid of real localized screenshots
LANGS = ["ar", "de", "es", "fr", "ja", "ko", "ru"]
SHOTS = {l: load_img(f"site/public/img/train_{l}.jpg") for l in LANGS}
TH = 520; TWD = round(360 * TH / 782); GAP = 22
S4_CAPS = [(0.3, 3.8, "Seven of 72 screenshots from one real run, all checked."),
           (3.8, 7.4, "18 languages x 4 screens: 9 minutes on iOS, 15 on Android.")]
def tiles(img, d, t, y0, stagger=0.45, t0=0.4):
    x0 = (W - (7 * TWD + 6 * GAP)) // 2
    for i, l in enumerate(LANGS):
        k = ease((t - t0 - i * stagger) / 0.4)
        if k <= 0: continue
        x = x0 + i * (TWD + GAP); y = y0 + int((1 - k) * 28)
        im = rounded(SHOTS[l].resize((TWD, TH), Image.LANCZOS), 14)
        a = im.getchannel("A").point(lambda v: int(v * k)); im.putalpha(a)
        img.paste(im, (x, y), im)
        c = lerp(INK, PAPER, k); text(d, x + 6, y0 + TH + 52, l, 40, c, 700)
        cx, cy = x + TWD - 26, y0 + TH + 34                 # "checked" stamp, under the tile
        d.ellipse((cx - 20, cy - 20, cx + 20, cy + 20), fill=lerp(INK, (23, 105, 58), k))
        d.line([(cx - 9, cy), (cx - 2, cy + 7), (cx + 10, cy - 7)], fill=lerp(INK, (255, 255, 255), k), width=5, joint="curve")
def scene4(t):
    img, d = base(); brand(img, d)
    tiles(img, d, t, 150)
    d = ImageDraw.Draw(img)
    caption_band(img, d, S4_CAPS, t, "Real screenshots: site/public/img/train_{ar,de,es,fr,ja,ko,ru}.jpg (my app, WOD Tracker, M1 Pro)")
    return img

# ---------------------------------------------------------------- scene 5: end card (wording from site/public/llms.txt)
def llms_line(prefix):
    for ln in open(P("site/public/llms.txt"), encoding="utf-8"):
        if ln.startswith(prefix): return ln[2:].strip()
    raise SystemExit("llms.txt line not found: " + prefix)
FREE = llms_line("- `check` is free")              # "`check` is free for everyone. `run` is free for up to 2 languages."
LIC = llms_line("- A licence unlocks")              # first sentence only: the price line
PRICE_LINE = LIC.split(". ")[0] + "."
REQ = "Apple silicon Mac, Maestro 2.x, Java 17+"
def rich(d, x, y, s, size, base_col, code_col=YEL):
    """Draw s; `code` spans lose their backticks and are drawn in yellow bold."""
    for i, part in enumerate(s.split("`")):
        x = text(d, x, y, part, size, code_col if i % 2 else base_col, 700 if i % 2 else 400)
    return x
def rich_w(s, size): return sum(tw(p, size, 700 if i % 2 else 400) for i, p in enumerate(s.split("`")))
def scene5(t):
    img, d = base()
    k0 = ease((t - 0.4) / 0.5)
    nw = tw("shotfleet", 130, 700); x0 = int((W - (175 + nw)) / 2)
    fav = FAV[140]; img.paste(fav, (x0, 150), fav); text(d, x0 + 175, 262, "shotfleet", 130, lerp(INK, PAPER, k0), 700)
    k1 = ease((t - 1.6) / 0.5)
    if k1 > 0:
        c = lerp(INK, PAPER, k1); x = (W - rich_w(FREE, 44)) // 2
        rich(d, x, 450, FREE, 44, c, lerp(INK, YEL, k1))
    k2 = ease((t - 3.6) / 0.5)
    if k2 > 0 and PRICE:
        c = lerp(INK, PAPER, k2); a, b = PRICE_LINE.split(": ")
        for i, ln in enumerate([a + ":", b]):
            x = (W - rich_w(ln, 44)) // 2; rich(d, x, 545 + i * 64, ln, 44, c, lerp(INK, YEL, k2))
    k3 = ease((t - (5.4 if PRICE else 3.6)) / 0.5)
    if k3 > 0:
        text(d, (W - tw(REQ, 40)) // 2, 775, REQ, 40, lerp(INK, PAPER, k3))
        text(d, (W - tw("shotfleet.com", 48, 700)) // 2, 880, "shotfleet.com", 48, lerp(INK, YEL, k3), 700)
    return img

SCENES = [(scene1, 8.8), (scene2a, 3.4), (scene2b, 3.4), (scene2c, 4.4), (scene3, 8.4), (scene4, 7.4), (scene5, 8.4)]
FADE = 0.25

def frame_at(i, t):
    fn, dur = SCENES[i]; im = fn(t)
    a = min(1.0, t / FADE, (dur - t) / FADE)
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), INK), im, max(0.0, a))

def poster():
    img, d = base(); brand(img, d)
    text(d, 60, 170, "Store screenshots in every language your app ships.", 56, PAPER, 700)
    tiles(img, d, 99, 250); d = ImageDraw.Draw(img)
    text(d, 60, 1000, "One English Maestro flow, every language, iOS and Android.", 40, YEL, 700)
    return img.resize((1280, 720), Image.LANCZOS)

def main():
    if "--stills" in sys.argv:                        # debug: a few stills per scene into src/stills/
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for i, (fn, dur) in enumerate(SCENES):
            for tt in (dur * 0.35, dur - 0.5):
                frame_at(i, tt).save(os.path.join(HERE, "stills", f"s{i}_{tt:.1f}.png"))
        return
    poster().save(os.path.join(OUT, "poster.png"), optimize=True)
    out = os.path.join(OUT, "shotfleet-product.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-profile:v", "high", "-level", "4.0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-movflags", "+faststart", "-an", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0
    for i, (fn, dur) in enumerate(SCENES):
        for f in range(round(dur * FPS)):
            pr.stdin.write(frame_at(i, f / FPS).tobytes()); n += 1
    pr.stdin.close(); pr.wait()
    print(f"{n} frames, {n / FPS:.1f} s -> {out}")

if __name__ == "__main__": main()
