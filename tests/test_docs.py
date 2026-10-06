"""The docs page (site/public/docs.html) and the guides generator (tools/build-guides.py), checked against the program. Stdlib only, no network.

Run: python3 -m unittest tests.test_docs
"""
import contextlib, html, importlib.util, io, json, re, sys, tempfile, tomllib, unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
import shotfleet as sf
from test_agent_skills import argv_of, parse  # the same real-parser helpers the agent skills' commands are tested with
from test_site import BANNED, PAGES, Page, resolve

PUB = ROOT / "site/public"
DOCS = (PUB / "docs.html").read_text()
EM_DASH = "—"

spec = importlib.util.spec_from_file_location("build_guides", ROOT / "tools/build-guides.py")
bg = importlib.util.module_from_spec(spec); spec.loader.exec_module(bg)


def tag(text, pattern):
    m = re.search(pattern, text)
    assert m, pattern
    return html.unescape(m.group(1))


def code_blocks(text):
    return [html.unescape(re.sub(r"<[^>]+>", "", b)) for b in re.findall(r"<pre><code[^>]*>(.*?)</code></pre>", text, re.S)]


def html_commands(text):
    """Every `shotfleet <command> ...` on a line of a code block (also `- run: shotfleet ...`) and every complete inline one."""
    found = []
    for block in code_blocks(text):
        for line in block.splitlines():
            m = re.match(r"^\s*(?:-\s*)?(?:run:\s*)?(shotfleet .+)$", line)
            if m: found.append(m.group(1))
    plain = re.sub(r"<pre>.*?</pre>", "", text, flags=re.S)
    for c in re.findall(r"<code>(shotfleet [^<]+)</code>", plain):
        c, parts = html.unescape(c), html.unescape(c).split()
        if parts[1] in sf.COMMANDS and "..." not in c and "|" not in c and (len(parts) > 2 or parts[1] in ("run", "doctor")): found.append(c)
    return found


