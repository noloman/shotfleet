"""Tests for the Android 7" tablet slot, check/export of Watch, Mac, Apple TV and Vision Pro sets made elsewhere,
and Android typed values per emulator. No device, simulator or Maestro needed (the node tests skip without node).

Run: python3 -m unittest discover -s tests
"""
import contextlib, io, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

# These tests describe the Mac and Apple-silicon behaviour (Vision, Homebrew, arm64 images); the same code on Linux is in
# test_portable.py. The patches last for this module only.
_MAC = [mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "SYSTEM_SDKS", ()),
        mock.patch.object(sf, "ABI", "arm64-v8a"), mock.patch.object(sf, "DEFAULT_IMAGE", "system-images;android-36;google_apis;arm64-v8a")]
def setUpModule():
    for p in _MAC: p.start()
def tearDownModule():
    for p in reversed(_MAC): p.stop()


def png_c(w, h, color_type=2):  # PNG header with a color type: 2 = RGB, 6 = RGBA (as in test_shotfleet.py)
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, color_type]) + b"\0" * 8 + b"IDAT"


class SevenInchTablet(unittest.TestCase):
    def test_the_device_is_9_16_at_1080_px_and_in_the_7_inch_layout_bucket(self):
        kind = sf.ANDROID_DEVICES["tablet-7"]
        w, h, dpi = kind["size"]
        self.assertEqual((kind["folder"], h * 9), ("sevenInchScreenshots", w * 16))  # Play recommends exactly 9:16 at 1080 px+
        self.assertTrue(600 <= w * 160 / dpi < 720)  # sw600dp (7"), below the 10" bucket (720dp)
        self.assertIn("avd_tablet-7", sf.KEYS["android"])  # the config key for its emulator name, like avd_tablet

    def test_export_writes_the_seven_inch_set_next_to_phone_and_ten_inch(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"; (out / "raw/de").mkdir(parents=True)
            (out / "raw/de/01.png").write_bytes(png_c(1080, 1920))
            (out / "run.json").write_text(json.dumps({"platform": "android", "device": "tablet-7", "locales": {"de": {"ok": True}}}))
            (out / "check.json").write_text(json.dumps({"problems": []}))
            fl = Path(d) / "fl"; (fl / "metadata/android/de-DE/images/tenInchScreenshots").mkdir(parents=True)
            (fl / "metadata/android/de-DE/images/tenInchScreenshots/keep.png").write_bytes(b"ten")
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(sf.cmd_export(out, fl), 0)
            images = fl / "metadata/android/de-DE/images"
            self.assertTrue((images / "sevenInchScreenshots/01.png").exists())
            self.assertEqual((images / "tenInchScreenshots/keep.png").read_bytes(), b"ten")

    def test_check_reads_the_seven_inch_folder_with_play_rules_and_a_size_note(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "supply/de-DE/images/sevenInchScreenshots"; f.mkdir(parents=True)
            (f / "1.png").write_bytes(png_c(800, 1280))
            self.assertEqual(sf.play_folders(Path(d) / "supply"), ["sevenInchScreenshots"])
            with mock.patch.object(sf, "warm_up_ocr", return_value=True), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "readable_languages", return_value={"de", "ja"}), \
                 mock.patch.object(sf, "read_text", return_value={"text": "Hallo", "chars": 5, "lang": "de", "langs": {"de": 1}}), \
                 contextlib.redirect_stdout(io.StringIO()) as out:
                sf.check_any(Path(d) / "supply", report=Path(d) / "rep")
            self.assertNotIn("App Store", out.getvalue())
            notes = json.loads((Path(d) / "rep/check.json").read_text())["notes"]
            self.assertTrue(any("under 1080 px" in n and "1,080-7,680" in n for n in notes))

    def test_the_size_note_is_for_tablets_only(self):
        png = Path(tempfile.mkdtemp()) / "a.png"; png.write_bytes(png_c(800, 1280))
        self.assertTrue(any("under 1080 px" in n for n in sf.store_rules({"de": [png]}, android=True, tablet=True)[1]))
        self.assertFalse(any("under 1080 px" in n for n in sf.store_rules({"de": [png]}, android=True)[1]))


class ScreenshotsMadeElsewhere(unittest.TestCase):
    """Watch, Mac, Apple TV and Vision Pro sets from other tools: size and count rules, then export. No capture."""
    def images(self, spec):
        d = Path(tempfile.mkdtemp()); out = {}
        for label, files in spec.items():
            (d / label).mkdir()
            for name, size in files.items():
                (d / label / name).write_bytes(png_c(*size)); out.setdefault(label, []).append(d / label / name)
        return out

    def test_the_published_sizes_of_every_class_pass_and_unknown_ones_do_not(self):
        sizes = {"Apple Watch": [(422, 514), (410, 502), (416, 496), (396, 484), (368, 448), (312, 390)],  # research/store-specs.md
                 "Mac": [(1280, 800), (1440, 900), (2560, 1600), (2880, 1800)],
                 "Apple TV / Vision Pro": [(1920, 1080), (3840, 2160)]}  # Vision Pro is 3840x2160 too
        for cls, ok in sizes.items():
            for size in ok: self.assertEqual(sf.apple_class(size), cls)
            self.assertIsNone(sf.apple_class((ok[0][0] + 1, ok[0][1])))
        self.assertIsNone(sf.apple_class((800, 1280)))  # Mac is not rotated: 16:10 landscape only
        for one in (sizes["Mac"][0], sizes["Apple TV / Vision Pro"][1]):
            self.assertEqual(sf.store_rules(self.images({"de-DE": {"a.png": one}}), android=False), ([], []))

    def test_iphone_duo_sizes_are_known_but_do_not_replace_the_required_iphone_set(self):
        # Apple's specification page of 2026-10-03 lists the foldable's outer (1398x2034) and inner (2007x2853) displays
        self.assertEqual(sf.apple_class((1398, 2034)), "iPhone Duo (outer display)")
        self.assertEqual(sf.apple_class((2853, 2007)), "iPhone Duo (inner display)")  # landscape is accepted too
        self.assertEqual(sf.store_rules(self.images({"de-DE": {"a.png": (1398, 2034), "b.png": (1320, 2868)}}), android=False), ([], []))
        problems, _ = sf.store_rules(self.images({"de-DE": {"a.png": (1398, 2034)}}), android=False)
        self.assertEqual(len(problems), 1); self.assertIn('iPhone screenshots need a 6.9" or 6.5" set', problems[0])

    def test_each_class_takes_at_most_ten(self):
        problems, _ = sf.store_rules(self.images({"de-DE": {f"{i}.png": (2880, 1800) for i in range(11)}}), android=False)
        self.assertEqual(problems, ["de-DE: 11 Mac screenshots; the App Store takes at most 10"])

    def test_one_watch_size_in_every_language(self):
        imgs = self.images({"de-DE": {"a.png": (416, 496)}, "fr-FR": {"a.png": (416, 496)}, "ja": {"a.png": (410, 502)}})
        problems, _ = sf.store_rules(imgs, android=False)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("ja: Apple Watch screenshots aren't 416x496") and "one Watch size" in problems[0])
        same = self.images({"de-DE": {"a.png": (416, 496)}, "ja": {"a.png": (416, 496)}})
        self.assertEqual(sf.store_rules(same, android=False), ([], []))

    def test_check_then_export_a_plain_folder_of_watch_screenshots(self):
        with tempfile.TemporaryDirectory() as d:
            shots = Path(d) / "watch"
            for lp in ("de-DE", "ja"):
                (shots / lp).mkdir(parents=True); (shots / lp / "01.png").write_bytes(png_c(416, 496))
            fl = Path(d) / "fl"; (fl / "screenshots/de-DE").mkdir(parents=True)
            (fl / "screenshots/de-DE/phone.png").write_bytes(png_c(1320, 2868))  # another size: stays
            reads = {"de-DE": {"text": "Hallo Welt", "chars": 10, "lang": "de", "langs": {"de": 1}},
                     "ja": {"text": "こんにちは世界", "chars": 7, "lang": "ja", "langs": {"ja": 1}}}
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(sf.Fail, "hasn't been checked.*--report"): sf.cmd_export(shots, fl)
                with mock.patch.object(sf, "warm_up_ocr", return_value=True), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "readable_languages", return_value={"de", "ja"}), \
                     mock.patch.object(sf, "read_text", side_effect=lambda ocr, png: reads[png.parent.name]):
                    self.assertEqual(sf.cmd_check(shots, report_dir=shots), 0)
                self.assertEqual(sf.cmd_export(shots, fl), 0)
            self.assertEqual(sorted(p.name for p in (fl / "screenshots/de-DE").iterdir()), ["01.png", "phone.png"])
            self.assertTrue((fl / "screenshots/ja/01.png").exists())

    def test_export_skips_a_language_with_a_problem(self):
        with tempfile.TemporaryDirectory() as d:
            shots = Path(d) / "mac"
            for lp in ("de-DE", "ja"):
                (shots / lp).mkdir(parents=True); (shots / lp / "01.png").write_bytes(png_c(2880, 1800))
            (shots / "check.json").write_text(json.dumps({"problems": ["ja/01.png: shows en strings (3 lines) more than ja (0)"]}))
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(sf.cmd_export(shots, Path(d) / "fl"), 1)
            self.assertEqual(sorted(p.name for p in (Path(d) / "fl/screenshots").iterdir()), ["de-DE"])

    def test_an_empty_folder_is_still_not_a_run(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(sf.Fail, "no shotfleet run"):
            sf.cmd_export(Path(d), Path(d) / "fl")


class AndroidTypedValuesPerDevice(unittest.TestCase):
    INPUTS = {"name": "Alex", "city": "Oslo", "ja": {"name": "田中"}}
    LANG = {"emulator-5702": "de", "emulator-5704": "ja"}
    FLOW = "appId: x\n---\n- tapOn: Next\n- inputText: ${name}\n- inputText: ${city}\n- takeScreenshot: 01\n"

    def run_js(self, js, preamble):
        script = preamble + "var output = {};\n" + js + "\nconsole.log(JSON.stringify(output.v));\n"
        r = subprocess.run(["node", "-e", script], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip().splitlines()

    def test_only_names_with_a_per_language_value_are_mapped(self):
        js, names = sf.android_vars(self.INPUTS, self.LANG)
        self.assertEqual(names, {"name"})  # city has a default only: stays a header env entry
        self.assertEqual(sf.android_vars({"name": "Alex"}, self.LANG), ("", set()))
        self.assertEqual(sf.android_vars(None, self.LANG), ("", set()))
        self.assertTrue(js.isascii())  # \u escapes: safe JS for any text

    def test_the_flow_asks_the_script_for_mapped_names_and_nothing_else(self):
        text = sf.android_flow(self.FLOW, "f0", Path("/o"), sf.inputs_for(self.INPUTS, "", defaults_only=True), {"name"})
        body = text.split("\n---\n")[1]
        self.assertTrue(body.startswith("- runScript: shotfleet_vars.js\n- launchApp\n"))
        self.assertIn("- inputText: ${output.v.name}", body)
        self.assertIn("- inputText: ${city}", body)
        plain = sf.android_flow(self.FLOW, "f0", Path("/o"), {"name": "Alex"})
        self.assertNotIn("runScript", plain); self.assertIn("${name}", plain)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_each_device_gets_its_own_language_under_node(self):
        js, _ = sf.android_vars(self.INPUTS, self.LANG)
        self.assertEqual(self.run_js(js, 'var MAESTRO_DEVICE_UDID = "emulator-5704";\n'), ['{"name":"田中"}'])
        self.assertEqual(self.run_js(js, 'var MAESTRO_DEVICE_UDID = "emulator-5702";\n'), ['{"name":"Alex"}'])  # German has no value of its own: the default

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_an_unreadable_device_id_degrades_to_the_defaults_with_a_note(self):
        js, _ = sf.android_vars(self.INPUTS, self.LANG)
        for pre in ("", 'var MAESTRO_DEVICE_UDID = "something-else";\n'):  # variable missing (an older Maestro) or not a serial we know
            lines = self.run_js(js, pre)
            self.assertEqual(lines[-1], '{"name":"Alex"}')
            self.assertTrue(any("typing the [inputs] defaults" in l for l in lines[:-1]), lines)
        only_ja = sf.android_vars({"ja": {"name": "田中"}}, {"emulator-5704": "ja", "emulator-5706": "de"})[0]
        self.assertEqual(self.run_js(only_ja, "")[-1], '{"name":"田中"}')  # no default: the first language's value


if __name__ == "__main__":
    unittest.main()
