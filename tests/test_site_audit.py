"""Regression tests for the site critique (research/site-critique-2.md) and the SEO audit (research/seo-audit.md).
Static checks on site/public: contrast ratios computed from the CSS tokens, tap-target and font sizes in the CSS, table semantics,
landmarks, heading order, language tags, JSON-LD, meta lengths, robots and sitemap, favicons, forms without JavaScript, the CSP,
and the waitlist/sale markers on the pages go-live.sh rewrites. Stdlib only, no browser, no network.
"""
import json, re, subprocess, sys, tempfile, unittest
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "site/public"
CSS = (PUB / "site.css").read_text()
PAGES = {p.name: p.read_text() for p in sorted(PUB.glob("*.html"))}
LIVE = "<!-- WAITLIST -->" not in PAGES["index.html"]  # go-live.sh already ran: the waitlist copy is gone on purpose
CHECKOUT = "https://example.gumroad.com/l/shotfleet"


# ---------------------------------------------------------------- helpers
def visible(html):
    """The page as a visitor sees it: comments (the WAITLIST and SALE blocks) are dropped by the HTML parser, scripts and styles removed."""
    return html


def strip_comments(html):
    return re.sub(r"<!--.*?-->", "", html, flags=re.S)


class Tree(HTMLParser):
    """Flat list of elements (tag, attrs, text-after-open) plus a few derived facts."""
    VOID = {"meta", "link", "img", "input", "br", "hr", "source"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.els, self.stack, self.headings, self.text_of = [], [], [], []
        self.feed(strip_comments(html))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        e = {"tag": tag, "a": a, "parents": [s["tag"] for s in self.stack], "chain": list(self.stack), "text": []}
        self.els.append(e)
        if tag == "h1" or tag in ("h2", "h3", "h4", "h5", "h6"): self.headings.append(e)
        if tag not in self.VOID: self.stack.append(e)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        for s in self.stack: s["text"].append(data)

    def find(self, tag, **attrs):
        return [e for e in self.els if e["tag"] == tag and all(e["a"].get(k) == v for k, v in attrs.items())]

    def txt(self, e):
        return re.sub(r"\s+", " ", "".join(e["text"])).strip()


TREES = {n: Tree(h) for n, h in PAGES.items()}


def rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lum(h):
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def tokens(block):
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{3,6})\s*;", block))


def theme_tokens():
    light_block = re.search(r":root \{(.*?)\n\}", CSS, flags=re.S).group(1)
    media = re.search(r"@media \(prefers-color-scheme: dark\) \{\s*:root:not\(\[data-theme=\"light\"\]\) \{(.*?)\n  \}", CSS, flags=re.S).group(1)
    forced = re.search(r":root\[data-theme=\"dark\"\] \{(.*?)\n\}", CSS, flags=re.S).group(1)
    light = tokens(light_block)
    dark = {**light, **tokens(media)}
    return light, dark, {**light, **tokens(forced)}


def rem(v):
    return float(v[:-3]) if v.endswith("rem") else float(v[:-2]) / 16 if v.endswith("px") else float(v[:-2]) if v.endswith("em") else None


