"""shotfleet is free and open source (MIT) since 2026-11-11: no license check, no price, no free tier, GitHub Sponsors instead.

Run: python3 -m unittest tests.test_open_source
"""
import re, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

SITE = sorted((ROOT / "site/public").glob("*.html")) + sorted((ROOT / "site/public/guides").glob("*.html")) + [ROOT / "site/public/llms.txt"]
MONEY = re.compile(r"gumroad|\$(?:29|49)\b|\bbuy shotfleet\b|shotfleet activate", re.I)


class TheProgramHasNoPaywall(unittest.TestCase):
    def test_the_license_code_and_its_server_are_gone_from_the_program(self):
        text = (ROOT / "shotfleet.py").read_text()
        for gone in ("gumroad", "LICENCE_FILE", "LOCALE_CAP", "require_licence", "apply_free_tier", "NoLicence", "SHOTFLEET_KEY", "FREE_LANGUAGES"):
            self.assertNotIn(gone.lower(), text.lower(), gone)

    def test_activate_and_deactivate_are_not_commands(self):
        self.assertEqual(sf.COMMANDS, ("doctor", "mcp", "skill", "init", "run", "check", "export"))
        for cmd in ("activate", "deactivate"):
            r = subprocess.run([sys.executable, str(ROOT / "shotfleet.py"), cmd, "x"], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)

    def test_the_mcp_run_tool_does_not_mention_a_license(self):
        for tool in sf.MCP_TOOLS: self.assertNotRegex(tool["description"], r"(?i)licen[cs]e|2 languages")


class TheProjectIsOpenSource(unittest.TestCase):
    def test_the_license_is_mit_and_names_the_author(self):
        text = (ROOT / "LICENSE").read_text()
        self.assertTrue(text.startswith("MIT License"))
        self.assertIn("Permission is hereby granted, free of charge", text)
        self.assertIn("Manuel Lorenzo Parejo", text)

    def test_github_sponsors_is_set_up_for_the_repository(self):
        self.assertEqual((ROOT / ".github/FUNDING.yml").read_text().strip(), "github: noloman")

    def test_the_readme_the_site_and_the_contributing_guide_say_so_and_link_sponsors(self):
        for f in ("README.md", "site/public/index.html", "site/public/terms.html", "CONTRIBUTING.md"):
            text = (ROOT / f).read_text()
            self.assertIn("MIT", text, f)
            self.assertIn("https://github.com/sponsors/noloman", text, f)

    def test_no_page_of_the_site_sells_anything(self):
        for page in SITE:
            if page.name == "whats-new.html": continue  # the history of earlier versions stays
            text = page.read_text()
            self.assertIsNone(MONEY.search(text), f"{page.name}: {MONEY.search(text) and MONEY.search(text).group(0)}")

    def test_the_alternatives_page_lists_shotfleet_as_free(self):
        text = (ROOT / "site/public/alternatives.html").read_text()
        self.assertRegex(text, r"<th scope=\"row\">shotfleet</th>.*?<td>Free and open source \(MIT\)</td>")


if __name__ == "__main__":
    unittest.main()


class TabletImage(unittest.TestCase):
    """#109: a tablet avoids the API 37 image (its "app handle" and tooltip show in screenshots)."""
    def test_a_tablet_picks_an_older_image_and_an_emulator_named_after_it(self):
        import tempfile
        from pathlib import Path
        d = Path(tempfile.mkdtemp())
        for api in ("android-34", "android-37"):
            p = d / "system-images" / api / "google_apis" / sf.ABI; p.mkdir(parents=True); (p / "package.xml").write_text("x")
        old = sf.SDK; sf.SDK = d
        try:
            self.assertIn("android-34", sf.tablet_image({}, "tablet"))
            self.assertEqual(sf.android_avd_name({}, "tablet"), "shotfleet_android_tablet_api34")
            self.assertEqual(sf.android_avd_name({}, "phone"), "shotfleet_android")  # a phone keeps the newest
            self.assertIsNone(sf.tablet_image({"system_image": "x"}, "tablet"))  # the config's own choice wins
            self.assertEqual(sf.android_avd_name({"system_image": "x"}, "tablet"), "shotfleet_android_tablet")
        finally: sf.SDK = old