class DocsPage(unittest.TestCase):
    page = Page(DOCS)

    def test_it_parses_has_one_h1_and_is_in_the_pages_the_site_tests_cover(self):
        self.assertEqual(self.page.h1, 1)
        self.assertIn("docs.html", [p.name for p in PAGES])
        self.assertEqual(self.page.external, [])
        self.assertEqual(self.page.handlers, [])

    def test_head_matches_the_other_pages_pattern(self):
        self.assertEqual(tag(DOCS, r'<link rel="canonical" href="([^"]+)"'), "https://shotfleet.com/docs")
        self.assertEqual(tag(DOCS, r'property="og:url" content="([^"]+)"'), "https://shotfleet.com/docs")
        for prop in ("og:title", "og:description", "og:image", "og:type", "og:site_name"): self.assertIn(f'property="{prop}"', DOCS)
        self.assertIn('<link rel="stylesheet" href="/site.css">', DOCS)
        self.assertIn('<nav class="pill" aria-label="Main">', DOCS)
        self.assertIn("<footer>", DOCS)

    def test_title_and_description_lengths_and_uniqueness(self):
        title, desc = tag(DOCS, r"<title>(.*?)</title>"), tag(DOCS, r'<meta name="description" content="([^"]*)"')
        self.assertLessEqual(len(title), 60, title)
        self.assertLessEqual(len(desc), 160, desc)
        self.assertGreaterEqual(len(desc), 70)
        self.assertEqual(tag(DOCS, r'property="og:title" content="([^"]*)"'), title)
        for p in PAGES:
            if p.name != "docs.html":
                other = p.read_text()
                self.assertNotEqual(re.findall(r"<title>(.*?)</title>", other), [title], p.name)
                self.assertNotIn(f'name="description" content="{html.escape(desc)}"', other, p.name)

    def test_every_anchor_resolves_and_every_section_is_in_the_table_of_contents(self):
        ids = re.findall(r'\bid="([^"]+)"', DOCS)
        self.assertEqual(len(ids), len(set(ids)), "duplicate ids")
        toc = re.search(r'<nav class="toc".*?</nav>', DOCS, re.S).group(0)
        toc_ids = re.findall(r'href="#([^"]+)"', toc)
        self.assertGreaterEqual(len(toc_ids), 10)
        for frag in re.findall(r'href="#([^"]+)"', DOCS): self.assertIn(frag, ids, f"#{frag} points at nothing")
        for h2 in re.findall(r'<h2 id="([^"]+)"', DOCS): self.assertIn(h2, toc_ids, f"section {h2} is not in the table of contents")

    def test_local_links_resolve(self):
        for tag_, attr, ref in self.page.refs:
            self.assertTrue(resolve(ref, self.page.ids), f"<{tag_} {attr}={ref!r}> points at nothing")

    def test_last_checked_line_names_this_version_and_a_date(self):
        m = re.search(r"Last checked against version ([\d.]+) on (\d{4}-\d\d-\d\d)\.", DOCS)
        self.assertTrue(m)
        self.assertEqual(m.group(1), sf.VERSION)
        date.fromisoformat(m.group(2))

    def test_no_em_dash_and_no_banned_phrase(self):
        for name in ("docs.html", "llms.txt", "sitemap.xml"):
            text = (PUB / name).read_text()
            self.assertNotIn(EM_DASH, text, name)
        for phrase in BANNED: self.assertNotIn(phrase, DOCS.lower())
        self.assertNotIn("<!--", re.sub(r"<!-- DOCKER-PENDING.*?DOCKER-PENDING -->", "", DOCS, flags=re.S))  # only the parked Linux image text (test_site DockerPending)

    def test_it_is_in_the_sitemap_and_in_llms_txt_once(self):
        self.assertIn("<loc>https://shotfleet.com/docs</loc>", (PUB / "sitemap.xml").read_text())
        self.assertEqual((PUB / "llms.txt").read_text().count("](https://shotfleet.com/docs)"), 1)

    def test_every_shotfleet_command_parses_with_the_real_parser(self):
        cmds = html_commands(DOCS)
        self.assertGreaterEqual(len(cmds), 18)
        for cmd in cmds:
            with self.subTest(cmd=cmd):
                argv = argv_of(cmd)
                try: ns = parse(argv)
                except SystemExit as e: self.fail(f"argparse refused: {cmd!r} (exit {e.code})")
                self.assertEqual(ns.cmd, argv[0])
        for needed in ("init", "run", "check", "export", "skill", "activate", "doctor"):
            self.assertTrue(any(c.split()[1] == needed for c in cmds), f"no `shotfleet {needed}` example")

    def test_every_config_key_listed_exists_and_every_toml_example_is_accepted(self):
        table = re.search(r"<table>.*?</table>", DOCS, re.S).group(0)
        rows = [(k, set(re.split(r",\s*", s))) for k, s in re.findall(r"<tr><td><code>(\w+)</code></td><td>([^<]+)</td>", table)]
        self.assertGreaterEqual(len(rows), 12)
        for key, sections in rows:
            self.assertTrue(sections <= {"ios", "android"}, key)
            for section in sections: self.assertIn(key, {**sf.KEYS["common"], **sf.KEYS[section]}, f"{key} is not a {section} key")
        listed = {k for k, _ in rows}
        self.assertTrue({"app", "apk", "flow", "out", "parallel", "locales", "base_locale", "strings", "device_types", "devices"} <= listed)
        blocks = 0
        for block in code_blocks(DOCS):
            first = next((l for l in block.splitlines() if l.strip()), "")
            if first.startswith("["):
                docs = [tomllib.loads(block)]
            elif first.startswith("strings ="):
                docs = [tomllib.loads(l) for l in block.splitlines() if l.startswith("strings =")]
            else: continue
            blocks += 1
            for doc in docs:
                if "strings" in doc: self.assertIn("strings", sf.KEYS["common"])
                else: sf.check_tables(doc, "docs.html")  # raises Fail on an unknown table, hook event or bad type
                for section in ("ios", "android"):
                    for key in doc.get(section, {}): self.assertIn(key, {**sf.KEYS["common"], **sf.KEYS[section]}, key)
        self.assertGreaterEqual(blocks, 6)

    def test_hooks_variables_and_events_match_the_code(self):
        for event in sf.HOOK_EVENTS: self.assertIn(event, DOCS)
        for name in ("SHOTFLEET_EVENT", "SHOTFLEET_PLATFORM", "SHOTFLEET_PROBLEMS", "SHOTFLEET_FASTLANE", "SHOTFLEET_KEY", "SHOTFLEET_OCR"):
            self.assertIn(name, DOCS)
            self.assertIn(name.removeprefix("SHOTFLEET_"), (ROOT / "shotfleet.py").read_text().upper())
        for code in ("0", "1", "2", "130"): self.assertRegex(DOCS, rf"<code>{code}</code> ")

    def test_it_does_not_promise_an_upload_or_a_price(self):
        self.assertIn("uploads nothing to a store", DOCS)
        self.assertNotRegex(DOCS, r"\$\d")  # prices live on the home page and in /terms