# ---------------------------------------------------------------- contrast (critique P1-1 and the dark-theme pennant)
class Contrast(unittest.TestCase):
    TEXT_PAIRS = [("ink", "paper"), ("ink", "surface"), ("muted", "paper"), ("muted", "surface"), ("blue", "paper"), ("blue", "surface"),
                  ("on-blue", "blue"), ("on-blue", "blue-hover"), ("on-red", "red"), ("paper", "ink"), ("red", "paper"), ("red", "surface"),
                  ("pass", "pass-bg"), ("pass", "surface"), ("ink", "pass-bg"), ("terminal-text", "terminal"), ("terminal-dim", "terminal")]
    GRAPHIC_PAIRS = [("on-pass", "pass"), ("field", "surface"), ("field", "paper"), ("blue", "paper")]  # check mark, field border, focus ring: 3:1

    def test_the_dark_theme_is_defined_twice_and_identically(self):
        light, dark, forced = theme_tokens()
        self.assertEqual(dark, forced, "the prefers-color-scheme block and :root[data-theme=dark] must hold the same tokens")

    def test_text_pairs_reach_4_5_in_light_and_dark(self):
        light, dark, _ = theme_tokens()
        for name, t in (("light", light), ("dark", dark)):
            for fg, bg in self.TEXT_PAIRS:
                with self.subTest(theme=name, fg=fg, bg=bg):
                    self.assertGreaterEqual(ratio(t[fg], t[bg]), 4.5, f"--{fg} on --{bg} in {name}: {ratio(t[fg], t[bg]):.2f}")

    def test_graphics_reach_3_in_light_and_dark(self):
        light, dark, _ = theme_tokens()
        for name, t in (("light", light), ("dark", dark)):
            for fg, bg in self.GRAPHIC_PAIRS:
                with self.subTest(theme=name, fg=fg, bg=bg):
                    self.assertGreaterEqual(ratio(t[fg], t[bg]), 3.0, f"--{fg} on --{bg} in {name}: {ratio(t[fg], t[bg]):.2f}")

    def test_no_card_takes_its_background_from_the_ink_token(self):
        """P1-1: --ink turns near-white in dark, so a card that uses it as a background inverts and its fixed yellow text vanishes."""
        for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", CSS):
            sel, body = m.group(1).strip(), m.group(2)
            if re.search(r"background:\s*var\(--ink\)", body) and "::before" not in sel:  # a bullet square has no text
                # allowed only where the text colour is the paired --paper token (flags, selected tabs, the skip link)
                self.assertRegex(body, r"color:\s*var\(--paper\)", f"{sel} paints --ink behind text that is not --paper")


