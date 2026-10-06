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


if __name__ == "__main__":
    unittest.main()
