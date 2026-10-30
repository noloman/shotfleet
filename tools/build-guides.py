#!/usr/bin/env python3
"""Render the drafted articles (marketing/articles/NN-*.md) into guide pages. Stdlib only.

  python3 tools/build-guides.py                    draft pages and a hub in site/draft/guides/ (never served)
  python3 tools/build-guides.py --publish          also copy the VERIFIED articles into site/public/guides/, write the hub
                                                   (site/public/guides.html), add them all to site/public/sitemap.xml and write the Atom feed
  python3 tools/build-guides.py --publish-unverified   the same, for every article, ticked or not (your decision)
  python3 tools/build-guides.py --feed             only rewrite the Atom feed (site/public/guides/feed.xml) from the guides already published

An article is verified when its 'TO VERIFY BEFORE PUBLISHING' list has no item left unticked: an item counts as ticked
when its last TICKED is not a PARTLY TICKED (an item can record a partial run, then the full one). A list with no items counts as unverified.

Routing, checked with `wrangler dev` (cd site) on 2026-10-06: /guides/<slug> serves guides/<slug>.html with a 200 and
/guides serves guides.html; a guides/index.html would answer /guides with a redirect to /guides/, so the hub is not one.
"""
import argparse, html, json, re, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://shotfleet.com"
AUTHOR = "Manuel Lorenzo Parejo"
PLACEHOLDER = "BUILD_DATE"  # drafts carry this; --publish writes the day it ran

FEED_LINK = '\n<link rel="alternate" type="application/atom+xml" title="shotfleet guides" href="/guides/feed.xml">'

NAV = '''<header class="top">
  <nav class="pill" aria-label="Main">
    <a class="brand" href="/"><svg viewBox="46 46 420 420" aria-hidden="true"><defs><mask id="sf-check"><rect x="40" y="40" width="432" height="432" fill="#fff"/><path d="M208 248l40 40 68-74" fill="none" stroke="#000" stroke-width="46" stroke-linecap="round" stroke-linejoin="round"/></mask></defs><rect x="160" y="86" width="192" height="312" rx="38" fill="currentColor" transform="rotate(-16 256 456)" opacity="0.45"/><rect x="160" y="86" width="192" height="312" rx="38" fill="currentColor" transform="rotate(16 256 456)" opacity="0.45"/><g mask="url(#sf-check)"><rect x="160" y="86" width="192" height="312" rx="38" fill="currentColor"/></g></svg>shotfleet</a>
    <span class="links"><a href="/#run">How it works</a><a href="/examples">Examples</a><a href="/docs">Docs</a><a href="/#price">Pricing</a><a href="/whats-new">What’s new</a></span>
  </nav>
</header>'''
FOOTER = '''<footer>
  <div class="wrap">
    <span>shotfleet · by <a href="https://manulorenzo.me">Manuel Lorenzo Parejo</a></span>
    <span><a href="/">Home</a> · <a href="/docs">Docs</a> · <a href="/whats-new">What’s new</a> · <a href="/guides">Guides</a> · <a href="/alternatives">Alternatives</a> · <a href="/terms">Licence and refunds</a> · <a href="/privacy">Privacy</a></span>
  </div>
</footer>'''


# ---------- the Markdown subset: headings, paragraphs, lists, code fences, inline code, links, images, emphasis, tables ----------