# ---------------------------------------------------------------- sizes (critique P1-6)
class Targets(unittest.TestCase):
    def rule(self, selector):
        for m in re.finditer(r"(?<![\w.-])" + re.escape(selector) + r"\s*\{([^{}]*)\}", CSS):
            yield m.group(1)

    def test_buttons_links_and_controls_have_a_44px_target(self):
        for sel in (".brand", ".pill .links a", ".pill .btn.sm", ".tabs button", ".flowbtn", ".consent-btn", "footer a", ".zoom-close", ".btn", "input[type=email], select, textarea"):
            with self.subTest(selector=sel):
                heights = [int(h) for body in self.rule(sel) for h in re.findall(r"min-height:\s*(\d+)px", body)]
                self.assertTrue(heights and max(heights) >= 44, f"{sel} has min-height {heights}")

    def test_small_button_is_not_shrunk_back_below_44(self):
        self.assertRegex(CSS, r"\n\.btn\.sm \{ min-height: 44px;")

    def test_footer_and_toc_links_are_block_level_targets(self):
        self.assertRegex(CSS, r"footer a \{[^}]*display: inline-flex")
        self.assertRegex(CSS, r"\.docs \.toc a \{[^}]*min-height: 44px")

    def test_text_is_at_least_14px_unless_it_is_an_uppercase_label(self):
        small = []
        for m in re.finditer(r"([^{}@]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)):
            sel, body = m.group(1).strip(), m.group(2)
            if "@font-face" in sel or "text-transform: uppercase" in body: continue
            size = re.search(r"(?:^|;|\s)font-size:\s*([\d.]+(?:rem|px))", body)
            short = re.search(r"font:\s*(?:[\d]+\s+)?([\d.]+(?:rem|px))", body)
            for v in filter(None, [size and size.group(1), short and short.group(1)]):
                if rem(v) is not None and rem(v) < 0.875 and sel not in ("footer .wrap",):
                    small.append((sel, v))
        self.assertEqual(small, [], "readable text under 14px")

    def test_text_that_carries_meaning_is_not_tiny(self):
        for sel in (".small {", ".ship figcaption {", "footer .wrap {", ".note {"):
            m = re.search(re.escape(sel) + r"[^}]*?([\d.]+)rem", CSS)
            self.assertTrue(m and float(m.group(1)) >= 0.875, sel)


# ---------------------------------------------------------------- tables (critique P1-5)
class Tables(unittest.TestCase):
    def test_every_table_has_a_caption_column_headers_row_headers_and_a_focusable_scroll_region(self):
        count = 0
        for name, t in TREES.items():
            for table in t.find("table"):
                count += 1
                children = [e for e in t.els if table in e["chain"] or e is table]
                self.assertTrue([e for e in children if e["tag"] == "caption"], f"{name}: table without a caption")
                ths = [e for e in children if e["tag"] == "th"]
                self.assertTrue(ths, name)
                for th in ths: self.assertIn(th["a"].get("scope"), ("col", "row"), f"{name}: <th> {t.txt(th)!r} has no scope")
                wrap = [p for p in table["chain"] if "tablewrap" in (p["a"].get("class") or "")]
                self.assertTrue(wrap, f"{name}: a table outside .tablewrap cannot scroll on a phone")
                self.assertEqual(wrap[-1]["a"].get("tabindex"), "0", f"{name}: the scroll region is not keyboard reachable")
                self.assertEqual(wrap[-1]["a"].get("role"), "region")
                self.assertTrue(wrap[-1]["a"].get("aria-label") or wrap[-1]["a"].get("aria-labelledby"))
        self.assertGreaterEqual(count, 2)

    def test_the_comparison_table_shows_that_it_scrolls_and_keeps_its_first_column(self):
        self.assertIn("no-repeat local", CSS)  # scroll shadows
        self.assertIn("no-repeat scroll", CSS)
        self.assertRegex(CSS, r"\.tablewrap th:first-child \{[^}]*position: sticky")


# ---------------------------------------------------------------- structure
class Landmarks(unittest.TestCase):
    def test_every_page_has_skip_link_header_nav_main_and_footer(self):
        for name, t in TREES.items():
            with self.subTest(page=name):
                self.assertTrue(t.find("main", id="main"), "main#main")
                self.assertTrue(t.find("header"), "header")
                self.assertTrue([e for e in t.find("nav") if e["a"].get("aria-label")], "labelled nav")
                self.assertTrue(t.find("footer"), "footer")
                skip = [e for e in t.find("a") if "skip" in (e["a"].get("class") or "")]
                self.assertEqual([e["a"]["href"] for e in skip], ["#main"])

    def test_the_brand_link_is_a_real_link_in_a_pill_on_every_page(self):
        """P0-1: on the text pages the brand sat in a pointer-events:none header and could not be clicked."""
        self.assertNotRegex(CSS, r"pointer-events:\s*none")
        for name, t in TREES.items():
            brand = [e for e in t.find("a") if (e["a"].get("class") or "") == "brand"]
            self.assertEqual(len(brand), 1, name)
            self.assertEqual(brand[0]["a"]["href"], "/", name)
            self.assertIn("nav", brand[0]["parents"], name)
        self.assertNotRegex(CSS, r"\.top\s*\{[^}]*position:\s*(sticky|fixed)")

    def test_terms_can_get_home_and_to_privacy_from_its_footer(self):
        hrefs = [e["a"].get("href") for e in TREES["terms.html"].find("a")]
        for h in ("/", "/privacy", "/alternatives", "/docs"): self.assertIn(h, hrefs)

    def test_heading_levels_never_skip_a_level_and_start_at_h1(self):
        for name, t in TREES.items():
            levels = [int(h["tag"][1]) for h in t.headings]
            with self.subTest(page=name):
                self.assertEqual(levels[0], 1)
                for prev, cur in zip(levels, levels[1:]): self.assertLessEqual(cur, prev + 1, f"{name}: h{prev} jumps to h{cur}")

    def test_ids_are_unique_on_every_page(self):
        for name, t in TREES.items():
            ids = [e["a"]["id"] for e in t.els if "id" in e["a"]]
            self.assertEqual(sorted(i for i in ids if ids.count(i) > 1), [], name)

    def test_non_latin_text_carries_a_lang(self):
        """P2-3: language names in their own script are read with the page's English voice unless they say otherwise."""
        non_latin = re.compile(r"[Ѐ-ӿ֐-ۿ぀-ヿ㐀-鿿가-힯]")
        for name, t in TREES.items():
            for e in t.els:
                own = re.sub(r"\s+", " ", "".join(e["text"]))
                if e["tag"] in ("figcaption", "span", "a", "p", "li", "td") and non_latin.search(own):
                    langs = [x["a"].get("lang") for x in [*e["chain"], e] if x["a"].get("lang")]
                    # code samples in docs (examples with non-Latin keys) sit in pre/code and are data
                    if "pre" in e["parents"] or "code" in e["parents"] or "html" == e["tag"]: continue
                    self.assertTrue(langs, f"{name}: <{e['tag']}> {own[:30]!r} has no lang")

    def test_every_image_has_alt_and_dimensions(self):
        for name, t in TREES.items():
            for img in t.find("img"):
                self.assertIn("alt", img["a"], f"{name}: {img['a'].get('src')}")
                if "dialog" not in img["parents"]:
                    self.assertTrue(img["a"].get("width") and img["a"].get("height"), f"{name}: {img['a'].get('src')} has no width/height")

    def test_forms_have_labels_and_a_working_no_javascript_fallback(self):
        """P2-5: without the script a submit must not become GET /?email=... (the address would land in the URL and the logs)."""
        for name, t in TREES.items():
            labels = {e["a"].get("for") for e in t.find("label")}
            for form in t.find("form"):
                if form["a"].get("method") == "dialog" or "hidden" in form["a"] or any("hidden" in p["a"] for p in form["chain"]): continue
                if "followup" in (form["a"].get("class") or ""): continue  # lives in a box that is hidden until the script has saved the address
                with self.subTest(page=name, form=form["a"].get("id")):
                    self.assertEqual(form["a"].get("method"), "post")
                    self.assertTrue(form["a"].get("action", "").startswith("/api/"))
            for inp in t.find("input") + t.find("textarea") + t.find("select"):
                if inp["a"].get("type") in ("hidden", "submit") or "trap" in (inp["a"].get("class") or ""): continue
                self.assertIn(inp["a"].get("id"), labels, f"{name}: field {inp['a'].get('name')} has no <label for>")

    def test_form_errors_are_announced_and_wired_to_the_field(self):
        for name, t in TREES.items():
            for p in t.find("p"):
                if "form-error" in (p["a"].get("class") or ""):
                    self.assertEqual(p["a"].get("role"), "alert", name)
                    self.assertTrue(p["a"].get("id"), f"{name}: the error paragraph needs an id for aria-describedby")
        js = (PUB / "forms.js").read_text()
        self.assertIn('setAttribute("aria-describedby", err.id)', js)
        self.assertIn('removeAttribute("aria-describedby")', js)


# ---------------------------------------------------------------- copy that must stay honest and findable (P0-2, P1-2, P1-8, SEO fix 3)
class FirstScreen(unittest.TestCase):
    @unittest.skipIf(LIVE, "waitlist copy is gone after go-live")
    def test_the_first_screen_says_not_released_the_price_the_platform_and_the_stores(self):
        hero = strip_comments(PAGES["index.html"])
        hero = hero[hero.index('class="wrap hero"'):hero.index('class="fleet"')]
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", hero))
        for must in ("Not released yet", "$29", "$49", "first 100 buyers", "Apple silicon", "App Store", "Google Play", "Maestro", "Join the waitlist"):
            self.assertIn(must, text)

    def test_maestro_is_explained_with_a_link_on_first_use(self):
        self.assertRegex(PAGES["index.html"], r'<a href="https://maestro\.mobile\.dev">Maestro</a>, the UI-flow tool')

    def test_the_flutter_and_react_native_caveat_is_under_the_hero_strip_not_only_in_the_price_section(self):
        note = re.search(r'<p class="small fleet-note[^>]*>(.*?)</p>', PAGES["index.html"], flags=re.S).group(1)
        self.assertIn("not yet on other Flutter or React Native apps", note)
        self.assertIn("Apple silicon", note)

    def test_the_caveat_stays_in_the_price_section_and_on_the_comparison_page(self):
        self.assertIn("other apps and bare React Native not yet run", PAGES["index.html"])
        self.assertIn("not on other apps or on bare React Native", PAGES["alternatives.html"])
        self.assertIn("Apple silicon", PAGES["alternatives.html"])

    def test_the_gallery_heading_does_not_read_as_proof_of_the_tool(self):
        self.assertNotIn("The same screen, in the languages of my other apps", PAGES["index.html"])
        self.assertIn("not shotfleet output", PAGES["index.html"])
        self.assertIn("not what shotfleet can do", PAGES["index.html"])

    def test_joining_the_list_is_said_not_to_reserve_the_price(self):
        if not LIVE: self.assertIn("joining the list does not reserve the launch price", PAGES["index.html"])

    def test_the_number_strip_says_what_was_counted(self):
        self.assertIn("<dt>108 of 120</dt>", PAGES["index.html"])
        self.assertNotIn("108 problems", PAGES["index.html"])

    def test_the_story_says_the_run_could_not_tap_next(self):
        self.assertIn("so the run could not tap it", PAGES["index.html"])

    def test_no_time_bound_dig_on_the_comparison_page(self):
        self.assertNotIn("no stars when I looked", PAGES["alternatives.html"])


# ---------------------------------------------------------------- the pages go-live.sh rewrites
def go_live_text(name, html):
    script = (ROOT / "packaging/go-live.sh").read_text()
    code = re.search(r"<<'PY'\n(.*?)\nPY\n", script, flags=re.S).group(1)
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "site/public").mkdir(parents=True)
        for n in ("index.html", "alternatives.html", "terms.html"): (Path(d) / "site/public" / n).write_text(PAGES[n])
        subprocess.run([sys.executable, "-", CHECKOUT], input=code, text=True, cwd=d, check=True)
        return (Path(d) / "site/public" / name).read_text()


