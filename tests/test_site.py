"""Guardrails for the public site and the docs that repeat its promises. Stdlib only, no browser, no network.

Run: python3 -m unittest discover -s tests
"""
import os, re, stat, subprocess, sys, tempfile, unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

PUB = ROOT / "site/public"
PAGES = sorted(PUB.glob("*.html"))
INDEX = (PUB / "index.html").read_text()
EXAMPLES = (PUB / "examples.html").read_text()
TERMS = (PUB / "terms.html").read_text()
README = (ROOT / "README.md").read_text()
EMAIL = (ROOT / "marketing/launch-email.md").read_text()
POSTS = (ROOT / "marketing/launch-posts-v2.md").read_text()
CHECKOUT = "https://example.gumroad.com/l/shotfleet"
LIVE = "<!-- WAITLIST -->" not in INDEX  # go-live.sh already ran: the waitlist copy is gone on purpose

# Phrases that were true once, or never were. None may come back on the site, in the README or in the launch email.
BANNED = ["tested on sample projects", "tested with sample files", "works with every", "works with any app", "ai-powered", "ai powered",
          "guarantee", "first 100 on the list", "first 100 people", "before anyone else", "permission dialogs are translated",
          "permission prompts are translated", "two-line fix", "universal binary", "brew install noloman/shotfleet", "the thing every listing has to get right",
          "630 lines"]
# The launch posts get the claims that were wrong in them (not "guarantee" etc.: the notes there quote what not to say).
BANNED_IN_POSTS = ["first 100 on the list", "before anyone else", "two-line fix", "tested on sample projects", "android tablets."]


class Page(HTMLParser):
    """Collects what the checks need from one page. Comments (the WAITLIST and SALE blocks) are not parsed as markup."""
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.ids, self.refs, self.imgs, self.h1, self.inline_scripts, self.handlers, self.external = set(), [], [], 0, [], [], []
        self.text, self._script, self._dialog = [], None, 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        for name in ("href", "src", "data-full", "poster"):
            if a.get(name) is not None: self.refs.append((tag, name, a[name]))
        for name in a:
            if name.startswith("on"): self.handlers.append((tag, name))
        if tag == "a" and (a.get("href") or "").lower().startswith("javascript:"): self.handlers.append((tag, "javascript:"))
        if tag == "h1": self.h1 += 1
        if tag == "dialog": self._dialog += 1
        if tag == "img": self.imgs.append((a.get("src"), a.get("alt"), self._dialog > 0))
        if tag == "script":
            self._script = [] if "src" not in a and a.get("type", "text/javascript") in ("text/javascript", "module", "") else None
        if tag in ("script", "img", "link") and any(urlparse(a.get(n) or "").netloc for n in ("src", "href")) and not (tag == "link" and a.get("rel") in ("canonical",)):
            self.external.append((tag, a.get("src") or a.get("href")))

    def handle_endtag(self, tag):
        if tag == "dialog": self._dialog -= 1
        if tag == "script" and self._script is not None:
            if "".join(self._script).strip(): self.inline_scripts.append("".join(self._script))
            self._script = None

    def handle_data(self, data):
        if self._script is not None: self._script.append(data)
        self.text.append(data)

    def words(self):
        return re.sub(r"\s+", " ", "".join(self.text))


def go_live(index_html, checkout=CHECKOUT):
    """Run the very transform packaging/go-live.sh runs (its python heredoc, not a copy) on a throwaway copy of index.html."""
    script = (ROOT / "packaging/go-live.sh").read_text()
    code = re.search(r"<<'PY'\n(.*?)\nPY\n", script, flags=re.S).group(1)
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "site/public").mkdir(parents=True)
        (Path(d) / "site/public/index.html").write_text(index_html)
        subprocess.run([sys.executable, "-", checkout], input=code, text=True, cwd=d, check=True)
        return (Path(d) / "site/public/index.html").read_text()


def resolve(ref, page_ids):
    """Does a local href/src point at something that exists? (Cloudflare serves /terms from terms.html and / from index.html.)"""
    u = urlparse(ref)
    if u.scheme in ("http", "https", "mailto", "tel", "data"): return True
    if not u.path: return u.fragment in page_ids or not u.fragment
    path = PUB / (u.path.lstrip("/") or "index.html")
    if not path.is_file() and path.with_name(path.name + ".html").exists(): path = path.with_name(path.name + ".html")  # /guides: guides.html beats guides/
    elif path.is_dir(): path = path / "index.html"
    if not path.exists(): return False
    if u.fragment: return u.fragment in Page(path.read_text()).ids
    return True