SAMPLE = """# A title

First *paragraph* with `code_with_underscores`, **bold** and a [link](https://example.com/a?b=1&c=2).
Second line of the same paragraph.

## List and code

- one
- two `x < y`
  continued

1. first
2. second

```bash
shotfleet check <dir> && echo "a < b"
```

| a | b |
|---|---|
| 1 | `2` |

![alt text](https://shotfleet.com/img/x.jpg)

[bad](javascript:alert(1)) <script>alert(1)</script>

---
"""


def article(title, slug, items):
    return f"""# Article: {title}

Status: draft.

| Field | Value |
|---|---|
| Title (H1) | {title} |
| Meta description (under 160 chars) | About {title}. |
| Slug | `/{slug}` |

{items}

---

# {title}

Body of {title}.
"""


VERIFIED = "## TO VERIFY BEFORE PUBLISHING\n\n1. Thing one. TICKED 2026-10-02.\n2. Thing two. TICKED 2026-10-02.\n\nSources used:\n- https://example.com\n"
UNVERIFIED = "## TO VERIFY BEFORE PUBLISHING\n\n1. Thing one. TICKED 2026-10-02.\n2. Thing two, still open.\n"


class Renderer(unittest.TestCase):
    def setUp(self): self.out = bg.render_markdown(SAMPLE)

    def test_blocks(self):
        for expected in ("<h1>A title</h1>", "<h2>List and code</h2>", "<ul><li>one</li><li>two <code>x &lt; y</code> continued</li></ul>",
                         "<ol><li>first</li><li>second</li></ol>", "<hr>"):
            self.assertIn(expected, self.out)
        self.assertIn('<pre><code class="language-bash">shotfleet check &lt;dir&gt; &amp;&amp; echo "a &lt; b"</code></pre>', self.out)
        self.assertIn("<thead><tr><th scope=\"col\">a</th><th scope=\"col\">b</th></tr></thead><tbody><tr><td>1</td><td><code>2</code></td></tr></tbody>", self.out)

    def test_inline(self):
        self.assertIn("<em>paragraph</em>", self.out)
        self.assertIn("<code>code_with_underscores</code>", self.out)
        self.assertIn("<strong>bold</strong>", self.out)
        self.assertIn('<a href="https://example.com/a?b=1&amp;c=2">link</a>', self.out)
        self.assertEqual(self.out.count("<p>First"), 1)  # two source lines, one paragraph
        self.assertIn('<img src="/img/x.jpg" alt="alt text" loading="lazy">', self.out)  # our own absolute URLs become site-relative

    def test_html_in_the_source_is_escaped_and_only_safe_links_are_made(self):
        self.assertNotIn("<script>", self.out)
        self.assertIn("&lt;script&gt;", self.out)
        self.assertNotIn('href="javascript', self.out)

    def test_the_real_articles_render_without_leftovers(self):
        for a in self.articles():
            body = bg.render_markdown(a["body"])
            for leftover in ("```", "**", "\0", "](http"): self.assertNotIn(leftover, body, a["slug"])
            self.assertGreater(body.count("<p>"), 5)

    @staticmethod
    def articles():
        found = [a for p in sorted((ROOT / "marketing/articles").glob("[0-9][0-9]-*.md")) if (a := bg.parse_article(p))]
        assert len(found) == 3, [a["slug"] for a in found]  # 04-ideas.md has no Slug row and is skipped
        return found


