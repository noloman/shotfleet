"""Quality of `check`: when a text reader finds nothing it must say "could not read", not "blank". No device, no real OCR: the readers are fakes.

Run: python3 -m unittest discover -s tests
"""
import contextlib, io, json, struct, sys, tempfile, unittest, zlib
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

_MAC = [mock.patch.object(sf, "is_mac", lambda: True)]  # the Vision path, whatever machine the tests run on
def setUpModule():
    for p in _MAC: p.start()
def tearDownModule():
    for p in reversed(_MAC): p.stop()


def real_png(w, h, pixel):
    """A decodable PNG (filter 0 on every row) whose pixel at (x, y) is pixel(x, y)."""
    raw = b"".join(b"\0" + b"".join(bytes(pixel(x, y)) for x in range(w)) for y in range(h))
    chunk = lambda k, d: struct.pack(">I", len(d)) + k + d + b"\0\0\0\0"
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

# rows that differ, like glyphs on a screen; and one flat frame with a clock in the status bar
APP = lambda x, y: (0, 0, 0) if (y // 6) % 3 == 0 and x % (5 + y % 7) < 3 and 40 < y < 260 else (255, 255, 255)
FLAT = lambda x, y: (30, 30, 30) if y < 20 and 10 < x < 30 else (255, 255, 255)

STRINGS = {"en": {"a": "Next", "b": "Settings", "c": "Start Training"},
           "ar": {"a": "التالي", "b": "الإعدادات", "c": "ابدأ التمرين"}}
ENGLISH = {"text": "Next\nSettings", "chars": 13, "lang": None, "langs": {}, "ocr": "external"}
NOTHING = {"text": "", "chars": 0, "lang": None, "langs": {}, "ocr": "external"}  # Tesseract on the Arabic screen


class CouldNotRead(unittest.TestCase):
    def check(self, ar_pixels, vision=None, external=NOTHING, packs=("eng", "ara")):
        """check on an en and an ar listing. vision=None: macOS text recognition is stuck (Tesseract reads everything)."""
        d = Path(tempfile.mkdtemp())
        for lp, pix in (("en", APP), ("ar", ar_pixels)):
            f = d / "shots" / lp / "01_welcome.png"; f.parent.mkdir(parents=True); f.write_bytes(real_png(60, 300, pix))
        ext = lambda cmd, png, lp: ENGLISH if "/en/" in str(png) else external
        read = (lambda ocr, png, timeout=120: ENGLISH if "/en/" in str(png) else vision) if vision is not None else \
            mock.Mock(side_effect=AssertionError("macOS text recognition must not be used"))
        with mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "warm_up_ocr", return_value=vision is not None), \
             mock.patch.object(sf, "readable_languages", return_value={"en", "ar"}), mock.patch.object(sf, "read_text", read), \
             mock.patch.object(sf, "tesseract_languages", return_value=frozenset(packs)), mock.patch.object(sf, "external_ocr", ext), \
             mock.patch.object(sf, "tesseract_script", return_value={}), mock.patch.object(sf, "store_rules", return_value=([], [])),mock.patch.object(sf.shutil, "which", return_value="/x"), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            code = sf.cmd_check(d / "shots", strings=STRINGS, report_dir=d / "rep")
        return code, out.getvalue(), json.loads((d / "rep/check.json").read_text())

    def test_tesseract_finding_no_text_on_a_real_screen_is_a_note_not_a_problem(self):
        code, out, report = self.check(APP)
        self.assertEqual(report["problems"], [])
        self.assertEqual(code, 0)
        self.assertTrue(any(n.startswith("ar/01_welcome.png: could not read this screenshot") and "not blank" in n for n in report["notes"]))
        self.assertNotIn("can't read the script of ar", out)  # Arabic is readable; the reader failed, which the note says

    def test_a_language_pack_missing_for_the_fallback_is_the_same_note(self):
        code, _, report = self.check(APP, packs=("eng",))  # no Arabic data: the screenshot is never read at all
        self.assertEqual((code, report["problems"]), (0, []))
        self.assertTrue(any("could not read this screenshot" in n for n in report["notes"]))

    def test_a_flat_frame_is_still_a_problem_because_the_pixels_say_so(self):
        code, _, report = self.check(FLAT)
        self.assertEqual(code, 1)
        self.assertEqual([p.split(":")[0] for p in report["problems"]], ["ar/01_welcome.png"])
        self.assertIn("blank: nothing is drawn", report["problems"][0])
        self.assertFalse(any("could not read" in n for n in report["notes"]))

    def test_macos_text_recognition_finding_nothing_on_a_screen_it_reads_stays_a_problem(self):
        vision = {"text": "", "chars": 0, "lang": None, "langs": {}}  # a healthy read: no `ocr` key, no failure to blame
        code, _, report = self.check(APP, vision=vision)
        self.assertEqual(code, 1)
        self.assertIn("ar/01_welcome.png: no text found (blank or still loading?)", report["problems"])

    def test_a_screen_the_fallback_does_read_is_judged_as_before(self):
        code, _, report = self.check(APP, external={**ENGLISH, "text": "التالي\nالإعدادات", "chars": 15})
        self.assertEqual((code, report["problems"], report["notes"]), (0, [], []))