class Structure(unittest.TestCase):
    def pages(self):
        yield from ((p.name, Page(p.read_text())) for p in PAGES)
        if not LIVE: yield "index.html after go-live", Page(go_live(INDEX))

    def test_every_local_link_image_and_script_exists_and_anchors_resolve(self):
        for name, page in self.pages():
            for tag, attr, ref in page.refs:
                with self.subTest(page=name, ref=ref):
                    self.assertTrue(resolve(ref, page.ids), f"{name}: <{tag} {attr}={ref!r}> points at nothing")

    def test_social_image_exists(self):
        for m in re.findall(r'property="og:image" content="https://shotfleet\.manulorenzop\.workers\.dev/([^"]+)"', INDEX):
            self.assertTrue((PUB / m).is_file(), m)

    def test_every_image_has_alt_text(self):
        for name, page in self.pages():
            self.assertTrue(page.imgs or name != "index.html", "no images found: is the parser broken?")
            for src, alt, in_dialog in page.imgs:
                self.assertIsNotNone(alt, f"{name}: {src} has no alt")
                if not in_dialog: self.assertTrue(alt.strip(), f"{name}: {src} has empty alt")  # only the zoom dialog's image starts empty

    def test_exactly_one_h1_per_page(self):
        for name, page in self.pages(): self.assertEqual(page.h1, 1, name)

    def test_no_orphan_images(self):
        used = {Path(r).name for _, page in self.pages() for _, _, r in page.refs if "img/" in r} | {"og.jpg"}
        for p in (PUB / "img").rglob("*.jpg"): self.assertIn(p.name, used, f"{p.relative_to(PUB)} is not used by any page")

    def test_the_gallery_has_no_remoti_tab_and_defaults_to_the_first_tab(self):
        self.assertNotIn("remoti", EXAMPLES.lower())  # its UI is English under translated captions, the failure the product catches
        tabs = re.findall(r'role="tab" id="tab-(\w+)"[^>]*aria-selected="(\w+)"', EXAMPLES)
        self.assertEqual(tabs, [("stressi", "true"), ("cairn", "false")])
        self.assertIn("show(tabs[0])", (PUB / "tabs.js").read_text())
        self.assertEqual(set(re.findall(r'data-full="img/full/(\w+?)_', EXAMPLES)), {"stressi", "cairn"})

    def test_every_demo_video_loads_nothing_until_played_and_has_a_poster_and_english_captions(self):
        visible = re.sub(r"<!--.*?-->", "", (PUB / "demo.html").read_text(), flags=re.S)  # clips not recorded yet wait in comments
        videos = re.findall(r"<video\b[^>]*>.*?</video>", visible, flags=re.S)
        self.assertTrue(videos)
        for v in videos:
            with self.subTest(video=v[:120]):
                for must in ('preload="none"', "muted", "playsinline", 'poster="/media/demo/', 'src="/media/demo/', '<track kind="captions" srclang="en"'):
                    self.assertIn(must, v)

    def test_no_resource_comes_from_another_server(self):
        for name, page in self.pages(): self.assertEqual(page.external, [], name)


class StrayTags(unittest.TestCase):
    """`<App>` typed in prose or in <code> is parsed as a tag and the word vanishes: write &lt;App&gt;. Every start tag on every public page (and guide) must be a known element."""
    KNOWN = set("""a b body br button caption circle code dd defs dialog div dl dt em figcaption figure footer form g h1 h2 h3 h4 head header hr html i img input label
        li link main mask meta nav ol p path pre rect script section span strong style svg table tbody td textarea th thead title tr track ul video""".split())

    def test_every_start_tag_is_a_real_html_or_svg_element(self):
        class Tags(HTMLParser):
            def __init__(self): super().__init__(); self.names = set()
            def handle_starttag(self, tag, attrs): self.names.add(tag)
        for p in PAGES + sorted((PUB / "guides").glob("*.html")):
            tags = Tags(); tags.feed(p.read_text())
            with self.subTest(page=p.name): self.assertEqual(tags.names - self.KNOWN, set(), "a placeholder like <App> in text or code: write &lt;App&gt;")


