"""The agent skills (skill/), the paste-in block (docs/AGENTS-snippet.md) and site/public/llms.txt, checked against the program.

Stdlib only, no network. Run: python3 -m unittest tests.test_agent_skills
"""
import ast, contextlib, io, json, re, shlex, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tests"))
import shotfleet as sf
from test_cli_claims import fixture, fake_vision, run_main  # the same fixture, stubbed text recognition and runner the README's promises are tested with

SKILLS = sorted(p.parent for p in (ROOT / "skill").glob("*/SKILL.md"))
DOCS = sorted((ROOT / "skill").rglob("*.md")) + [ROOT / "docs/AGENTS-snippet.md"]
LLMS = (ROOT / "site/public/llms.txt").read_text()
INDEX = (ROOT / "site/public/index.html").read_text()
SOURCE = (ROOT / "shotfleet.py").read_text()
EM_DASH = "—"
BANNED = ["works with every", "works with any app", "guarantee", "universal binary", "tested on sample projects",
          "brew install noloman/shotfleet", "ai-powered", "first 100 people", "before anyone else"]


def frontmatter(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    return dict(l.split(": ", 1) for l in m.group(1).splitlines() if ": " in l)


def parse(argv):
    """The namespace the real argparse parser of shotfleet.py builds for these arguments (nothing runs)."""
    seen = []
    with mock.patch.object(sf, "main_cmd", side_effect=lambda a: seen.append(a) or 0), mock.patch.object(sf.shutil, "which", return_value=None), \
         mock.patch.object(sf, "LAST_REPORT", None), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        sf.main(argv)
    return seen[0]


def commands(path):
    """Every `shotfleet <command> ...` in code fences (also `- run: shotfleet ...` in YAML) and every complete inline one."""
    text, found = path.read_text(), []
    for block in re.findall(r"```[a-z]*\n(.*?)```", text, re.S):
        for line in block.splitlines():
            line = line.strip()
            m = re.match(r"^(?:-\s*)?(?:run:\s*)?(shotfleet .+)$", line)
            if m: found.append(m.group(1))
    for c in re.findall(r"`(shotfleet [^`]+)`", text):
        parts = c.split()
        if parts[1] in sf.COMMANDS and "..." not in c and "|" not in c and (len(parts) > 2 or parts[1] in ("run", "doctor")):
            found.append(c)
    return found


def argv_of(cmd):
    cmd = re.sub(r"<[^>]*>", "x", cmd)          # <dir>, <MyApp.app | app.apk>, <fastlane-dir>: sample values
    cmd = re.sub(r"\s+2?>\s*\S+", "", cmd)      # redirections such as > check.json
    return shlex.split(cmd, comments=True)[1:]


class Layout(unittest.TestCase):
    def test_the_three_skills_exist(self):
        self.assertEqual([p.name for p in SKILLS], ["shotfleet", "shotfleet-ci", "shotfleet-review"])

    def test_frontmatter_is_valid(self):
        for d in SKILLS:
            with self.subTest(skill=d.name):
                fm = frontmatter(d / "SKILL.md")
                self.assertEqual(set(fm), {"name", "description"})
                self.assertEqual(fm["name"], d.name)
                self.assertTrue(re.fullmatch(r"[a-z0-9-]+", fm["name"]))
                self.assertTrue(fm["description"].strip())
                self.assertLess(len(fm["description"]), 1024)
                self.assertIn("Use when", fm["description"])  # the trigger phrases an agent matches on
                self.assertNotIn("<", fm["description"])

    def test_skill_files_are_short(self):
        for d in SKILLS:
            lines = len((d / "SKILL.md").read_text().splitlines())
            self.assertLess(lines, 250, d.name)
        self.assertLess(len((ROOT / "skill/shotfleet/SKILL.md").read_text().splitlines()), 200)

    def test_references_exist_and_every_link_resolves(self):
        refs = ["troubleshooting.md", "flow-writing.md", "config.md", "ci.md", "licence.md"]
        self.assertEqual(sorted(p.name for p in (ROOT / "skill/shotfleet/references").glob("*.md")), sorted(refs))
        main = (ROOT / "skill/shotfleet/SKILL.md").read_text()
        for r in refs: self.assertIn(f"references/{r}", main, f"SKILL.md never points at {r}")
        for doc in DOCS:
            for target in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
                if target.startswith(("http", "#")): continue
                with self.subTest(doc=doc.name, target=target):
                    self.assertTrue((doc.parent / target.split("#")[0]).exists())

    def test_no_em_dash_and_no_banned_phrase(self):
        for p in [*DOCS, ROOT / "site/public/llms.txt"]:
            text = p.read_text()
            self.assertNotIn(EM_DASH, text, p.name)
            for phrase in BANNED: self.assertNotIn(phrase, text.lower(), f"{p.name} says {phrase!r}")

    def test_this_file_needs_no_network(self):
        mine = ast.parse(Path(__file__).read_text())
        names = {a.name.split(".")[0] for n in ast.walk(mine) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(mine) if isinstance(n, ast.ImportFrom)}
        self.assertFalse(names & {"socket", "ssl", "urllib", "http", "requests", "httpx"}, names)


class Commands(unittest.TestCase):
    def test_every_documented_command_parses_with_the_real_parser(self):
        total = 0
        for doc in DOCS:
            for cmd in commands(doc):
                total += 1
                with self.subTest(doc=doc.name, cmd=cmd):
                    argv = argv_of(cmd)
                    try: ns = parse(argv)
                    except SystemExit as e: self.fail(f"argparse refused: {cmd!r} (exit {e.code})")
                    self.assertEqual(ns.cmd, argv[0])
        self.assertGreaterEqual(total, 25)

    def test_the_install_command_exists_installs_every_skill_and_keeps_what_is_there(self):
        import tempfile, contextlib, io
        self.assertIn("skill", sf.COMMANDS)
        self.assertIn("shotfleet skill install", (ROOT / "skill/README.md").read_text())
        names = sorted(p.name for p in (ROOT / "skill").iterdir() if (p / "SKILL.md").is_file())
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sf.main(["skill", "install", "--dir", d]), 0)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), names)
            (Path(d) / names[0] / "SKILL.md").write_text("mine")
            sf.main(["skill", "install", "--dir", d])
            self.assertEqual((Path(d) / names[0] / "SKILL.md").read_text(), "mine")  # not overwritten without --force
            sf.main(["skill", "install", "--dir", d, "--force"])
            self.assertNotEqual((Path(d) / names[0] / "SKILL.md").read_text(), "mine")
        self.assertIn("kept", out.getvalue())

    def install(self, *args):
        """`shotfleet skill install ...` with HOME and the working folder in a temp dir; never the real home folder."""
        import os, shutil
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        home, proj = d / "home", d / "proj"; home.mkdir(); proj.mkdir()
        self.addCleanup(os.chdir, os.getcwd()); os.chdir(proj)
        env = mock.patch.dict(os.environ, {"HOME": str(home)}); env.start(); self.addCleanup(env.stop)
        self.assertEqual(Path.home(), home)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sf.main(["skill", "install", *args]), 0)
        return home, proj, out.getvalue()

    def test_install_writes_the_claude_and_the_shared_agents_folder(self):
        names = [p.name for p in SKILLS]
        home, proj, out = self.install()
        for folder in (".claude/skills", ".agents/skills"):
            with self.subTest(folder=folder):
                self.assertEqual(sorted(p.name for p in (home / folder).iterdir()), names)
                self.assertFalse((proj / folder).exists())
        lines = out.splitlines()
        self.assertEqual(len(lines), 2, out)  # one line per folder
        self.assertTrue(lines[0].startswith(f"{home / '.claude/skills'} (Claude Code, Cursor): installed "), out)
        self.assertTrue(lines[1].startswith(f"{home / '.agents/skills'} (Codex, Gemini CLI, Copilot, Cursor): installed "), out)

    def test_project_writes_both_folders_in_the_project(self):
        names = [p.name for p in SKILLS]
        home, proj, out = self.install("--project")
        for folder in (".claude/skills", ".agents/skills"):
            with self.subTest(folder=folder):
                self.assertEqual(sorted(p.name for p in (proj / folder).iterdir()), names)
                self.assertFalse((home / folder).exists())
        self.assertEqual(len(out.splitlines()), 2, out)

    def test_each_folder_keeps_its_own_copy_without_force(self):
        home, proj, _ = self.install()
        (home / ".agents/skills/shotfleet/SKILL.md").write_text("mine")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            sf.main(["skill", "install"])
        self.assertEqual((home / ".agents/skills/shotfleet/SKILL.md").read_text(), "mine")
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines: self.assertIn(": kept shotfleet, shotfleet-ci, shotfleet-review (already there; --force replaces it)", line)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            sf.main(["skill", "install", "--force"])
        self.assertNotEqual((home / ".agents/skills/shotfleet/SKILL.md").read_text(), "mine")
        self.assertNotIn("kept", out.getvalue())

    def test_dir_writes_only_that_folder(self):
        home, proj, out = self.install("--dir", "custom")
        self.assertTrue((proj / "custom/shotfleet/SKILL.md").is_file())
        self.assertFalse((home / ".claude").exists() or (home / ".agents").exists())
        self.assertEqual(len(out.splitlines()), 1, out)

    def test_the_agents_snippet_names_the_six_commands(self):
        snippet = (ROOT / "docs/AGENTS-snippet.md").read_text()
        for c in ("doctor", "init", "run", "check", "export", "activate"):
            self.assertIn(f"`shotfleet {c}", snippet)


