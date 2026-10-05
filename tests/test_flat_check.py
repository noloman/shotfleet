"""`check` on a flat folder of PNGs (a hand-made single-language set): needs --locale, says so without it.
No device, no real OCR: the readers are fakes.

Run: python3 -m unittest tests.test_flat_check
"""
import contextlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf
from tests.test_check_quality import APP, ENGLISH, STRINGS, real_png

def fakes():
    return [mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "ocr_tool", return_value="ocr"),
            mock.patch.object(sf, "warm_up_ocr", return_value=True), mock.patch.object(sf, "readable_languages", return_value={"en"}),
            mock.patch.object(sf, "read_text", lambda ocr, png, timeout=120: ENGLISH), mock.patch.object(sf, "tesseract_languages", return_value=frozenset()),
            mock.patch.object(sf, "tesseract_script", return_value={}), mock.patch.object(sf, "store_rules", return_value=([], [])),
            mock.patch.object(sf.shutil, "which", return_value=None)]

class FlatFolder(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.flat = self.d / "shots"; self.flat.mkdir()
        for n in ("01_welcome.png", "02_home.png"): (self.flat / n).write_bytes(real_png(60, 300, APP))
        self.report = self.d / "rep"

    def run_check(self, *args):
        argv = ["check", str(self.flat), "--report", str(self.report), *args]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as st:
            for f in fakes(): st.enter_context(f)
            st.enter_context(contextlib.redirect_stdout(out)); st.enter_context(contextlib.redirect_stderr(err))
            code = sf.main(argv)
        return code, out.getvalue() + err.getvalue()

    def test_flat_folder_with_locale_is_checked_as_that_language(self):
        code, out = self.run_check("--locale", "en")
        self.assertEqual(code, 0, out)
        rows = json.loads((self.report / "check.json").read_text())["screenshots"]
        self.assertEqual(sorted(r["file"] for r in rows), ["en/01_welcome.png", "en/02_home.png"])

    def test_flat_folder_without_locale_says_locale_is_needed_and_shows_the_example(self):
        code, out = self.run_check()
        self.assertEqual(code, 2)
        self.assertIn("--locale", out); self.assertIn(f"shotfleet check {self.flat} --locale en", out)
        self.assertNotIn("no screenshots found", out)  # it found them; it cannot guess the language

    def test_bad_locale_is_refused(self):
        code, out = self.run_check("--locale", "not a code")
        self.assertEqual(code, 2); self.assertIn("not a language code", out)

    def test_empty_folder_keeps_the_old_error(self):
        for f in self.flat.iterdir(): f.unlink()
        code, out = self.run_check("--locale", "en")
        self.assertEqual(code, 2); self.assertIn("no screenshots found", out)

    def test_locale_folders_are_unchanged_and_win_over_a_stray_locale_flag(self):
        for lp in ("en", "de"):
            f = self.flat / lp / "01_welcome.png"; f.parent.mkdir(); f.write_bytes(real_png(60, 300, APP))
        self.assertEqual(sorted(sf.find_screenshots(self.flat, locale="fr")), ["de", "en"])
        self.assertEqual(sorted(sf.find_screenshots(self.flat)), ["de", "en"])

if __name__ == "__main__":
    unittest.main()