class Style(unittest.TestCase):
    TEXT_FILES = [*PUB.glob("*"), *(ROOT / "site/draft").glob("*"), ROOT / "README.md", ROOT / "DISTRIBUTION.md", ROOT / "LAUNCH.md",
                  *(ROOT / "marketing").glob("launch-*.md")]

    def test_no_em_dash_anywhere_on_the_site_or_in_the_launch_texts(self):
        for p in self.TEXT_FILES:
            if p.is_file() and p.suffix in (".html", ".css", ".js", ".md", ".txt", ".sh", ""):
                self.assertNotIn("—", p.read_text(), p.relative_to(ROOT))

    def test_banned_phrases_are_absent(self):
        files = {**{p.name: p.read_text() for p in PAGES}, "README.md": README, "launch-email.md": EMAIL}
        for name, text in files.items():
            for phrase in BANNED:
                self.assertNotIn(phrase, text.lower(), f"{name} says {phrase!r}")
        for phrase in BANNED_IN_POSTS: self.assertNotIn(phrase, POSTS.lower().replace("do not claim", ""), f"launch-posts-v2.md says {phrase!r}")


class Offer(unittest.TestCase):
    """One price, one refund window, one founder count, one free tier, everywhere."""
    DOCS = {"index.html": INDEX, "terms.html": TERMS, "README.md": README, "launch-email.md": EMAIL}

    def test_prices_are_29_launch_and_49_standard_everywhere(self):
        for name, text in self.DOCS.items():
            self.assertLessEqual(set(re.findall(r"\$(\d+)", text)), {"29", "49"}, name)
        for name in ("index.html", "README.md", "launch-email.md"):
            self.assertEqual(set(re.findall(r"\$(\d+)", self.DOCS[name])), {"29", "49"}, name)

    def test_founder_price_is_for_the_first_100_buyers_everywhere(self):
        for name in ("index.html", "README.md", "launch-email.md"):
            self.assertEqual(set(re.findall(r"first (\d+)", self.DOCS[name])), {"100"}, name)
            self.assertIn("first 100 buyers", self.DOCS[name], name)

    def test_refund_window_is_14_days_everywhere(self):
        for name, text in self.DOCS.items():
            found = set(re.findall(r"(\d+)[- ]day refund", text)) | set(re.findall(r"within (\d+) days(?! of (?:your|the) purchase)", text))
            if name in ("index.html", "terms.html", "launch-email.md", "README.md"): self.assertEqual(found, {"14"}, name)

    def test_free_tier_wording_matches_the_code_on_every_page(self):
        for name, text in self.DOCS.items():
            plain = re.sub(r"<[^>]+>", "", text)
            if name != "launch-email.md": self.assertEqual(set(re.findall(r"up to (\d+) languages", plain)), {str(sf.FREE_LANGUAGES)}, name)
        self.assertRegex(re.sub(r"<[^>]+>", "", INDEX), r"Capture up to 2 languages with run")
        self.assertRegex(re.sub(r"<[^>]+>", "", TERMS), r"check is free for everyone, and run is free for up to 2 languages\. The licence unlocks every language and export\.")
        self.assertIn("`shotfleet check` is free for everyone, and `run` is free for up to 2 languages. A licence unlocks every language and `export`", README)

    def test_limits_match_the_code(self):
        self.assertEqual(sf.MAX_MACS, 5); self.assertIn(f"A key can be activated {sf.MAX_MACS} times: 3 Macs and 2 spare for reinstalls", TERMS)
        for text in (INDEX, TERMS): self.assertIn("there are spare activations for reinstalls, and if you run out, email", text)
        self.assertNotRegex(INDEX + TERMS + README, r"\b3 activations")
        self.assertIn(f"works offline for {sf.LICENCE_OFFLINE_DAYS} days", INDEX); self.assertIn(f"up to {sf.LICENCE_OFFLINE_DAYS} days", TERMS)
        self.assertIn("about once a week", TERMS); self.assertEqual(sf.LICENCE_RECHECK_DAYS, 7)

    def test_apple_silicon_is_said_where_a_buyer_decides(self):
        for text in (INDEX, TERMS, README): self.assertIn("Apple silicon", text)
        self.assertEqual(INDEX.count("needs an Apple silicon Mac, Maestro and Java 17+"), 1 if LIVE else 2)  # waitlist and sale versions
        self.assertIn("arm64", (PUB / "install.sh").read_text())  # and the installer really refuses anything else

    def test_the_updates_promise_is_not_an_unconditional_forever(self):
        self.assertIn("The renewal isn't on sale yet, so for now email", TERMS)  # renewal
        self.assertNotIn("you can renew", TERMS)
        self.assertIn("Versions you have keep working while macOS and your tools allow", INDEX)
        self.assertIn("keep working for as long as macOS, Xcode and Maestro let them, and as long as the licence check can run", TERMS)