class AgainstTheProgram(unittest.TestCase):
    def test_json_keys_in_the_skill_are_the_ones_check_prints(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); shots = fixture(d)
            with fake_vision():  # the keys, not the reader: real Vision is test_cli_claims.RealVisionSmoke's job
                code, out, err = run_main("check", str(shots), "--strings", str(d / "locales/*/translation.json"),
                                          "--ocr-command", "cat {image}.txt", "--report", str(d / "rep"), "--json")
        report = json.loads(out)
        self.assertEqual(set(report), {"exit", "screenshots", "problems", "notes", "unverified"})
        self.assertEqual(set(report["screenshots"][0]), {"file", "src", "sha", "lang", "chars", "evidence"})
        skill = (ROOT / "skill/shotfleet/SKILL.md").read_text()
        for key in [*report, *report["screenshots"][0]]: self.assertIn(f'"{key}"', skill)
        for key in ("exit", "exported", "skipped"): self.assertIn(f'"{key}"', skill)

    def test_problem_lines_the_review_skill_explains_exist_in_the_program(self):
        review = (ROOT / "skill/shotfleet-review/SKILL.md").read_text()
        source = SOURCE.replace('\\"', '"')  # the program writes 6.9" inside a double-quoted string
        for fragment in ("strings (", "more than", "text looks like", "the caption is in", "identical image in", ": missing ",
                         "so this listing shows another language", "no text found (blank or still loading?)",
                         "has transparency (an alpha channel); both stores reject it", "isn't an App Store screenshot size",
                         "is outside Google Play's 320-3840 px", "the App Store takes at most 10", "Google Play takes at most 8",
                         'need a 6.9" or 6.5" set', 'the app runs on iPad, so the App Store requires 13" iPad screenshots'):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, source)
                self.assertIn(fragment.strip(": "), review)

    def test_every_troubleshooting_message_is_in_the_program(self):
        text = (ROOT / "skill/shotfleet/references/troubleshooting.md").read_text()
        fragments = re.findall(r"^\| `([^`]+)` \|", text, re.M)
        self.assertGreaterEqual(len(fragments), 60)
        for f in fragments:
            with self.subTest(fragment=f):
                self.assertIn(f, SOURCE)

    def test_config_md_lists_every_key_table_and_hook_event(self):
        text = (ROOT / "skill/shotfleet/references/config.md").read_text()
        for k in sorted({k for table in sf.KEYS.values() for k in table}):
            with self.subTest(key=k): self.assertIn(f"`{k}`", text)
        for k in (*sf.HOOK_EVENTS, "hook_timeout_s"):
            with self.subTest(hook=k): self.assertIn(k, text)
        for table in sf.TABLES: self.assertIn(f"[{table}", text)
        for table in ("ios", "android"):
            for k in sf.REQUIRED[table]: self.assertRegex(text, rf"`{k}` \(required\)")

    def test_environment_variables_named_in_the_docs_exist_in_the_program(self):
        for doc in DOCS:
            for var in set(re.findall(r"SHOTFLEET_[A-Z_]+", doc.read_text())):
                with self.subTest(doc=doc.name, var=var):
                    self.assertIn(var, SOURCE)

    def test_exit_codes_and_the_free_tier_match_the_program(self):
        self.assertEqual(sf.FREE_LANGUAGES, 2)
        self.assertIn("2 languages", (ROOT / "skill/shotfleet/references/licence.md").read_text())
        for p in ("skill/shotfleet/SKILL.md", "skill/shotfleet-ci/SKILL.md", "docs/AGENTS-snippet.md"):
            text = (ROOT / p).read_text()
            for code in ("130", "2", "1", "0"): self.assertRegex(text, rf"\b{code}\b", p)
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "LAST_REPORT", None):  # exit 2: only `exit` in the JSON
            code, out, err = run_main("check", str(Path(d) / "nope"), "--json")
        self.assertEqual((code, json.loads(out)), (2, {"exit": 2}))
        self.assertIn("shotfleet: no folder at", err)

    def test_the_config_the_skill_shows_is_accepted_by_the_config_checker(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            doc = {"ios": {"app": "x.app", "strings": "lib/l10n/*.arb", "parallel": 4, "device_types": ["iPhone 17 Pro Max"]},
                   "android": {"apk": "x.apk", "devices": ["phone", "tablet"]},
                   "hooks": {"before_run": "true", "hook_timeout_s": 5}, "overrides": {"tr": {"Next": "Ileri"}}}
            sf.check_tables(doc, "shotfleet.toml")  # raises Fail on a typo; the keys in config.md are the ones it knows
        for table in ("ios", "android"):
            for k in doc[table]: self.assertIn(k, {**sf.KEYS["common"], **sf.KEYS[table]})


class LlmsTxt(unittest.TestCase):
    def test_only_prices_that_match_the_site(self):
        prices = set(re.findall(r"\$(\d+)", LLMS))
        self.assertEqual(prices, set(re.findall(r"\$(\d+)", INDEX)))
        self.assertEqual(prices, {"29", "49"})
        self.assertIn("first 100 buyers", LLMS)
        self.assertIn(f"up to {sf.FREE_LANGUAGES} languages", LLMS)
        self.assertIn("14-day refund", LLMS)

    def test_links_are_the_site_pages_and_they_exist(self):
        links = re.findall(r"\]\((https?://[^)]+)\)", LLMS)
        self.assertEqual(links, ["https://shotfleet.com/", "https://shotfleet.com/docs", "https://shotfleet.com/whats-new", "https://shotfleet.com/demo", "https://shotfleet.com/alternatives", "https://shotfleet.com/terms",
                                 "https://shotfleet.com/privacy"])
        sitemap = (ROOT / "site/public/sitemap.xml").read_text()
        for url in links:
            self.assertIn(f"<loc>{url}</loc>", sitemap)
            page = url.removeprefix("https://shotfleet.com").strip("/") or "index"
            self.assertTrue((ROOT / f"site/public/{page}.html").is_file(), url)

    def test_requirements_match_the_readme(self):
        readme = (ROOT / "README.md").read_text()
        for fact in ("Apple silicon", "Java 17+"):
            self.assertIn(fact, readme)
            self.assertIn(fact, LLMS)
        self.assertIn("Maestro (tested with 2.0.10 and 2.11.0)", readme)
        self.assertIn("Maestro", LLMS)
        self.assertTrue(LLMS.startswith("# shotfleet\n\n> "))

    def test_it_does_not_promise_an_upload_or_a_live_sale(self):
        self.assertIn("never uploads", LLMS)
        self.assertNotIn("buy now", LLMS.lower())


if __name__ == "__main__":
    unittest.main()