@unittest.skipIf(LIVE, "the site is already live")
class GoLivePages(unittest.TestCase):
    def test_comparison_and_terms_drop_every_waitlist_sentence_at_go_live(self):
        for name in ("alternatives.html", "terms.html"):
            raw = PAGES[name]
            self.assertEqual(raw.count("    <!-- WAITLIST -->\n"), raw.count("<!-- /WAITLIST -->"), name)
            self.assertIn("not on sale yet", raw, f"{name} must say it before launch")
            live = go_live_text(name, raw)
            for gone in ("WAITLIST", "SALE", "@CHECKOUT@", "not on sale yet", "waitlist", "join the list"):
                self.assertNotIn(gone, live, f"{name} still says {gone!r} after go-live")

    def test_the_comparison_page_gets_a_buy_link_at_go_live(self):
        live = go_live_text("alternatives.html", PAGES["alternatives.html"])
        self.assertGreaterEqual(live.count(f'href="{CHECKOUT}"'), 2)
        self.assertIn("Buy shotfleet", live)

    def test_the_comparison_page_has_a_way_to_join_before_launch_both_in_the_middle_and_at_the_end(self):
        t = strip_comments(PAGES["alternatives.html"])  # comments are stripped; the markers are comments, so look at the raw text
        raw = PAGES["alternatives.html"]
        self.assertEqual(raw.count('class="cta-row"'), 4)  # two waitlist, two sale
        self.assertLess(raw.index('class="cta-row"'), raw.index("<h2>What each tool does</h2>"))
        self.assertGreater(raw.rindex('class="cta-row"'), raw.index("<h2>The story</h2>"))
        self.assertIn('href="/#price"', t)

    def test_go_live_script_adds_all_three_pages_to_its_commit_and_checks_them(self):
        script = (ROOT / "packaging/go-live.sh").read_text()
        self.assertEqual(script.count("site/public/index.html site/public/alternatives.html site/public/terms.html"), 2)
        self.assertIn("still has waitlist copy or markers", script)