@unittest.skipIf(LIVE, "the site is already live; the waitlist blocks are gone")
class GoLive(unittest.TestCase):
    def test_the_waitlist_and_sale_blocks_are_balanced(self):
        self.assertEqual(INDEX.count("<!-- WAITLIST -->"), INDEX.count("<!-- /WAITLIST -->"))
        self.assertGreaterEqual(INDEX.count("<!-- WAITLIST -->"), 3)
        self.assertEqual(INDEX.count("    <!-- SALE\n"), INDEX.count("    SALE -->"))
        self.assertGreaterEqual(INDEX.count("    <!-- SALE\n"), 3)

    def test_go_live_turns_it_into_a_sale_page_with_a_checkout_link_and_no_markers(self):
        live = go_live(INDEX)
        for marker in ("WAITLIST", "SALE", "@CHECKOUT@", "@GUMROAD@", "data-signup", "id=\"signup", "isn’t released yet", "Get early access", "Join the list"):
            self.assertNotIn(marker, live, marker)
        self.assertGreaterEqual(live.count(f'href="{CHECKOUT}"'), 3)  # nav, hero, price card
        self.assertEqual(live.count("curl -fsSL https://shotfleet.com/install.sh | sh"), 1)
        self.assertIn("Buy shotfleet", live); self.assertNotIn("Early access", live)
        self.assertIn("It needs an Apple silicon Mac, Maestro and Java 17+.", live)
        for must in ("<h1>", 'id="price"', 'data-full="img/full/stressi_ja.jpg"', "/forms.js", "/tabs.js"): self.assertIn(must, live)

    def test_the_waitlist_page_still_has_its_signup_form_and_no_checkout_placeholder_outside_comments(self):
        visible = re.sub(r"<!--.*?-->", "", INDEX, flags=re.S)
        self.assertIn("data-signup", visible); self.assertNotIn("@CHECKOUT@", visible)


class Security(unittest.TestCase):
    def csp(self):
        line = next(l for l in (PUB / "_headers").read_text().splitlines() if l.strip().startswith("Content-Security-Policy:"))
        return {d.split()[0]: d.split()[1:] for d in line.split(":", 1)[1].split(";") if d.strip()}

    def test_csp_allows_no_inline_script_and_no_other_origin(self):
        csp = self.csp()
        self.assertEqual(csp["default-src"], ["'self'"])
        # Google Analytics 4 is allowed on purpose, and only loads after consent (ga.js); the exact hosts are pinned in tests/test_consent.py
        self.assertEqual(csp["script-src"], ["'self'", "https://www.googletagmanager.com"])  # no 'unsafe-inline', no 'unsafe-eval'
        self.assertEqual(csp["img-src"][0], "'self'"); self.assertEqual(csp["connect-src"][0], "'self'")
        self.assertEqual(csp["frame-ancestors"], ["'none'"])
        self.assertNotIn("unsafe-eval", " ".join(sum(csp.values(), [])))

    def test_pages_have_no_inline_script_and_no_event_handler_attributes(self):
        for p in PAGES + ([] if LIVE else [None]):
            name, page = (p.name, Page(p.read_text())) if p else ("index.html after go-live", Page(go_live(INDEX)))
            self.assertEqual(page.inline_scripts, [], name)
            self.assertEqual(page.handlers, [], name)