class HangMidCheck(unittest.TestCase):
    def test_a_screen_macos_read_before_it_hung_is_not_replaced_by_an_empty_tesseract_read(self):
        import threading
        d = Path(tempfile.mkdtemp()); first_done = threading.Event()
        for lp in ("en", "ar"):
            f = d / "shots" / lp / "01_welcome.png"; f.parent.mkdir(parents=True); f.write_bytes(real_png(60, 300, APP))
        def read(ocr, png, timeout=120):
            if "/en/" in str(png): first_done.set(); return {"text": "Next\nSettings", "chars": 13, "lang": "en", "langs": {"en": 1}}
            first_done.wait(5); raise RuntimeError("hung twice")  # the second screenshot hangs after the first was read
        with mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "warm_up_ocr", return_value=True), \
             mock.patch.object(sf, "readable_languages", return_value={"en", "ar"}), mock.patch.object(sf, "read_text", read), \
             mock.patch.object(sf, "tesseract_languages", return_value=frozenset({"eng", "ara"})), \
             mock.patch.object(sf, "external_ocr", return_value=NOTHING), mock.patch.object(sf, "tesseract_script", return_value={}), \
             mock.patch.object(sf, "store_rules", return_value=([], [])), mock.patch.object(sf.shutil, "which", return_value="/x"), \
             contextlib.redirect_stdout(io.StringIO()):
            code = sf.cmd_check(d / "shots", strings=STRINGS, report_dir=d / "rep")
        report = json.loads((d / "rep/check.json").read_text())
        self.assertEqual({r["file"]: r["chars"] for r in report["screenshots"]}, {"en/01_welcome.png": 13, "ar/01_welcome.png": 0})
        self.assertEqual((code, report["problems"]), (0, []))  # en keeps its good read; ar is only a note
        self.assertEqual(len(report["notes"]), 1)


class NoStringsOnTesseract(unittest.TestCase):
    def test_a_german_screen_in_the_english_folder_is_not_flagged_so_the_run_says_the_language_was_not_checked(self):
        d = Path(tempfile.mkdtemp()); f = d / "shots/en/01_home.png"; f.parent.mkdir(parents=True); f.write_bytes(real_png(60, 300, APP))
        german = {"text": "Einstellungen\nTraining starten\nVerlauf", "chars": 36, "lang": None, "langs": {}, "ocr": "external"}
        with mock.patch.object(sf, "vision_available", lambda: False), mock.patch.object(sf.shutil, "which", return_value="/x"), \
             mock.patch.object(sf, "external_ocr", return_value=german), mock.patch.object(sf, "store_rules", return_value=([], [])), \
             mock.patch.object(sf, "tesseract_languages", return_value=frozenset({"eng"})), contextlib.redirect_stdout(io.StringIO()):
            code = sf.cmd_check(d / "shots", report_dir=d / "rep")
        report = json.loads((d / "rep/check.json").read_text())
        self.assertEqual((code, report["problems"]), (0, []))  # nothing can judge it: that is a limit, so it is said
        self.assertTrue(any("without --app" in n and "language was not checked" in n for n in report["notes"]))


if __name__ == "__main__":
    unittest.main()