# ---------------------------------------------------------------- structured data, metadata, robots, sitemap (seo-audit sections 3, 4, 9)
class JsonLd(unittest.TestCase):
    def blocks(self, html):
        return [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', html, flags=re.S)]

    @unittest.skipIf(LIVE, "waitlist block is gone after go-live")
    def test_waitlist_block_parses_and_says_pre_order_never_in_stock(self):
        (d,) = self.blocks(strip_comments(PAGES["index.html"]).replace("<!-- SALE", ""))
        self.assertEqual(d["@type"], "SoftwareApplication")
        self.assertEqual({o["price"] for o in d["offers"]}, {"0", "29", "49"})
        self.assertEqual({o["availability"] for o in d["offers"]}, {"https://schema.org/PreOrder"})
        self.assertIn("Apple silicon", d["operatingSystem"])

    @unittest.skipIf(LIVE, "waitlist block is gone after go-live")
    def test_sale_block_parses_after_go_live_and_the_only_block_is_in_stock(self):
        live = go_live_text("index.html", PAGES["index.html"])
        (d,) = self.blocks(live)
        self.assertEqual({o["availability"] for o in d["offers"]}, {"https://schema.org/InStock"})
        self.assertEqual([o.get("url") for o in d["offers"] if o["price"] != "0"], [CHECKOUT, CHECKOUT])
        self.assertNotIn("@CHECKOUT@", live)

    def test_nothing_the_product_cannot_back_is_marked_up(self):
        for text in re.findall(r'<script type="application/ld\+json">(.*?)</script>', PAGES["index.html"], flags=re.S):
            for banned in ("aggregateRating", "review", "softwareVersion", "downloadUrl", "FAQPage", "HowTo"):
                self.assertNotIn(banned, text)

    def test_json_ld_is_a_data_block_so_the_csp_needs_no_inline_script_allowance(self):
        for name, h in PAGES.items():
            for m in re.finditer(r"<script([^>]*)>", strip_comments(h) if name != "index.html" else h):
                if "ld+json" not in m.group(1) and "src=" not in m.group(1): self.fail(f"{name}: inline script {m.group(0)}")


class Metadata(unittest.TestCase):
    def meta(self, name):
        t = TREES[name]
        return ({e["a"].get("name") or e["a"].get("property"): e["a"].get("content") for e in t.find("meta")},
                [e["a"]["href"] for e in t.find("link") if e["a"].get("rel") == "canonical"],
                "".join(t.find("title")[0]["text"]))

    def test_title_and_description_lengths_and_uniqueness(self):
        titles, descs = [], []
        for name in PAGES:
            if name == "404.html": continue
            m, _, title = self.meta(name)
            titles.append(title); descs.append(m["description"])
            with self.subTest(page=name):
                self.assertTrue(15 <= len(title) <= 65, f"title {len(title)} chars: {title}")
                self.assertTrue(50 <= len(m["description"]) <= 160, f"description {len(m['description'])} chars")
        self.assertEqual(len(set(titles)), len(titles)); self.assertEqual(len(set(descs)), len(descs))

    def test_every_indexable_page_has_a_self_canonical_and_the_social_tags(self):
        for name in PAGES:
            if name == "404.html": continue
            m, canon, _ = self.meta(name)
            slug = "" if name == "index.html" else name[:-5]
            with self.subTest(page=name):
                self.assertEqual(canon, [f"https://shotfleet.com/{slug}"])
                self.assertEqual(m["og:url"], canon[0])
                for k in ("og:title", "og:description", "og:image", "og:type", "og:site_name", "twitter:card"): self.assertTrue(m.get(k), k)
                self.assertTrue(m["og:image"].startswith("https://shotfleet.com/"))

    def test_the_404_is_noindex_and_not_in_the_sitemap(self):
        m, canon, _ = self.meta("404.html")
        self.assertEqual(m["robots"], "noindex"); self.assertEqual(canon, [])
        self.assertNotIn("404", (PUB / "sitemap.xml").read_text())

    def test_every_page_has_the_icon_links_and_the_files_exist(self):
        for name, t in TREES.items():
            rels = {(e["a"].get("rel"), e["a"].get("href")) for e in t.find("link")}
            for want in (("icon", "/favicon.svg"), ("icon", "/favicon.ico"), ("apple-touch-icon", "/apple-touch-icon.png")): self.assertIn(want, rels, name)
        png = (PUB / "apple-touch-icon.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual((int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")), (180, 180))
        ico = (PUB / "favicon.ico").read_bytes()
        self.assertEqual(ico[:4], b"\x00\x00\x01\x00"); self.assertEqual((ico[6], ico[7]), (48, 48))
        self.assertEqual(ico[22:30], b"\x89PNG\r\n\x1a\n")


