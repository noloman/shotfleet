"""Proof for the site-layer claims C002, C033, C042, C077 to C084, C087, C088, C101 and C104 (tests/claims.json).

Worker behaviour is proved by site/worker.test.mjs (run once here, then each named check is looked up); form and counter behaviour by
tests/browser_site.cjs (Chromium through Playwright, every /api call stubbed; skipped when Playwright or Chromium is missing).
Nothing here touches the network or the live site: what only the live site, a device or a real payment can show is said in the register.

Run: python3 -m unittest discover -s tests
"""
import html, json, os, re, shutil, stat, subprocess, sys, tempfile, unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
import shotfleet as sf
from test_site import Page, go_live, LIVE, INDEX as INDEX_HTML
from test_cli_claims import fixture, STRINGS

PUB = ROOT / "site/public"
NODE = shutil.which("node")


def read(rel):
    return (ROOT / rel).read_text()


def plain(text):
    """Visible text: tags dropped, entities decoded, whitespace collapsed."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).replace(" ,", ",").replace(" .", ".")


def run_node(*args, timeout=180):
    return subprocess.run([NODE, *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)


# --------------------------------------------------------------------------------------------------------------------- C002, C033
class PlatformAndRequirements(unittest.TestCase):
    """Mac only, Apple silicon only, and the same prerequisites everywhere a buyer reads them."""

    def installer(self, system, machine):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); (d / "bin").mkdir()
            (d / "bin/uname").write_text('#!/bin/sh\ncase "$1" in -s) echo "$FAKE_S";; -m) echo "$FAKE_M";; *) echo "$FAKE_S";; esac\n')
            (d / "bin/curl").write_text(f'#!/bin/sh\ntouch "{d}/reached-the-download"\nexit 1\n')  # the first thing after the guards
            for f in (d / "bin").iterdir(): f.chmod(f.stat().st_mode | stat.S_IEXEC)
            env = {"PATH": f"{d}/bin:/usr/bin:/bin", "FAKE_S": system, "FAKE_M": machine, "HOME": str(d)}
            r = subprocess.run(["sh", str(PUB / "install.sh")], capture_output=True, text=True, env=env, timeout=30)
            return r.returncode, r.stderr, (d / "reached-the-download").exists()

    def test_install_sh_refuses_linux_and_intel_macs_and_lets_apple_silicon_through(self):
        for system, machine, message in (("Linux", "x86_64", "macOS only"), ("Linux", "aarch64", "macOS only"), ("Darwin", "x86_64", "Apple silicon")):
            with self.subTest(system=system, machine=machine):
                code, err, reached = self.installer(system, machine)
                self.assertEqual(code, 1); self.assertIn(message, err); self.assertFalse(reached, "it started downloading")
        code, err, reached = self.installer("Darwin", "arm64")
        self.assertTrue(reached, "an Apple silicon Mac was stopped before the download")

    def test_the_site_terms_and_readme_say_apple_silicon_where_a_buyer_decides(self):
        text = plain(INDEX_HTML)
        self.assertIn("It needs an Apple silicon Mac, Maestro and Java 17+.", text)
        self.assertIn("you don’t have an Apple silicon Mac. iOS simulators need a Mac", text)
        self.assertRegex(plain(read("site/public/terms.html")), r"Apple silicon")
        self.assertIn("macOS on Apple silicon only (the installer refuses Intel Macs)", read("README.md"))
        self.assertIn("Apple silicon", read("site/public/alternatives.html"))

    def test_every_place_that_lists_the_prerequisites_names_the_same_things(self):
        readme = read("README.md"); limits = next(l for l in readme.splitlines() if "Needs Xcode for iOS" in l)
        ld = set(re.findall(r'"softwareRequirements": "([^"]+)"', INDEX_HTML)); self.assertEqual(len(ld), 1)
        places = {"README Limits": limits, "index.html data": ld.pop(), "llms.txt": read("site/public/llms.txt")}
        for name, text in places.items():
            with self.subTest(place=name):
                for need in ("Java 17", "Maestro", "Xcode for iOS", "Android SDK"): self.assertIn(need, text)
        self.assertIn("Apple silicon", places["README Limits"]); self.assertIn("Apple silicon", places["index.html data"])
        self.assertIn("Maestro 2.x", places["index.html data"]); self.assertIn("Maestro 2.x", places["llms.txt"])
        self.assertIn("tested with 2.0.10", limits)
        self.assertEqual(sf.MAESTRO_TESTED, ("2.0.10", "2.11.0"))
        # the one-sentence version on the page is a subset of that set and never names another Java
        for rel in ("README.md", "site/public/index.html", "site/public/llms.txt", "site/public/alternatives.html", "site/public/terms.html"):
            self.assertNotRegex(plain(read(rel)), r"Java (1[0-6]|[0-9])\b(?!\.)", rel)

    def test_java_17_is_the_real_floor_in_the_program(self):
        from unittest import mock
        majors = {}
        with mock.patch.dict(os.environ, {"PATH": "/usr/bin", "JAVA_HOME": "/j"}), mock.patch.object(sf.shutil, "which", return_value=None), \
             mock.patch.object(sf, "java_major", side_effect=lambda j: majors.get(str(j), 0)), \
             mock.patch.object(sf.Path, "exists", return_value=False), mock.patch.object(sf.glob, "glob", return_value=[]):
            majors["/j/bin/java"] = 16
            self.assertEqual(sf.find_java(), (False, None))
            majors["/j/bin/java"] = 17
            self.assertEqual(sf.find_java(), (True, None))
        sf.java_env.cache_clear()


# --------------------------------------------------------------------------------------------------------------------- C042
class PriceAgreement(unittest.TestCase):
    """$29 for the first 100 buyers, then $49 once per developer: every text that says so says the same."""
    CUSTOMER = ["site/public/index.html", "site/public/terms.html", "site/public/alternatives.html", "site/public/llms.txt", "README.md",
                "marketing/launch-email.md", "marketing/launch-posts-v2.md", "site/draft/alternatives.html"]
    INTERNAL = ["LAUNCH.md", "DISTRIBUTION.md", "STRATEGY.md", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "marketing/kit").glob("*.md"))]
    OWN_ROW = {"site/public/alternatives.html": r"<th scope=\"row\">shotfleet</th>.*?</tr>", "site/draft/alternatives.html": r"<td>shotfleet</td>.*?</tr>"}

    def text(self, rel):
        raw = read(rel)
        if rel in self.OWN_ROW:  # the comparison pages quote other tools' prices too; only shotfleet's own row is ours
            raw = re.search(self.OWN_ROW[rel], raw, flags=re.S).group(0)
        return plain(raw) if rel.endswith(".html") else raw

    def segments(self, rel):
        """Every stretch of text around a 'first N buyers/people/on the list' phrase."""
        t = self.text(rel)
        return [(m.group(1), t[max(0, m.start() - 160):m.end() + 160]) for m in re.finditer(r"first (\d+)\*{0,2} (?:buyers|people|on the list)", t)]

    def test_the_only_shotfleet_prices_are_29_and_49(self):
        for rel in self.CUSTOMER:
            with self.subTest(file=rel):
                found = set(re.findall(r"\$(\d+)", self.text(rel)))
                if rel in ("site/public/index.html", "README.md", "marketing/launch-email.md", "site/public/llms.txt", "marketing/launch-posts-v2.md"):
                    self.assertTrue({"29", "49"} <= found, found)
                if rel == "marketing/launch-posts-v2.md": found -= {"99", "180"}  # other tools' prices, quoted in the comparison bullets
                self.assertLessEqual(found, {"29", "49"})
        # amounts quoted beside the offer in the operating docs: the discount is the difference, the rest are fees
        launch = read("LAUNCH.md")
        self.assertIn("**$49** once, **$29 for the first 100**", launch); self.assertIn("($20 off, limit 100 uses, applied automatically)", launch)
        self.assertEqual(49 - 20, 29)
        self.assertIn("`FOUNDER29` $20 off for the first 100", read("DISTRIBUTION.md"))
        self.assertIn("$29 founder price for the first 100 buyers", read("STRATEGY.md"))

    def test_every_first_n_is_100_and_says_buyers_never_the_list(self):
        seen = 0
        for rel in self.CUSTOMER + self.INTERNAL:
            for n, seg in self.segments(rel):
                seen += 1
                with self.subTest(file=rel, around=seg[150:200]):
                    self.assertEqual(n, "100")
        self.assertGreaterEqual(seen, 20, "the phrase collector found too little: is it broken?")
        for rel in self.CUSTOMER + self.INTERNAL:
            t = self.text(rel)
            for bad in ("first 100 on the list", "first 100 people", "before anyone else", "founder price for the list"):
                with self.subTest(file=rel, bad=bad): self.assertNotIn(bad, t)

    def test_wherever_the_29_is_offered_the_49_follows_in_the_same_breath(self):
        strict = ["site/public/index.html", "site/public/alternatives.html", "site/public/llms.txt", "README.md", "marketing/launch-email.md"]
        for rel in self.CUSTOMER + [r for r in self.INTERNAL if r.startswith("marketing/kit/")]:
            both = [seg for n, seg in self.segments(rel) if "$29" in seg and "$49" in seg]
            alone = [seg for n, seg in self.segments(rel) if "$29" in seg and "$49" not in seg]
            with self.subTest(file=rel):
                if rel in strict: self.assertEqual(alone, []); self.assertTrue(both)  # every offer sentence names the later price too
                elif rel in self.CUSTOMER and (both or alone): self.assertTrue(both)               # the posts and drafts state the whole offer at least once; their notes only refer back to it
        card = plain(INDEX_HTML)
        self.assertRegex(card, r"\$29 ?launch price, first 100 buyers Then \$49 once, per developer\.")
        self.assertIn("Prices are before VAT where it applies", card)

    def test_structured_data_on_the_page_has_the_same_two_prices_and_a_free_tier(self):
        pages = [re.sub(r"<!-- SALE\n.*?    SALE -->", "", INDEX_HTML, flags=re.S)]  # the waitlist page as served ...
        if not LIVE: pages.append(go_live(INDEX_HTML))                                       # ... and the sale page after go-live.sh
        for page in pages:
            blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, flags=re.S)]
            offers = [o for b in blocks for o in (b.get("offers") if isinstance(b.get("offers"), list) else [])]
            self.assertEqual(sorted(o["price"] for o in offers), ["0", "29", "49"])
            by = {o["price"]: o["description"] for o in offers}
            self.assertIn("first 100 buyers", by["29"]); self.assertIn("after the first 100 buyers", by["49"])

    def test_the_free_tier_in_the_same_sentences_matches_the_code(self):
        self.assertEqual(sf.FREE_LANGUAGES, 2)
        for rel in ("README.md", "site/public/llms.txt"):
            self.assertRegex(self.text(rel), r"up to 2 languages|run` is free for 2 languages|2 languages in `run`")


# --------------------------------------------------------------------------------------------------------------------- C101
class LinksResolve(unittest.TestCase):
    """Every shotfleet.com address and relative link in the README, the launch texts and the docs lands on something the site has."""
    TEXTS = ["README.md", "LAUNCH.md", "DISTRIBUTION.md", "marketing/launch-email.md", "marketing/launch-posts-v2.md", "site/public/llms.txt"]
    KIT = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "marketing/kit").glob("*.md"))
    RELEASE_FILES = {"VERSION", "shotfleet-macos-arm64.tar.gz", "shotfleet-macos-arm64.tar.gz.sha256", "shotfleet-macos-arm64.pkg"}  # built by packaging/release.sh, not kept in the repo
    URL = re.compile(r"https://shotfleet\.com(/[^\s)>\]`'\"*,;<]*)?")

    def index_ids(self):
        ids = [Page(INDEX_HTML).ids]
        if not LIVE: ids.append(Page(go_live(INDEX_HTML)).ids)  # the page the day the sale opens
        return ids

    def ids_for(self, path):
        """Lists of id sets the page can have (index has two while the waitlist is up). None: the path is not a page."""
        if path in ("", "/"): return self.index_ids()
        f = PUB / path.lstrip("/")
        if not f.is_file(): f = f.with_name(f.name + ".html")
        return [Page(f.read_text()).ids] if f.suffix == ".html" and f.is_file() else None

    def addresses(self, rel):
        out = []
        for m in self.URL.finditer(read(rel)):
            u = urlparse("https://shotfleet.com" + (m.group(1) or "").rstrip(".:!?"))
            out.append((u.path, u.fragment))
        return out

    def test_every_address_in_the_texts_resolves_to_a_published_file_and_anchor(self):
        checked = 0
        for rel in self.TEXTS:
            for path, frag in self.addresses(rel):
                checked += 1
                with self.subTest(file=rel, url=path + ("#" + frag if frag else "")):
                    if path.startswith("/download/"): self.assertIn(path.split("/")[-1], self.RELEASE_FILES); continue
                    if path in ("/install.sh", "/llms.txt", "/robots.txt", "/sitemap.xml"): self.assertTrue((PUB / path.lstrip("/")).is_file()); self.assertFalse(frag); continue
                    idsets = self.ids_for(path)
                    self.assertIsNotNone(idsets, f"{path} is not a page of the site")
                    if frag: self.assertTrue(all(frag in ids for ids in idsets), f"#{frag} is not an id on {path or '/'}")
        self.assertGreaterEqual(checked, 12)

    def test_the_buy_link_in_the_launch_email_lands_on_the_price_section(self):
        self.assertIn("Buy: https://shotfleet.com/#price", read("marketing/launch-email.md"))
        for ids in self.index_ids(): self.assertIn("price", ids)
        section = re.search(r'<section[^>]*id="price"[^>]*>(.*?)</section>', INDEX_HTML, flags=re.S)
        self.assertIsNotNone(section); self.assertIn("launch price", plain(section.group(1)))  # it is the pricing section, not some other block

    def test_relative_links_in_the_readme_exist(self):
        for rel in ("README.md", "LAUNCH.md", "DISTRIBUTION.md"):
            for target in re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+)(?:#[^)]*)?\)", read(rel)):
                with self.subTest(file=rel, target=target): self.assertTrue((ROOT / target).exists(), target)

    def test_kit_addresses_point_at_the_site_or_at_a_guide_that_is_drafted_or_planned(self):
        drafts = {p.stem for p in (ROOT / "site/draft/guides").glob("*.html")}
        planned = set(re.findall(r"Slug: `/([a-z0-9-]+)`", read("marketing/articles/04-ideas.md")))  # articles not written yet; the kit says not to send those links before they exist
        unpublished = set()
        for rel in self.KIT:
            for path, frag in self.addresses(rel):
                with self.subTest(file=rel, url=path):
                    if path.startswith("/download/") or path in ("/install.sh",): continue
                    if self.ids_for(path) is not None: continue
                    slug = path.strip("/"); unpublished.add(slug)
                    self.assertIn(slug, drafts | planned, f"{rel}: {path} is neither a published page, a draft guide nor a planned article")
        self.assertTrue(unpublished)  # these 404 until the guides are published (see the register)


# --------------------------------------------------------------------------------------------------------------------- C077 to C084, C087
@unittest.skipIf(NODE is None, "node is not installed")
class WorkerBehaviour(unittest.TestCase):
    """The worker's own checks (site/worker.test.mjs), each looked up by name. The key-value store and the rate limiter are stand-ins
    that record what the worker asks of them; the real Cloudflare services are not run here."""
    @classmethod
    def setUpClass(cls):
        r = run_node("site/worker.test.mjs")
        cls.out = r.stdout + r.stderr; cls.code = r.returncode
        cls.ok = set(re.findall(r"^ok\s+(.*)$", r.stdout, flags=re.M))

    def has(self, *names):
        for n in names: self.assertIn(n, self.ok, f"worker check missing or failing: {n}")

    def test_the_whole_worker_suite_passes(self):
        self.assertEqual(self.code, 0, self.out[-2000:]); self.assertNotRegex(self.out, r"(?m)^FAIL")
        self.assertGreaterEqual(len(self.ok), 55)

    def test_c077_a_visit_adds_to_a_total_per_day_source_language_and_event_and_stores_nothing_else(self):
        self.has("visits are counted per day, source and language", "known events are kept, unknown ones count as a view", "source is sanitised",
                 "a visit stores nothing about the visitor", "a single visit below the batch size is still stored",
                 "one visit writes exactly one key, a day/source/language/event total",
                 "a visit key and value hold neither the IP address nor the user agent")

    def test_c078_only_three_kinds_of_record_exist_and_none_holds_the_ip_or_user_agent(self):
        self.has("a signup record holds exactly at, platform, stack, country, lang and ref",
                 "the signup record and key never hold the IP address or the user agent",
                 "a contact message is one msg: record holding exactly message, email and country",
                 "a contact message never holds the IP address or the user agent",
                 "the only kinds of key ever written are email:, msg: and hit:",
                 "the server's own log lines name the event and country, never the IP, user agent or an address")

    def test_c079_the_waitlist_record_has_the_listed_fields_and_never_the_ip(self):
        self.has("the signup record has the country, the language, the referrer verbatim, the stack and the date",
                 "the referrer is cut at 300 characters", "without a country the record says null, not a guess",
                 "the signup record and key never hold the IP address or the user agent")

    def test_c082_forget_removes_the_signup_and_the_messages_and_answers_the_same_either_way(self):
        self.has("forget removes the address from the list", "forget removes the messages left with that reply address",
                 "forget leaves other people's messages", "forget answers identically whether or not the address was on the list",
                 "forget with an address that is not an address is a 400 and deletes nothing")

    def test_c083_the_contact_form_stores_a_message_and_refuses_what_it_should(self):
        self.has("contact 200", "message stored with a lower-cased reply address", "contact without a reply address is fine", "contact too short 400",
                 "contact too long 400", "contact bad reply address 400", "contact honeypot is not stored",
                 "a message of exactly 2,000 characters is accepted", "a message of 1 character after trimming is refused",
                 "a body over 4,096 bytes is refused with 413", "a body that is not JSON is a 400",
                 "rate limited contact, forget and signup are all 429", "a rate limited request writes nothing")

    def test_c083_messages_can_be_read_with_signups_sh(self):
        sh = read("site/signups.sh")
        self.assertIn("msg:", sh); self.assertIn("messages", sh)  # the script lists the msg: records and prints each one

    def test_c084_the_limiter_is_keyed_by_ip_refuses_with_429_and_leaves_page_views_alone(self):
        self.has("rate limited 429", "rate limit does not block visit counting", "GET on an api route 405", "unknown path 404",
                 "the limiter is asked about the client IP address, once per request",
                 "page views are not rate limited, so they never reach the limiter")

    def test_c081_the_purge_step_exists_and_the_privacy_page_and_launch_checklist_agree(self):
        self.assertIn("I will delete the waitlist within 30 days after I send the launch email", read("site/public/privacy.html"))
        self.assertIn("--purge-waitlist", read("site/signups.sh")); self.assertIn("--purge-waitlist", read("LAUNCH.md"))
        self.assertRegex(read("LAUNCH.md"), r"30 days")
        self.assertNotIn("expirationTtl", read("site/worker.js"))  # nothing deletes by itself: the promise is a manual step


class WranglerConfig(unittest.TestCase):
    """site/wrangler.toml: the storage, the rate limit, and how unknown URLs are answered."""
    @classmethod
    def setUpClass(cls):
        try: import tomllib
        except ImportError: raise unittest.SkipTest("tomllib needs Python 3.11")
        cls.cfg = tomllib.loads(read("site/wrangler.toml"))

    def test_c084_the_list_lives_in_workers_kv_under_the_binding_the_worker_uses(self):
        kv = self.cfg["kv_namespaces"]
        self.assertEqual([k["binding"] for k in kv], ["WAITLIST"]); self.assertTrue(re.fullmatch(r"[0-9a-f]{32}", kv[0]["id"]))
        code = read("site/worker.js")
        self.assertIn("env.WAITLIST.put", code)
        self.assertEqual(set(re.findall(r"env\.([A-Z_]+)\b", code)) - {"HIT_BATCH", "FLUSH_MS", "ALERT", "ALERT_TO"}, {"WAITLIST", "LIMITER"})

    def test_c084_the_rate_limit_is_five_a_minute_per_ip_through_the_limiter_binding(self):
        rl = self.cfg["ratelimits"]
        self.assertEqual([(r["name"], r["simple"]["limit"], r["simple"]["period"]) for r in rl], [("LIMITER", 5, 60)])
        self.assertIn("env.LIMITER.limit({ key: ip })", read("site/worker.js"))
        self.assertIn('request.headers.get("cf-connecting-ip")', read("site/worker.js"))

    def test_c084_privacy_says_the_same_about_the_ip(self):
        text = plain(read("site/public/privacy.html"))
        self.assertIn("In Cloudflare Workers KV, the storage for the small server behind this page.", text)
        self.assertIn("Cloudflare also processes your IP address to serve the page and to limit how often the forms can be sent.", text)

    def test_c087_unknown_urls_get_the_404_page_and_only_the_api_reaches_the_worker(self):
        a = self.cfg["assets"]
        self.assertEqual(a["not_found_handling"], "404-page"); self.assertEqual(a["run_worker_first"], ["/api/*"])
        self.assertTrue((ROOT / "site" / a["directory"] / "404.html").is_file())

    def test_c087_the_404_page_says_there_is_no_page_here_and_drafts_are_outside_what_is_served(self):
        page = read("site/public/404.html")
        self.assertIn("There's no page here.", plain(page)); self.assertEqual(Page(page).h1, 1)
        self.assertRegex(page, r'<meta name="robots" content="noindex">')
        served = (ROOT / "site" / self.cfg["assets"]["directory"]).resolve()
        self.assertNotIn(served, (ROOT / "site/draft").resolve().parents)  # site/draft is not under the served folder
        self.assertEqual(list(served.rglob("draft*")), [])
        for p in served.rglob("*.html"): self.assertNotIn("the-button-nobody-could-reach", p.name)  # the unpublished guides are not in public/
        self.assertEqual(self.cfg["main"], "worker.js")
        self.assertNotIn("/404", read("site/worker.js"))  # the worker answers only /api/*; its own 404 is JSON, never the page

    def test_c087_the_pages_the_site_links_to_exist_and_the_draft_alternatives_page_is_not_the_published_one(self):
        self.assertTrue((PUB / "alternatives.html").is_file())
        self.assertNotEqual(read("site/draft/alternatives.html"), read("site/public/alternatives.html"))


class StackAnswers(unittest.TestCase):
    def test_every_option_of_the_what_do_you_build_with_question_is_a_stack_the_worker_keeps(self):
        # an option the worker does not know is silently dropped, so the answer would be lost
        options = set(re.findall(r'<option value="([a-z-]+)"', INDEX_HTML))
        stacks = set(re.findall(r'"([a-z-]+)"', re.search(r"const STACKS = new Set\(\[(.*?)\]\)", read("site/worker.js")).group(1)))
        self.assertTrue(options); self.assertLessEqual(options, stacks)


# --------------------------------------------------------------------------------------------------------------------- C078, C079
class PrivacyPageListsWhatIsStored(unittest.TestCase):
    PRIVACY = plain(read("site/public/privacy.html"))

    def test_c079_each_field_of_the_waitlist_record_is_named_on_the_page(self):
        for field, words in {"email": "Your email address.", "stack": "What you build with, if you answered the optional question.",
                             "country": "Your country, which Cloudflare works out from your IP address", "lang": "your browser's language. The IP address itself isn't stored.",
                             "ref": "The site that linked you here and any utm_ tags in the link", "at": "The date and time you joined."}.items():
            with self.subTest(field=field): self.assertIn(words, self.PRIVACY)
        self.assertIn("platform", read("site/worker.js"))  # derived from the stack answer, never asked or sent by the page
        self.assertNotIn("platform", read("site/public/forms.js"))

    def test_c078_the_contact_message_fields_are_named_on_the_page(self):
        self.assertIn("Messages you send through the contact form are kept until I've answered them, with the reply address if you gave one and your country", self.PRIVACY)
        self.assertIn("Beyond that, the only things stored are your analytics choice, in your own browser, and what you send when you join the waitlist or write to me.", self.PRIVACY)

    def test_c077_the_counter_is_described_as_the_code_does_it(self):
        self.assertIn("one to a running total for each page view and for a few actions (reaching the run or pricing section, clicking a button), split by day, by the site or link you came from, and by your browser's language.", self.PRIVACY)
        js = read("site/public/analytics.js"); code = re.sub(r"//.*", "", js)  # the comments say "cookie-free"; look at the code
        self.assertEqual(set(re.findall(r'\["(\w+)", "(\w+)"\]', js)), {("price", "pricing"), ("run", "runs")})
        self.assertEqual(sorted(re.findall(r"\b(?:send)\(\"(\w+)\"\)", js)), ["cta", "view"])
        for forbidden in ("cookie", "localStorage", "sessionStorage", "userAgent", "navigator."): self.assertNotIn(forbidden, code)
        self.assertEqual(re.findall(r"JSON\.stringify\((\{[^}]*\})\)", js), ["{ src: src, ev: ev }"])
        self.assertIn("/analytics.js", INDEX_HTML)
        for page in ("privacy.html", "terms.html", "alternatives.html", "docs.html"):
            self.assertNotIn("analytics.js", read("site/public/" + page), "the counter is the home page's only")
        self.assertNotIn("shotfleet-analytics", code)  # it does not read the consent choice: counted whether or not you accept


# --------------------------------------------------------------------------------------------------------------------- C077, C088 in a browser
@unittest.skipIf(NODE is None, "node is not installed")
class BrowserBehaviour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = run_node("tests/browser_site.cjs", timeout=300)
        if r.returncode == 77: raise unittest.SkipTest("Playwright or Chromium is not installed")
        cls.out = r.stdout + r.stderr; cls.code = r.returncode
        cls.ok = set(re.findall(r"^ok\s+(.*)$", r.stdout, flags=re.M))

    def has(self, *names):
        for n in names: self.assertIn(n, self.ok, f"browser check missing or failing: {n}\n{self.out[-1500:]}")

    def test_the_browser_run_passes(self):
        self.assertEqual(self.code, 0, self.out[-3000:]); self.assertNotRegex(self.out, r"(?m)^FAIL")

    @unittest.skipIf(LIVE, "the sale page has no waitlist form")
    def test_c088_signup_shows_you_are_on_the_list_then_the_optional_question(self):
        self.has("signup success shows You're on the list and hides the form", "signup sends one POST to /api/signup as JSON",
                 "the optional question is shown after the signup, not before",
                 "answering sends the same address with the stack and shows thanks",
                 "skipping the question costs nothing: the signup was already sent and an empty answer sends nothing more")

    @unittest.skipIf(LIVE, "the sale page has no waitlist form")
    def test_c088_errors_validation_and_the_honeypot(self):
        self.has("signup: 429 shows the server's own wait message", "signup: 500 without a message shows the generic retry text",
                 "signup: 400 shows the server's own text", "signup: a network failure shows the connection text",
                 "an empty or malformed address is stopped in the page with a message and no request",
                 "the hidden honeypot field is sent as website, so the server can drop it")

    @unittest.skipIf(LIVE, "the sale page has no waitlist form")
    def test_c079_the_page_sends_only_the_address_the_honeypot_and_the_referrer_host_with_utm_tags(self):
        self.has("signup sends exactly email, the honeypot as website, and the referrer with utm tags")

    @unittest.skipIf(LIVE, "the sale page has no waitlist form")
    def test_c077_the_counter_sends_only_src_and_ev_sets_no_cookie_and_runs_whatever_the_analytics_choice(self):
        for choice in ("declined", "undecided"):
            self.has(f"the counter sends a view with analytics {choice}", f"every counter call sends only src and ev, to /api/hit ({choice})",
                     f"views, reaching the run and pricing sections and a button click are each sent ({choice})",
                     f"the counter sets no cookie and loads nothing from another server ({choice})")
        self.has("without utm_source the source is the referring site's host")

    def test_c082_c083_the_privacy_page_forms_send_what_the_worker_expects(self):
        self.has("delete-my-email sends only the address to /api/forget and says Done", "a one-character message is stopped in the page",
                 "a malformed reply address is stopped in the page",
                 "the contact form sends message, reply address and honeypot to /api/contact and says Sent")


# --------------------------------------------------------------------------------------------------------------------- C104
class ComparisonTable(unittest.TestCase):
    """The cells about shotfleet itself, read from the published comparison table and the draft, against what the program does.
    What needs a device (capturing the real app) and what is about other tools (their pages, read by hand on 2026-10-02) is not tested here."""
    @staticmethod
    def rows(text):
        out = {}
        for tr in re.findall(r"<tr>(.*?)</tr>", text, flags=re.S):
            cells = [plain(c).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, flags=re.S)]
            if cells: out[cells[0]] = cells[1:]
        return out

    def test_the_shotfleet_row_of_the_published_table_reads_yes_yes_yes_both_and_the_real_price(self):
        table = self.rows(read("site/public/alternatives.html"))
        head = next(r for r in re.findall(r"<thead>(.*?)</thead>", read("site/public/alternatives.html"), flags=re.S))
        self.assertEqual([plain(c).strip() for c in re.findall(r"<th[^>]*>(.*?)</th>", head)][1:5],
                         ["Takes the screenshots from your running app", "One flow for every language", "Checks the language of the result", "iOS and Android"])
        row = table["shotfleet"]
        self.assertEqual(row[:4], ["Yes", "Yes", "Yes", "Both"])
        self.assertEqual(row[4], "$49 once ($29 for the first 100 buyers). Free: check and 2 languages in run")

    def test_the_draft_table_says_yes_to_five_things_and_each_is_a_command_or_option_the_program_has(self):
        table = self.rows(read("site/draft/alternatives.html"))
        self.assertEqual(table["shotfleet"][:5], ["Yes"] * 5)
        self.assertEqual(table["shotfleet"][5], "$49 once, $29 founder")
        self.assertIn("run", sf.COMMANDS); self.assertIn("check", sf.COMMANDS)
        parser_src = read("shotfleet.py")
        self.assertIn('p.add_argument("--parallel", type=int', parser_src)           # parallel capture
        self.assertIn('p.add_argument("--platform", choices=("ios", "android")', parser_src)  # Android support
        self.assertIn("ios_run", parser_src); self.assertIn("android_run", parser_src)

    def test_one_english_flow_becomes_a_flow_in_each_language_from_the_apps_own_strings(self):
        en = {"a": "Next", "b": "Start Training"}; de = {"a": "Weiter", "b": "Training starten"}; ja = {"a": "次へ", "b": "トレーニング開始"}
        flow = 'appId: x\n---\n- tapOn: "Next"\n- tapOn: "Start Training"\n'
        outs = {name: sf.translate_flow(flow, en, tr)[0] for name, tr in (("de", de), ("ja", ja))}
        self.assertIn("'Weiter'", outs["de"]); self.assertIn("'次へ'", outs["ja"]); self.assertNotEqual(outs["de"], outs["ja"])

    def test_check_finds_a_screenshot_in_the_wrong_language(self):
        import contextlib, io
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); shots = fixture(d)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = sf.cmd_check(shots, strings=STRINGS, report_dir=d / "rep", ocr_command="cat {image}.txt")
            report = json.loads((d / "rep/check.json").read_text())
        self.assertIn("el/2.png: shows en strings", out.getvalue()); self.assertNotEqual(code, 0)
        self.assertIn("2.png", json.dumps(report))

    def test_free_tier_in_the_price_cell_is_the_programs(self):
        self.assertEqual(sf.FREE_LANGUAGES, 2)


if __name__ == "__main__":
    unittest.main()
