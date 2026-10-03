"""Android strings from a real APK, on any system with aapt2. tests/fixtures/strings-fixture.apk is a resources-only APK
(about 4 KB) made with `aapt2 compile` and `aapt2 link` from tools/fixture-app-android's manifest and these strings in
en, de, ja, ar and tr: app_name, welcome, settings, next, done, tagline, settings_hint, quoted, a <plurals> `days`
and a <string-array> `sizes` (Small, Large)."""
import contextlib, io, json, os, sys, tempfile, tomllib, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

APK = Path(__file__).resolve().parent / "fixtures/strings-fixture.apk"
HAVE_AAPT2 = bool(__import__("shutil").which("aapt2")) or bool(sorted((sf.SDK / "build-tools").glob("*/aapt2")))


def png(w=1080, h=1920):
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + b"\x08\x02\0\0\0"


@unittest.skipUnless(HAVE_AAPT2, "aapt2 is not installed")
class ReadTheApk(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.strings = sf.load_strings_apk(APK)

    def test_every_language_the_app_ships(self):
        self.assertEqual(sorted(self.strings), ["ar", "de", "en", "ja", "tr"])
        self.assertEqual(sf.shipped_locales(self.strings), ["ar", "de", "en", "ja", "tr"])

    def test_string_arrays_are_read_per_item(self):
        self.assertEqual((self.strings["en"]["sizes[0]"], self.strings["en"]["sizes[1]"]), ("Small", "Large"))
        self.assertEqual((self.strings["de"]["sizes[0]"], self.strings["de"]["sizes[1]"]), ("Klein", "Groß"))
        self.assertEqual(self.strings["ja"]["sizes[1]"], "大")
        self.assertEqual(self.strings["ar"]["sizes[0]"], "صغير")

    def test_plurals_and_escapes(self):
        self.assertEqual((self.strings["de"]["days#one"], self.strings["de"]["days#other"]), ("%d Tag", "%d Tage"))
        self.assertEqual(self.strings["en"]["quoted"], 'He said "hi", it\'s fine')

    def test_a_flow_that_taps_an_array_item_is_translated(self):
        out, missing, _ = sf.translate_flow('- tapOn: "Large"\n- assertVisible: "Next"\n', self.strings["en"], self.strings["de"])
        self.assertEqual(missing, [])
        self.assertIn("'Groß'", out)

    def test_a_count_in_a_label_is_matched_and_translated(self):
        out, missing, _ = sf.translate_flow('- assertVisible: "3 days"\n', self.strings["en"], self.strings["de"])
        self.assertEqual(missing, [])
        self.assertIn("3 Tage", out)

    def test_init_reads_the_package_and_languages(self):
        d = Path(tempfile.mkdtemp()); out = io.StringIO()
        with contextlib.redirect_stdout(out): sf.cmd_init([str(APK)], d)
        cfg = tomllib.loads((d / "shotfleet.toml").read_text())
        self.assertTrue(cfg["android"]["apk"].endswith("strings-fixture.apk"))
        self.assertIn("com.shotfleet.fixture: 5 languages", out.getvalue())

    def test_check_with_the_apk_finds_a_german_folder_in_english(self):
        d = Path(tempfile.mkdtemp())
        for lp, words in (("en", ["Welcome", "Settings", "Next", "Small", "Large"]), ("de", ["Willkommen", "Einstellungen", "Weiter", "Klein"]),
                          ("ja", ["Welcome", "Settings", "Next", "Small", "Large"])):  # the Japanese folder shows English
            (d / lp).mkdir(); (d / lp / "1.png").write_bytes(png()); (d / lp / "1.png.txt").write_text("\n".join(words))
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(sf, "is_mac", lambda: False):  # no macOS text recognition
            code = sf.cmd_check(d, app=APK, report_dir=d / "rep", ocr_command="cat {image}.txt")
        report = json.loads((d / "rep/check.json").read_text())
        self.assertEqual(code, 1)
        self.assertTrue(any(p.startswith("ja/1.png: shows en") for p in report["problems"]), report["problems"])
        self.assertFalse(any(p.startswith("de/1.png") and "shows" in p for p in report["problems"]), report["problems"])


class ArraysInSourceFiles(unittest.TestCase):
    def test_string_array_in_a_strings_xml(self):
        d = Path(tempfile.mkdtemp()); (d / "values-de").mkdir()
        (d / "values-de/strings.xml").write_text('<resources><string name="a">Eins</string>'
                                                 '<string-array name="sizes"><item>Klein</item><item>Groß</item></string-array></resources>')
        t = sf.read_translation_file(d / "values-de/strings.xml", "en")
        self.assertEqual(t, {"de": {"a": "Eins", "sizes[0]": "Klein", "sizes[1]": "Groß"}})


if __name__ == "__main__":
    unittest.main()
