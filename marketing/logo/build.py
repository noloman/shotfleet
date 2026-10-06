"""Builds the shotfleet mark and every file that carries it.

The mark: three phones fanned like a hand of cards, the front one yellow with a check.
One flow, many devices, every screenshot checked. Colours are the site.css tokens.

  python3 marketing/logo/build.py      (needs rsvg-convert and magick)

Writes:
  marketing/logo/shotfleet-icon.svg          master app icon (gradient, soft shadows)
  marketing/logo/shotfleet-glyph.svg         one-colour glyph (currentColor), for the site header
  site/public/favicon.svg                    flat icon, no filters, crisp at 16-32 px
  site/public/favicon.ico                    48 x 48, PNG inside ICO
  site/public/apple-touch-icon.png           180 x 180, full-bleed square, no alpha (iOS rounds it)
  marketing/gumroad/images/icon.svg, icon-1024/512/64.png
"""
import pathlib, subprocess, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PUB = ROOT / "site/public"
GUM = ROOT / "marketing/gumroad/images"
INK, YEL, YEL_TOP, BLUE, BLUE_L = "#0b1220", "#f5c400", "#ffd43a", "#1b3fd1", "#5b7cff"
PIVOT = "256 456"  # the cards fan out around a point below the tile


def cards(back_l, back_r, front, check, shadow="", check_w=34):
    def card(rot, fill, extra=""):
        r = f' transform="rotate({rot} {PIVOT})"' if rot else ""
        return f'<rect x="160" y="86" width="192" height="312" rx="38" fill="{fill}"{r}{extra}/>'
    return (card(-16, back_l) + card(16, back_r, shadow) + card(0, front, shadow)
            + f'<path d="M208 248l40 40 68-74" fill="none" stroke="{check}" stroke-width="{check_w}" stroke-linecap="round" stroke-linejoin="round"/>')


def icon(rich=True, rx=114):
    if rich:
        defs = ('<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a2540"/><stop offset="1" stop-color="#0b1220"/></linearGradient>'
                f'<linearGradient id="y" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{YEL_TOP}"/><stop offset="1" stop-color="{YEL}"/></linearGradient>'
                '<filter id="sh" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="-10" dy="10" stdDeviation="12" flood-color="#050a14" flood-opacity="0.55"/></filter></defs>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">{defs}'
                f'<rect width="512" height="512" rx="{rx}" fill="url(#bg)"/>'
                f'<g id="icon">{cards(BLUE, BLUE_L, "url(#y)", INK, " filter=" + chr(34) + "url(#sh)" + chr(34))}</g></svg>\n')
    # Flat: a thin ink gap stands in for the shadow so the cards stay apart at 16 px.
    gap = f' stroke="{INK}" stroke-width="14"'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="{rx}" fill="{INK}"/>'
            f'<g id="icon">{cards(BLUE, BLUE_L, YEL, INK, gap, check_w=40)}</g></svg>\n')


def glyph():
    """One colour: back cards at 45%, front card solid with the check cut out. Square viewBox around the fan."""
    m = ('<mask id="sf-check"><rect x="40" y="40" width="432" height="432" fill="#fff"/>'
         '<path d="M208 248l40 40 68-74" fill="none" stroke="#000" stroke-width="46" stroke-linecap="round" stroke-linejoin="round"/></mask>')
    c = lambda rot, op: (f'<rect x="160" y="86" width="192" height="312" rx="38" fill="currentColor"'
                         + (f' transform="rotate({rot} {PIVOT})"' if rot else "") + (f' opacity="{op}"' if op else "") + "/>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="46 46 420 420"><defs>{m}</defs>'
            f'{c(-16, .45)}{c(16, .45)}<g mask="url(#sf-check)">{c(0, None)}</g></svg>\n')


def png(svg_text, px, out, flatten=False):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg_text)
    subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px), "-o", str(out), f.name], check=True)
    if flatten:
        subprocess.run(["magick", str(out), "-background", INK, "-alpha", "remove", "-alpha", "off", "-define", "png:color-type=2", str(out)], check=True)


if __name__ == "__main__":
    (HERE / "shotfleet-icon.svg").write_text(icon())
    (HERE / "shotfleet-glyph.svg").write_text(glyph())
    (PUB / "favicon.svg").write_text(icon(rich=False))
    png(icon(rich=False), 48, HERE / "favicon-48.png")
    data = (HERE / "favicon-48.png").read_bytes()
    (HERE / "favicon-48.png").unlink()
    # ICO header, one directory entry (48 x 48, 32 bpp), then the PNG itself.
    entry = bytes([48, 48, 0, 0]) + (1).to_bytes(2, "little") + (32).to_bytes(2, "little") + len(data).to_bytes(4, "little") + (22).to_bytes(4, "little")
    (PUB / "favicon.ico").write_bytes(b"\x00\x00\x01\x00\x01\x00" + entry + data)
    png(icon(rx=0), 180, PUB / "apple-touch-icon.png", flatten=True)
    (GUM / "icon.svg").write_text(icon())
    for px in (1024, 512, 64):
        png(icon() if px > 64 else icon(rich=False), px, GUM / f"icon-{px}.png")
    print("ok")
