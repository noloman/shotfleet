"""Bring your own capture on iOS ([capture]): shotfleet runs a team's own XCUITest screenshot tests on its simulator pool.
No simulator, xcodebuild or Maestro is used: every xcrun call is faked. The device test is tools/fixture-byoc-e2e.sh (opt-in)."""
import contextlib, io, json, os, plistlib, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf
sf.USE_DEVICE_LOCK = False

CAPTURE = '[capture]\nbuild = "true"\nxctestrun = "build/Build/Products/*.xctestrun"\n'


def write(d, text):
    (Path(d) / "shotfleet.toml").write_text(text)
    return str(Path(d) / "shotfleet.toml")


class CaptureConfig(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def load(self, text):
        with mock.patch.object(sf, "maestro_cmd", return_value=None):  # capture mode must not need Maestro
            return sf.load_config(write(self.d, text))

    def fails(self, text, words):
        with self.assertRaises(sf.Fail) as cm: self.load(text)
        self.assertIn(words, str(cm.exception))

    def test_capture_without_flow_or_app_loads_and_needs_no_maestro(self):
        platform, cfg, _ = self.load('[ios]\nlocales = ["de", "ja"]\n' + CAPTURE)
        self.assertEqual(platform, "ios")
        self.assertEqual(cfg["_capture"]["xctestrun"], "build/Build/Products/*.xctestrun")
        self.assertNotIn("flow", cfg)

    def test_flow_and_capture_together_are_refused(self):
        self.fails('[ios]\nflow = "flow.yaml"\n' + CAPTURE, "Use one")

    def test_a_flow_config_without_capture_still_needs_app_and_flow(self):
        self.fails('[ios]\nlocales = ["de"]\n', "missing: app")

    def test_capture_needs_build_and_xctestrun(self):
        self.fails('[ios]\n[capture]\nxctestrun = "x/*.xctestrun"\n', "missing build")
        self.fails('[ios]\n[capture]\nbuild = "make"\n', "missing xctestrun")
        self.fails('[ios]\n[capture]\nbuild = " "\nxctestrun = "x"\n', "missing build")

    def test_bad_screenshots_value_typo_and_types_are_refused(self):
        self.fails('[ios]\n' + CAPTURE + 'screenshots = "both"\n', '"auto" (both), not \'both\'')
        self.fails('[ios]\n' + CAPTURE + 'screenshot = "auto"\n', "did you mean 'screenshots'?")
        self.fails('[ios]\n' + CAPTURE + 'timeout = "900"\n', "timeout in shotfleet.toml should be a whole number")
        self.fails('[ios]\n' + CAPTURE + 'timeout = 0\n', "1 or more seconds")
        self.fails('[ios]\n' + CAPTURE + 'only_testing = "A/B"\n', "only_testing in shotfleet.toml should be a list")
        self.fails('[ios]\n' + CAPTURE + 'only_testing = [1]\n', "list of test names")

    def test_every_screenshots_value_is_accepted(self):
        for v in sf.CAPTURE_SHOTS:
            self.assertEqual(self.load('[ios]\n' + CAPTURE + f'screenshots = "{v}"\n')[1]["_capture"]["screenshots"], v)

    def test_capture_is_ios_only(self):
        (Path(self.d) / "a.apk").write_bytes(b"")
        self.fails('[android]\napk = "a.apk"\n' + CAPTURE, "needs an [ios] section")

    def test_android_section_next_to_capture_keeps_its_flow(self):
        with mock.patch.object(sf, "sh", return_value=mock.Mock(stdout="package: name='a.b'")), mock.patch.object(sf, "aapt2", return_value="aapt2"), \
             mock.patch.object(sf, "maestro_cmd", return_value="maestro"):
            (Path(self.d) / "a.apk").write_bytes(b""); (Path(self.d) / "flow.yaml").write_text("- launchApp\n")
            _, cfg, _ = sf.load_config(write(self.d, '[ios]\n[android]\napk = "a.apk"\n' + CAPTURE), "android")
        self.assertIsNone(cfg["_capture"]); self.assertEqual(cfg["flow"], "flow.yaml")


# manifest.json as `xcrun xcresulttool export attachments` wrote it in experiment E4 (Xcode 27.0), one test, 2 screenshots
MANIFEST = [{"attachments": [
    {"configurationName": "Test Scheme Action", "deviceId": "49AA2BD4-B262-4891-9B05-E3FA06093FD8", "deviceName": "byoc-e4-de",
     "exportedFileName": "3B27D4D2-C9D8-47FC-B942-6F27E7F1A9EA.png", "isAssociatedWithFailure": False,
     "suggestedHumanReadableName": "02Settings_0_6232EC24-4CAA-4AFA-B012-EFE755D104BD.png", "timestamp": 1791304707.732},
    {"configurationName": "Test Scheme Action", "deviceId": "49AA2BD4-B262-4891-9B05-E3FA06093FD8", "deviceName": "byoc-e4-de",
     "exportedFileName": "19473290-4472-47B4-9DF6-239A2308A41D.png", "isAssociatedWithFailure": False,
     "suggestedHumanReadableName": "01Welcome_0_17023C40-2DA9-4EEC-B1BF-B5F48E30CDB1.png", "timestamp": 1791304707.109}],
    "testIdentifier": "ScreenshotTests/testScreenshots()"}]


def fake_export(manifest, files):
    """A stand-in for `xcrun xcresulttool export attachments`: writes manifest.json and the <UUID>.png files into --output-path."""
    calls = []
    def sh(cmd, **kw):
        calls.append(cmd)
        out = Path(cmd[cmd.index("--output-path") + 1])
        (out / "manifest.json").write_text(json.dumps(manifest))
        for name, data in files.items(): (out / name).write_bytes(data)
        return sf.subprocess.CompletedProcess(cmd, 0, "", "")
    return sh, calls


class AttachmentCollector(unittest.TestCase):
    def test_names_come_from_the_manifest_without_the_index_and_uuid(self):
        sh, calls = fake_export(MANIFEST, {"3B27D4D2-C9D8-47FC-B942-6F27E7F1A9EA.png": b"settings", "19473290-4472-47B4-9DF6-239A2308A41D.png": b"welcome"})
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "sh", sh):
            dst = Path(d) / "raw/de"
            names = sf.xcresult_pngs(Path(d) / "de.xcresult", dst)
            self.assertEqual(sorted(names), ["01Welcome.png", "02Settings.png"])
            self.assertEqual((dst / "01Welcome.png").read_bytes(), b"welcome")
            self.assertEqual(sorted(p.name for p in dst.iterdir()), ["01Welcome.png", "02Settings.png"])
        self.assertEqual(calls[0][:4], ["xcrun", "xcresulttool", "export", "attachments"])
        self.assertEqual(calls[0][-2:], ["--filter", "*.png"])

    def test_a_name_used_twice_keeps_both_and_warns(self):
        twice = [{"attachments": [dict(MANIFEST[0]["attachments"][1], exportedFileName="A.png"),
                                  dict(MANIFEST[0]["attachments"][1], exportedFileName="B.png")]}]
        sh, _ = fake_export(twice, {"A.png": b"a", "B.png": b"b"})
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "sh", sh), contextlib.redirect_stdout(io.StringIO()) as out:
            names = sf.xcresult_pngs(Path(d) / "x.xcresult", Path(d) / "raw")
        self.assertEqual(names, ["01Welcome.png", "01Welcome-2.png"])
        self.assertIn("two screenshots are named 01Welcome", out.getvalue())

    def test_an_empty_manifest_is_no_screenshots(self):  # SnapshotHelper never attaches: E5 got an empty manifest
        sh, _ = fake_export([], {})
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "sh", sh):
            self.assertEqual(sf.xcresult_pngs(Path(d) / "x.xcresult", Path(d) / "raw"), [])
            self.assertFalse((Path(d) / "raw").exists())