class WaitlistPurge(unittest.TestCase):
    """site/signups.sh --purge-waitlist makes the 30-day promise doable: it deletes the email: records and nothing else."""
    def run_purge(self, answer):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); bin_ = d / "bin"; bin_.mkdir()
            npx = bin_ / "npx"
            npx.write_text(f"""#!/bin/sh
case "$*" in
  *"key list"*) echo '[{{"name":"email:a@x.com"}},{{"name":"email:b@x.com"}}]' ;;
  *"bulk delete"*) cp "$6" "{d}/deleted.json"; echo "$*" > "{d}/args" ;;
esac
""")
            npx.chmod(npx.stat().st_mode | stat.S_IEXEC)
            r = subprocess.run(["sh", str(ROOT / "site/signups.sh"), "--purge-waitlist"], input=answer, text=True, capture_output=True,
                               env={**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}"})
            deleted = (d / "deleted.json").read_text() if (d / "deleted.json").exists() else None
            args = (d / "args").read_text() if (d / "args").exists() else ""
        return r, deleted, args

    def test_typing_purge_deletes_exactly_the_email_records(self):
        r, deleted, args = self.run_purge("PURGE\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("2 waitlist emails will be deleted", r.stdout)
        self.assertEqual(deleted.strip(), '["email:a@x.com", "email:b@x.com"]')
        self.assertIn("--binding WAITLIST --remote --force", args)

    def test_anything_else_deletes_nothing(self):
        r, deleted, _ = self.run_purge("no\n")
        self.assertNotEqual(r.returncode, 0); self.assertIsNone(deleted); self.assertIn("nothing deleted", r.stdout)


class PrivacyPage(unittest.TestCase):
    def test_privacy_says_what_the_program_and_the_site_really_do(self):
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", (PUB / "privacy.html").read_text()))
        for must in ("about once a week", "the product ID", "count as an activation", "shotfleet doctor", "latest version number",
                     "by day, by the site or link you came from, and by your browser's language", "your IP address is not stored",
                     "The waitlist is closed and I never emailed it. Any address still on it will be deleted",
                     "kept until I've answered them", "I delete them on request", "Your app and screenshots are never uploaded"):
            self.assertIn(must, text)
        self.assertNotIn("I delete the list 30 days after", text)  # that was a promise nothing carried out
        self.assertNotIn("after I send the launch email", text)  # no waitlist email was ever sent


class WhatsNew(unittest.TestCase):
    """/whats-new: linked from every page, listed for crawlers, and its newest release date filled in before that release is published."""
    PAGE = (PUB / "whats-new.html").read_text()
    PLACEHOLDER = "<!-- RELEASE_DATE -->"

    def test_every_page_links_to_it_in_the_nav_and_in_the_footer(self):
        for p in PAGES:
            html = re.sub(r"<!--.*?-->", "", p.read_text(), flags=re.S)
            with self.subTest(page=p.name):
                self.assertIn('/whats-new">', re.search(r'<span class="links">(.*?)</span>', html, flags=re.S).group(1))
                self.assertIn('href="/whats-new"', re.search(r"<footer>(.*?)</footer>", html, flags=re.S).group(1))

    def test_it_is_in_the_sitemap_and_llms_txt(self):
        self.assertIn("<loc>https://shotfleet.com/whats-new</loc>", (PUB / "sitemap.xml").read_text())
        self.assertEqual((PUB / "llms.txt").read_text().count("](https://shotfleet.com/whats-new)"), 1)

    def test_the_newest_release_date_is_filled_in_once_the_changelog_has_it(self):
        """The release step dates the CHANGELOG heading (## X.Y.Z (YYYY-MM-DD)) and must put the same date here; packaging/publish.sh refuses the placeholder too."""
        newest = re.search(r'<h2 id="v[\d-]+">(\d+\.\d+\.\d+), (.*?)</h2>', self.PAGE)
        self.assertTrue(newest, "no release heading on /whats-new")
        version, when = newest.groups()
        self.assertEqual(self.PAGE.count(self.PLACEHOLDER), int(when == self.PLACEHOLDER), "the placeholder belongs in the newest heading only")
        dated = re.search(rf"^## {re.escape(version)} \((\d{{4}}-\d\d-\d\d)\)", (ROOT / "CHANGELOG.md").read_text(), flags=re.M)
        if dated: self.assertEqual(when, dated.group(1), f"{version} is released on {dated.group(1)}: replace {self.PLACEHOLDER} on /whats-new with that date")
        else: self.assertEqual(when, self.PLACEHOLDER, f"{version} has no dated CHANGELOG heading yet, so its date stays the placeholder")
        for v, d in re.findall(r'<h2 id="v[\d-]+">(\d+\.\d+\.\d+), (\d{4}-\d\d-\d\d)</h2>', self.PAGE):
            with self.subTest(version=v): self.assertRegex((ROOT / "CHANGELOG.md").read_text(), rf"(?m)^## {re.escape(v)} \(")


class DockerPending(unittest.TestCase):
    """The Linux check image and its GitHub Action are not published yet. Until site/DOCKER_PUBLISHED exists, no public file mentions it (the held-back text is in
    site/draft/docker-pending.txt); after publishing, put it back and add the flag file."""
    FILES = [p for p in sorted(PUB.glob("*")) if p.suffix in (".html", ".txt", ".xml", ".js")]
    PUBLISHED = (ROOT / "site/DOCKER_PUBLISHED").exists()

    def test_no_uncommented_mention_while_the_image_is_unpublished(self):
        seen = 0
        for p in self.FILES:
            text = p.read_text()
            seen += text.count("ghcr.io/noloman/shotfleet-check")
            with self.subTest(file=p.name):
                self.assertEqual(text.count("<!-- DOCKER-PENDING"), text.count("DOCKER-PENDING -->"))
                if self.PUBLISHED: self.assertNotIn("DOCKER-PENDING", text, "published: remove the markers")
                else: self.assertNotIn("noloman/shotfleet-check", re.sub(r"<!--.*?-->", "", text, flags=re.S))

    def test_the_readme_follows_the_same_flag(self):
        text = (ROOT / "README.md").read_text()
        self.assertEqual(text.count("<!-- DOCKER-PENDING"), text.count("DOCKER-PENDING -->"))
        if self.PUBLISHED: self.assertNotIn("DOCKER-PENDING", text, "published: remove the markers")
        else:
            visible = re.sub(r"<!--.*?-->", "", text, flags=re.S)
            for word in ("docker", "ghcr", "noloman/shotfleet-check", "linux and ci"): self.assertNotIn(word, visible.lower())


class ByocPending(unittest.TestCase):
    """Bring your own capture ([capture], your own XCUITest tests on iOS). Passed its device test 2026-10-07, so site/BYOC_DEVICE_PROVEN exists and
    no public line may say otherwise. Without the flag, every public line that offers it carries CAVEAT."""
    CAVEAT = "its device test hasn't passed yet"
    FILES = [ROOT / "README.md"] + [p for p in sorted(PUB.glob("*")) if p.suffix in (".html", ".txt")]
    PROVEN = (ROOT / "site/BYOC_DEVICE_PROVEN").exists()

    def test_every_line_offering_your_own_xcuitest_tests_says_it_is_not_device_proven(self):
        seen = 0
        for p in self.FILES:
            for n, line in enumerate(p.read_text().splitlines(), 1):
                with self.subTest(file=p.name, line=n):
                    if self.PROVEN: self.assertNotRegex(line.replace("’", "'"), r"(?i)(hasn't|has not|not) passed( yet)?\b|device test (hasn't|has not)", "BYOC_DEVICE_PROVEN exists: no caveat")
                    elif "your own XCUITest" in line:
                        seen += 1
                        self.assertIn(self.CAVEAT, line.replace("’", "'"), "BYOC is not device-proven yet: say so on this line")
        if not self.PROVEN: self.assertGreaterEqual(seen, 10, "fewer BYOC lines than expected: is this test still looking at the right files?")

    def test_a_line_saying_you_need_neither_maestro_nor_java_for_xcuitest_tests_says_it_is_not_device_proven(self):
        seen = 0
        for p in self.FILES:
            for n, line in enumerate(p.read_text().splitlines(), 1):
                if "XCUITest" in line and re.search(r"Maestro or Java|neither", line):
                    seen += 1
                    with self.subTest(file=p.name, line=n):
                        if not self.PROVEN: self.assertIn(self.CAVEAT, line.replace("’", "'"), "this line says no Maestro or Java for XCUITest tests: say it is not device-proven")
        self.assertGreaterEqual(seen, 6)  # README and docs lead + needs sentence, home page, llms.txt, alternatives


class ActivationCaveat(unittest.TestCase):
    def test_every_page_that_promises_spare_activations_says_they_start_with_0_1_6(self):
        for path in (PUB / "docs.html", PUB / "terms.html", PUB / "index.html", PUB / "llms.txt", ROOT / "README.md"):
            with self.subTest(page=path.name): self.assertIn("The spare activations work from 0.1.6; 0.1.5 and older stop at 3.", path.read_text())


class SecurityTxt(unittest.TestCase):
    """RFC 9116: /.well-known/security.txt. Workers static assets upload dot-directories (wrangler's asset ignore list is only .assetsignore, _headers, _redirects)."""
    F = PUB / ".well-known/security.txt"

    def test_the_file_has_exactly_the_four_fields(self):
        text = self.F.read_text(); self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"))
        self.assertEqual([l.split(": ", 1)[0] for l in text.splitlines()], ["Contact", "Expires", "Preferred-Languages", "Canonical"])
        f = dict(l.split(": ", 1) for l in text.splitlines())
        self.assertEqual(f["Contact"], "mailto:hello@shotfleet.com"); self.assertEqual(f["Preferred-Languages"], "en")
        self.assertEqual(f["Canonical"], "https://shotfleet.com/.well-known/security.txt")

    def test_expires_is_in_the_future_and_under_a_year_away(self):
        from datetime import datetime, timedelta, timezone
        exp = dict(l.split(": ", 1) for l in self.F.read_text().splitlines())["Expires"]
        self.assertRegex(exp, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z$")
        when = datetime.fromisoformat(exp.replace("Z", "+00:00")); now = datetime.now(timezone.utc)
        self.assertGreater(when, now, f"security.txt expired on {exp}: bump Expires in site/public/.well-known/security.txt")
        self.assertLess(when - now, timedelta(days=366), "RFC 9116: Expires should be less than a year away")

    def test_headers_serve_it_as_utf8_text_plain(self):
        self.assertIn("/.well-known/security.txt\n  Content-Type: text/plain; charset=utf-8\n", (PUB / "_headers").read_text())

    def test_nothing_ignores_it_and_the_worker_is_not_in_its_way(self):
        self.assertFalse(any(".well-known" in (ROOT / p).read_text() for p in ("site/public/.assetsignore", "site/.assetsignore") if (ROOT / p).exists()))
        self.assertNotIn("well-known", (ROOT / "site/worker.js").read_text())  # worker runs first only for /api/* (wrangler.toml), so this is a plain asset


class Hsts(unittest.TestCase):
    def test_every_page_sends_hsts_for_six_months_without_subdomains_or_preload(self):
        block = (ROOT / "site/public/_headers").read_text().split("\n\n")[0]
        self.assertIn("Strict-Transport-Security: max-age=15552000", block)
        self.assertNotIn("includeSubDomains", block); self.assertNotIn("preload", block)


class TextFilesAreUtf8(unittest.TestCase):
    """Plain-text files say charset=utf-8. /download/VERSION also matches `/download/:file` (Cache-Control: no-cache); the rules merge by header name, so its own rule sets only Content-Type."""
    RULES = {b.splitlines()[0]: b.splitlines()[1:] for b in (PUB / "_headers").read_text().strip().split("\n\n")}

    def test_each_text_file_has_one_utf8_plain_text_content_type_rule(self):
        for path in ("/download/VERSION", "/llms.txt", "/robots.txt", "/install.sh", "/.well-known/security.txt"):
            with self.subTest(path=path): self.assertEqual([l.strip() for l in self.RULES[path]].count("Content-Type: text/plain; charset=utf-8"), 1)

    def test_versioned_sha256_files_are_utf8_text_and_stay_immutable(self):
        # live they had no content-type; Cache-Control comes from /download/:version/* (rules merge by header name)
        self.assertEqual([l.strip() for l in self.RULES["/download/:version/*.sha256"]], ["Content-Type: text/plain; charset=utf-8"])
        self.assertEqual([l.strip() for l in self.RULES["/download/:version/*"]], ["Cache-Control: public, max-age=31536000, immutable"])

    def test_version_is_still_no_cache_and_its_own_rule_adds_no_second_cache_control(self):
        self.assertEqual([l.strip() for l in self.RULES["/download/:file"]], ["Cache-Control: no-cache"])
        self.assertFalse([l for l in self.RULES["/download/VERSION"] if "Cache-Control" in l])


if __name__ == "__main__":
    unittest.main()