class RobotsAndSitemap(unittest.TestCase):
    def locs(self):
        xml = (PUB / "sitemap.xml").read_text()
        return re.findall(r"<url><loc>([^<]+)</loc>(?:<lastmod>([^<]+)</lastmod>)?</url>", xml)

    def test_robots_allows_the_site_blocks_only_the_api_and_names_the_sitemap(self):
        robots = (PUB / "robots.txt").read_text().splitlines()
        self.assertIn("User-agent: *", robots); self.assertIn("Allow: /", robots); self.assertIn("Disallow: /api/", robots)
        self.assertIn("Sitemap: https://shotfleet.com/sitemap.xml", robots)
        self.assertNotIn("Disallow: /", robots)

    def test_the_sitemap_lists_exactly_the_indexable_pages_with_a_real_date(self):
        pages = {"https://shotfleet.com/" + ("" if n == "index.html" else n[:-5]) for n in PAGES if n != "404.html"}
        locs = self.locs()
        self.assertEqual({l for l, _ in locs}, pages)
        for loc, last in locs:
            self.assertTrue(last, f"{loc} has no lastmod")
            d = date.fromisoformat(last)
            self.assertLessEqual(d, date.today()); self.assertGreaterEqual(d, date(2026, 10, 1))
            self.assertEqual(urlparse(loc).netloc, "shotfleet.com")

    def test_llms_txt_links_only_to_pages_that_exist(self):
        for url in re.findall(r"\]\((https://shotfleet\.com[^)\s]*)\)", (PUB / "llms.txt").read_text()):
            u = urlparse(url); path = u.path.strip("/")
            self.assertTrue((PUB / (path or "index.html")).exists() or (PUB / (path + ".html")).exists(), url)

    def test_the_sitemap_and_the_footer_agree_on_the_content_pages(self):
        for name in ("index.html", "alternatives.html", "terms.html", "privacy.html", "docs.html", "404.html"):
            hrefs = {e["a"].get("href") for e in TREES[name].find("a")}
            self.assertIn("/docs", hrefs, f"{name} does not link to the docs"); self.assertIn("/privacy" if name != "privacy.html" else "/alternatives", hrefs)

    def test_the_home_page_links_deep_into_the_comparison_page(self):
        hrefs = {e["a"].get("href") for e in TREES["index.html"].find("a")}
        for h in ("/alternatives", "/alternatives#fastlane", "/alternatives#butterkit", "/alternatives#appscreens"): self.assertIn(h, hrefs)
        ids = {e["a"]["id"] for e in TREES["alternatives.html"].els if "id" in e["a"]}
        self.assertTrue({"fastlane", "butterkit", "appscreens", "simshot", "shotfleet"} <= ids)

    def test_the_404_offers_ways_on(self):
        hrefs = {e["a"].get("href") for e in TREES["404.html"].find("a")}
        self.assertTrue({"/", "/docs", "/alternatives"} <= hrefs)