class FastlaneCollector(unittest.TestCase):
    def test_takes_only_this_simulators_files_and_strips_the_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            cache, dst = Path(d) / "screenshots", Path(d) / "raw/de"; cache.mkdir()
            for n in ("shotfleet-1-01Home.png", "shotfleet-1-02Prices.png", "shotfleet-10-01Home.png", "shotfleet-2-01Home.png", "shotfleet-1-notes.txt"):
                (cache / n).write_bytes(n.encode())
            self.assertEqual(sf.fastlane_pngs(cache, "shotfleet-1", dst), ["01Home.png", "02Prices.png"])
            self.assertEqual((dst / "01Home.png").read_bytes(), b"shotfleet-1-01Home.png")
            self.assertEqual(sorted(p.name for p in cache.iterdir()), ["shotfleet-1-notes.txt", "shotfleet-10-01Home.png", "shotfleet-2-01Home.png"])

    def test_settings_files_are_moved_aside_and_put_back(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / "screenshots"; cache.mkdir(); (cache / "language.txt").write_text("de-DE"); (cache / "locale.txt").write_text("de_DE")
            with sf.fastlane_cache(cache) as folder:
                self.assertEqual(folder, cache)
                self.assertFalse((cache / "language.txt").exists()); self.assertFalse((cache / "locale.txt").exists())
            self.assertEqual((cache / "language.txt").read_text(), "de-DE"); self.assertEqual((cache / "locale.txt").read_text(), "de_DE")
            self.assertEqual(sorted(p.name for p in cache.iterdir()), ["language.txt", "locale.txt"])  # no aside folder left

    def test_settings_files_come_back_when_the_run_fails(self):
        for err in (RuntimeError("xcodebuild died"), KeyboardInterrupt()):
            with tempfile.TemporaryDirectory() as d:
                cache = Path(d) / "screenshots"; cache.mkdir(); (cache / "snapshot-launch_arguments.txt").write_text("-x")
                with self.assertRaises(type(err)), sf.fastlane_cache(cache): raise err
                self.assertEqual((cache / "snapshot-launch_arguments.txt").read_text(), "-x")

    def test_a_folder_shotfleet_made_is_removed_and_one_that_existed_is_kept(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / "tools.fastlane/screenshots"
            with sf.fastlane_cache(cache): self.assertTrue(cache.is_dir())
            self.assertFalse((Path(d) / "tools.fastlane").exists())  # the parent was made too, so it goes too
            cache.mkdir(parents=True)
            with sf.fastlane_cache(cache): pass
            self.assertTrue(cache.is_dir())

    def test_files_a_killed_run_left_aside_are_put_back_first(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / "screenshots"; (cache / ".shotfleet-aside").mkdir(parents=True); (cache / ".shotfleet-aside/language.txt").write_text("ja")
            with sf.fastlane_cache(cache): self.assertFalse((cache / "language.txt").exists())
            self.assertEqual((cache / "language.txt").read_text(), "ja")


if __name__ == "__main__":
    unittest.main()