class Generator(unittest.TestCase):
    def make_root(self, d):
        root = Path(d)
        (root / "marketing/articles").mkdir(parents=True); (root / "site/public").mkdir(parents=True)
        (root / "site/public/sitemap.xml").write_text('<urlset>\n  <url><loc>https://shotfleet.com/</loc></url>\n</urlset>\n')
        (root / "marketing/articles/01-good.md").write_text(article("A good guide", "good-guide", VERIFIED))
        (root / "marketing/articles/02-open.md").write_text(article("An open guide", "open-guide", UNVERIFIED))
        (root / "marketing/articles/03-ideas.md").write_text("# Ideas\n\n---\n\nNo slug row here.\n")
        return root

    def run_build(self, root, **kw):
        out, err = io.StringIO(), io.StringIO()
        return bg.build(root, out=out, err=err, today=date(2026, 11, 1), **kw), out.getvalue(), err.getvalue()

    def test_open_items(self):
        self.assertEqual(bg.open_items(VERIFIED), [])
        self.assertEqual(len(bg.open_items(UNVERIFIED)), 1)
        self.assertEqual(len(bg.open_items("## TO VERIFY BEFORE PUBLISHING\n\n1. PARTLY TICKED (code read, not run).\n2. A thing.\n")), 2)
        self.assertEqual(len(bg.open_items("## TO VERIFY BEFORE PUBLISHING\n\nnothing listed\n")), 1)  # an empty list is not a checked list
        self.assertEqual(bg.open_items("no list at all"), [])

    def test_drafts_are_written_and_nothing_is_published_without_the_flag(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.make_root(d)
            code, out, err = self.run_build(root)
            self.assertEqual(code, 0)
            self.assertEqual(sorted(p.name for p in (root / "site/draft/guides").iterdir()), ["good-guide.html", "index.html", "open-guide.html"])
            self.assertFalse((root / "site/public/guides").exists())
            self.assertIn(bg.PLACEHOLDER, (root / "site/draft/guides/good-guide.html").read_text())
            self.assertNotIn("guides", (root / "site/public/sitemap.xml").read_text())

    def test_publish_refuses_unverified_articles_and_publishes_verified_ones(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.make_root(d)
            code, out, err = self.run_build(root, publish=True)
            self.assertEqual(code, 1)
            self.assertIn("refused open-guide", err)
            pub = root / "site/public/guides"
            self.assertEqual(sorted(p.name for p in pub.iterdir()), ["good-guide.html", "index.html"])
            self.assertNotIn("open-guide", (pub / "index.html").read_text())
            page = (pub / "good-guide.html").read_text()
            self.assertIn('"datePublished": "2026-11-01"', page)
            self.assertNotIn(bg.PLACEHOLDER, page)
            self.assertIn('<link rel="canonical" href="https://shotfleet.com/guides/good-guide">', page)
            sitemap = (root / "site/public/sitemap.xml").read_text()
            self.assertIn("<loc>https://shotfleet.com/guides/good-guide</loc>", sitemap)
            self.assertIn("<loc>https://shotfleet.com/guides</loc>", sitemap)
            self.assertNotIn("open-guide", sitemap)
            self.run_build(root, publish=True)  # idempotent
            self.assertEqual(sitemap, (root / "site/public/sitemap.xml").read_text())

    def test_nothing_unverified_is_published_when_every_article_is_open(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.make_root(d)
            (root / "marketing/articles/01-good.md").write_text(article("A good guide", "good-guide", UNVERIFIED))
            code, out, err = self.run_build(root, publish=True)
            self.assertEqual(code, 1)
            self.assertFalse((root / "site/public/guides").exists())
            self.assertNotIn("guides", (root / "site/public/sitemap.xml").read_text())

    def test_publish_unverified_publishes_everything(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.make_root(d)
            code, out, err = self.run_build(root, publish=True, unverified=True)
            self.assertEqual(code, 0)
            self.assertEqual(sorted(p.name for p in (root / "site/public/guides").iterdir()), ["good-guide.html", "index.html", "open-guide.html"])

    def test_a_description_over_160_characters_is_refused_even_when_verified(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.make_root(d)
            long = article("A good guide", "good-guide", VERIFIED).replace("About A good guide.", "x" * 161)
            (root / "marketing/articles/01-good.md").write_text(long)
            code, out, err = self.run_build(root, publish=True, unverified=True)
            self.assertEqual(code, 1)
            self.assertIn("161 characters", err)
            self.assertFalse((root / "site/public/guides/good-guide.html").exists())
            self.assertTrue((root / "site/public/guides/open-guide.html").exists())

    def test_the_cli_flags(self):
        with contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit):
            bg.main(["--help"])
        self.assertIn("wrangler dev", out.getvalue())
        self.assertIn("/guides/<slug>", out.getvalue())
        self.assertIn("--publish-unverified", out.getvalue())

    def test_the_real_unverified_articles_are_not_on_the_site(self):
        for a in Renderer.articles():
            if a["open_items"]:
                self.assertFalse((PUB / "guides" / f"{a['slug']}.html").exists(), f"{a['slug']} is published with unticked TO VERIFY items")
                self.assertNotIn(f"/guides/{a['slug']}", (PUB / "sitemap.xml").read_text())

    def test_the_real_drafts_are_well_formed_pages(self):
        for a in Renderer.articles():
            text = bg.article_page(a, bg.PLACEHOLDER)
            page = Page(text)
            self.assertEqual(page.h1, 1, a["slug"])
            self.assertEqual(page.inline_scripts, [])
            self.assertNotIn(EM_DASH, text, a["slug"])
            self.assertTrue(a["title"] and a["description"] and re.fullmatch(r"[a-z0-9-]+", a["slug"]), a["slug"])
            self.assertEqual(tag(text, r'<link rel="canonical" href="([^"]+)"'), f"https://shotfleet.com/guides/{a['slug']}")
            ld = json.loads(re.search(r'<script type="application/ld\+json">\n(.*?)\n</script>', text, re.S).group(1))
            self.assertEqual((ld["@type"], ld["headline"], ld["author"]["name"], ld["datePublished"]), ("Article", a["title"], "Manuel Lorenzo Parejo", bg.PLACEHOLDER))
            self.assertEqual(set(ld), {"@context", "@type", "headline", "description", "author", "datePublished", "mainEntityOfPage"})  # honest fields only
            for tag_, attr, ref in page.refs:
                if ref.startswith("/") and not ref.startswith("//") and tag_ != "a": self.assertTrue(resolve(ref, page.ids), f"{a['slug']}: {ref}")

    def test_guide_pages_share_the_docs_pages_nav_and_footer(self):
        a = Renderer.articles()[0]
        text = bg.article_page(a, bg.PLACEHOLDER)
        for block in (r"<header class=\"top\">.*?</header>", r"<footer>.*?</footer>"):
            self.assertEqual(re.search(block, text, re.S).group(0), re.search(block, DOCS, re.S).group(0))
        hub = bg.hub_page(Renderer.articles(), True)
        self.assertEqual(Page(hub).h1, 1)
        for x in Renderer.articles(): self.assertIn(f'href="/guides/{x["slug"]}"', hub)


if __name__ == "__main__":
    unittest.main()