# ---------------------------------------------------------------- CSP and headers (critique P2 17)
class Headers(unittest.TestCase):
    def headers(self):
        return (PUB / "_headers").read_text()

    def test_style_src_has_no_unsafe_inline_because_no_page_uses_style_attributes_or_style_elements(self):
        csp = re.search(r"Content-Security-Policy: (.*)", self.headers()).group(1)
        self.assertRegex(csp, r"style-src 'self';")
        self.assertNotIn("unsafe-inline", csp)
        for name, h in PAGES.items():
            self.assertNotRegex(h, r"\sstyle=", f"{name} has a style attribute, which the CSP would block")
            self.assertNotIn("<style", h, name)
        for js in PUB.glob("*.js"):
            self.assertNotRegex(js.read_text(), r"setAttribute\(\s*['\"]style|cssText\s*=|innerHTML[^;]*style=", js.name)

    def test_opener_isolation_and_the_existing_security_headers_are_there(self):
        h = self.headers()
        for must in ("Cross-Origin-Opener-Policy: same-origin", "X-Content-Type-Options: nosniff", "Referrer-Policy:", "Permissions-Policy:", "frame-ancestors 'none'"):
            self.assertIn(must, h)


class PrintAndInputs(unittest.TestCase):
    def test_print_shows_the_content_that_scroll_reveal_hides(self):
        m = re.search(r"@media print \{(.*?)\n\}", CSS, flags=re.S)
        self.assertTrue(m)
        self.assertRegex(m.group(1), r"\.reveal[^{]*\{[^}]*opacity: 1 !important")

    def test_placeholder_text_uses_the_muted_token(self):
        self.assertRegex(CSS, r"::placeholder \{ color: var\(--muted\)")

    def test_the_hero_note_is_left_aligned_with_the_headline(self):
        self.assertNotRegex(PAGES["index.html"], r'<p class="wrap[^"]*fleet-note')
        self.assertIn('<div class="wrap"><p class="small fleet-note', PAGES["index.html"])

    def test_reduced_motion_never_hides_content(self):
        self.assertRegex(CSS, r"@media \(prefers-reduced-motion: no-preference\) \{[^@]*html\.js-reveal \.reveal \{ opacity: 0;")  # hidden only when motion is allowed


if __name__ == "__main__":
    unittest.main()