def inline(text):
    """Escape, then code spans, images, links, **strong** and *emphasis*. Only http(s), /, # and mailto links are made."""
    spans = []
    def stash(m):
        spans.append(f"<code>{html.escape(m.group(1), quote=False)}</code>"); return f"\0{len(spans) - 1}\0"
    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    safe = lambda u: re.match(r"(https?://|/|#|mailto:)", u)
    def attr(u): return html.escape(html.unescape(u), quote=True)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", lambda m: f'<img src="{attr(m.group(2).replace(SITE + "/", "/"))}" alt="{attr(m.group(1))}" loading="lazy">' if safe(m.group(2)) else m.group(0), text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{attr(m.group(2))}">{m.group(1)}</a>' if safe(m.group(2)) else m.group(0), text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    return re.sub(r"\0(\d+)\0", lambda m: spans[int(m.group(1))], text)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render_markdown(md):
    lines, out, i = md.splitlines(), [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip(): i += 1; continue
        fence = re.match(r"```(\w*)\s*$", line)
        if fence:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"): j += 1
            lang = f' class="language-{fence.group(1)}"' if fence.group(1) else ""
            out.append(f"<pre><code{lang}>{html.escape(chr(10).join(lines[i + 1:j]), quote=False)}</code></pre>"); i = j + 1; continue
        h = re.match(r"(#{1,6})\s+(.*)$", line)
        if h: out.append(f"<h{len(h.group(1))}>{inline(h.group(2))}</h{len(h.group(1))}>"); i += 1; continue
        if re.fullmatch(r"-{3,}", line.strip()): out.append("<hr>"); i += 1; continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.fullmatch(r"\s*\|?[\s:|-]+\|[\s:|-]*", lines[i + 1]):
            head, j = cells(line), i + 2
            rows = []
            while j < len(lines) and lines[j].lstrip().startswith("|"): rows.append(cells(lines[j])); j += 1
            out.append('<div class="tablewrap" tabindex="0" role="region" aria-label="Table"><table><thead><tr>' + "".join(f'<th scope="col">{inline(c)}</th>' for c in head)
                       + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")
            i = j; continue
        li = re.match(r"([-*]|\d+\.)\s+(.*)$", line)
        if li:
            tag, items = ("ol" if li.group(1)[0].isdigit() else "ul"), []
            while i < len(lines):
                m = re.match(r"([-*]|\d+\.)\s+(.*)$", lines[i])
                if m: items.append(m.group(2)); i += 1
                elif lines[i].startswith((" ", "\t")) and lines[i].strip() and items: items[-1] += " " + lines[i].strip(); i += 1  # continuation line
                else: break
            out.append(f"<{tag}>" + "".join(f"<li>{inline(t)}</li>" for t in items) + f"</{tag}>"); continue
        j = i
        while j < len(lines) and lines[j].strip() and not re.match(r"(```|#{1,6}\s|([-*]|\d+\.)\s|-{3,}\s*$)", lines[j]): j += 1
        out.append(f"<p>{inline(' '.join(l.strip() for l in lines[i:j]))}</p>"); i = max(j, i + 1)
    return "\n".join(out)


# ---------- the articles ----------

def parse_article(path):
    """{slug, title, description, body, open_items} from one marketing/articles file, or None when it has no Slug row (an ideas file)."""
    text = path.read_text()
    field = lambda name: (m.group(1).strip() if (m := re.search(rf"^\|\s*{name}[^|]*\|\s*(.*?)\s*\|\s*$", text, re.M)) else None)
    slug = (field("Slug") or "").strip("`/ ")
    if not slug: return None
    head, _, body = text.partition("\n---\n")
    return {"slug": slug, "title": field("Title") or "", "title_tag": field("Title tag"), "description": field("Meta description") or "", "body": body.strip(), "open_items": open_items(head), "file": path.name}


def open_items(text):
    """Unticked items of the 'TO VERIFY' section. A section without any item counts as one open item (nothing was checked)."""
    m = re.search(r"^#*\s*TO VERIFY.*$", text, re.M)
    if not m: return []
    section = re.split(r"^(?:---|Sources\b.*)$", text[m.end():], maxsplit=1, flags=re.M)[0]
    items = re.findall(r"^(?:\d+\.|[-*])\s+(.*)$", section, re.M)
    if not items: return ["(the TO VERIFY section lists nothing)"]
    ticked = lambda t: (marks := re.findall(r"(PARTLY )?TICKED", t)) and not marks[-1]  # the last mark counts
    return [t for t in items if not (re.match(r"\[[xX]\]", t) or ticked(t))]


def page(title, description, path, body, og_type="website", ld=None, assets="/"):
    blocks = ld if isinstance(ld, list) else [ld] if ld else []  # no "</script>" inside a tag
    ld_tag = "".join(f'\n<script type="application/ld+json">\n{json.dumps(b, indent=2, ensure_ascii=False).replace("</", "<\\/")}\n</script>' for b in blocks)
    e = lambda s: html.escape(s, quote=True)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f4f6f8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0a121c" media="(prefers-color-scheme: dark)">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{SITE}/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The same app screen in Japanese, Arabic and Korean, each with a language pennant">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="shotfleet">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE}{path}">
<link rel="icon" href="{assets}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{assets}favicon.ico" sizes="48x48">
<link rel="apple-touch-icon" href="{assets}apple-touch-icon.png">
<link rel="preload" href="{assets}fonts/geist-mono-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{assets}site.css">{FEED_LINK if path.startswith("/guides") else ""}{ld_tag}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{NAV}
<main class="wrap" id="main">
 <div class="page docs">
  <p class="label">Guide</p>
{body}
 </div>
</main>
{FOOTER}
</body>
</html>
'''


def article_page(a, built, assets="/"):
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["description"], "author": {"@type": "Person", "name": AUTHOR},
          "datePublished": built, "mainEntityOfPage": f"{SITE}/guides/{a['slug']}"}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": n, "name": name, "item": f"{SITE}{url}"}
        for n, (name, url) in enumerate([("Home", "/"), ("Guides", "/guides"), (a["title"], f"/guides/{a['slug']}")], 1)]}
    # the title tag can be shorter than the h1 (a "Title tag" row in the article's table); search results cut titles at about 60 characters
    return page(a["title_tag"] or a["title"], a["description"], f"/guides/{a['slug']}", render_markdown(a["body"]), "article", [ld, crumbs], assets)


def hub_page(arts, drafts, assets="/"):
    items = "".join(f'<li><a href="/guides/{a["slug"]}">{html.escape(a["title"])}</a><br><span class="small">{html.escape(a["description"])}'
                    + (f' [draft: {len(a["open_items"])} item(s) still to verify]' if drafts and a["open_items"] else "") + "</span></li>" for a in arts)
    body = f'<h1>Guides</h1>\n<p class="lede">How-tos for localized App Store and Google Play screenshots.</p>\n<ul>{items}</ul>'
    return page("shotfleet guides: localized screenshots", "Guides on localized App Store and Google Play screenshots: fastlane snapshot, Maestro locales and what a check finds.", "/guides", body, assets=assets)


def add_to_sitemap(root, paths, built):
    p = root / "site/public/sitemap.xml"
    text = p.read_text()
    for path in paths:
        loc = f"  <url><loc>{SITE}{path}</loc><lastmod>{built}</lastmod></url>\n"  # tests/test_site_audit wants a lastmod on every entry
        if f"<loc>{SITE}{path}</loc>" not in text: text = text.replace("</urlset>", loc + "</urlset>")
    p.write_text(text)


def feed_xml(entries):
    """An Atom feed (title, link, date, summary per guide) from [(slug, title, description, 'YYYY-MM-DD')], newest first."""
    e = html.escape
    entries = sorted(entries, key=lambda x: x[3], reverse=True)
    items = "".join(f"""  <entry>
    <title>{e(t)}</title>
    <link href="{SITE}/guides/{slug}"/>
    <id>{SITE}/guides/{slug}</id>
    <updated>{d}T00:00:00Z</updated>
    <summary>{e(desc)}</summary>
  </entry>
""" for slug, t, desc, d in entries)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>shotfleet guides</title>
  <link href="{SITE}/guides/feed.xml" rel="self" type="application/atom+xml"/>
  <link href="{SITE}/guides"/>
  <id>{SITE}/guides</id>
  <updated>{entries[0][3] if entries else "1970-01-01"}T00:00:00Z</updated>
  <author><name>{e(AUTHOR)}</name></author>
{items}</feed>
"""


def write_feed(root, arts, built):
    """site/public/guides/feed.xml for the articles that are published (a page exists in site/public/guides/), dated by their own datePublished."""
    pub, entries = root / "site/public/guides", []
    for a in arts:
        f = pub / f"{a['slug']}.html"
        if f.is_file():
            m = re.search(r'"datePublished": "(\d{4}-\d\d-\d\d)"', f.read_text())
            entries.append((a["slug"], a["title"], a["description"], m.group(1) if m else built))
    if entries: (pub / "feed.xml").write_text(feed_xml(entries))


def build(root=ROOT, publish=False, unverified=False, today=None, out=sys.stdout, err=sys.stderr, feed_only=False):
    """Write drafts; with publish, copy the verified articles to site/public/guides/. Returns an exit code (1 when an article was refused)."""
    arts = [a for p in sorted((root / "marketing/articles").glob("[0-9][0-9]-*.md")) if (a := parse_article(p))]
    draft = root / "site/draft/guides"; draft.mkdir(parents=True, exist_ok=True)
    for a in arts: (draft / f"{a['slug']}.html").write_text(article_page(a, PLACEHOLDER, "../../public/"))
    (draft / "index.html").write_text(hub_page(arts, True, "../../public/"))
    print(f"drafts: {len(arts)} article(s) and the hub in {draft.relative_to(root)}", file=out)
    if feed_only: write_feed(root, arts, (today or date.today()).isoformat()); return 0
    if not publish: return 0
    ok, refused = [], []
    for a in arts:
        long = len(a["description"]) > 160  # search results cut it; not a verification item, so --publish-unverified does not skip it
        if long: print(f"refused {a['slug']}: the meta description is {len(a['description'])} characters (max 160); shorten it in {a['file']}", file=err)
        elif a["open_items"] and not unverified: print(f"refused {a['slug']}: {len(a['open_items'])} item(s) of TO VERIFY BEFORE PUBLISHING unticked (first: {a['open_items'][0][:80]}...). Tick them in {a['file']}, or use --publish-unverified", file=err)
        (refused if long or (a["open_items"] and not unverified) else ok).append(a)
    if ok:
        pub = root / "site/public/guides"; pub.mkdir(parents=True, exist_ok=True)
        built = (today or date.today()).isoformat()
        for a in ok: (pub / f"{a['slug']}.html").write_text(article_page(a, built)); print(f"published {a['slug']}", file=out)
        (root / "site/public/guides.html").write_text(hub_page(ok, False))  # not guides/index.html: the worker would redirect /guides to /guides/
        add_to_sitemap(root, ["/guides", *(f"/guides/{a['slug']}" for a in ok)], built)
        write_feed(root, arts, built)
    return 1 if refused else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--publish", action="store_true", help="copy the verified articles into site/public/guides/ and add them to sitemap.xml")
    ap.add_argument("--publish-unverified", action="store_true", help="publish every article, including ones with unticked TO VERIFY items")
    ap.add_argument("--feed", action="store_true", help="only rewrite site/public/guides/feed.xml from the guides that are already published")
    a = ap.parse_args(argv)
    return build(publish=a.publish or a.publish_unverified, unverified=a.publish_unverified, feed_only=a.feed)


if __name__ == "__main__":
    sys.exit(main())
