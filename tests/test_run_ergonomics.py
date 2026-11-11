"""Fixes from the first real Android run of Quickspan (#92, #93, #95, #96): flow rewriting, failure reporting, --devices, warning noise."""
import sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


class EmptyLaunch(unittest.TestCase):
    def test_android_flow_does_not_leave_an_empty_launchapp_mapping(self):
        flow = "appId: x\n---\n- launchApp:\n    clearState: true\n- takeScreenshot: a\n"
        out = sf.android_flow(flow, "n", Path("n"))
        self.assertIn("\n- launchApp\n", out); self.assertNotIn("launchApp:", out)

    def test_options_that_remain_keep_their_mapping(self):
        out = sf.android_flow("appId: x\n---\n- launchApp:\n    clearState: true\n    permissions: { all: allow }\n", "n", Path("n"))
        self.assertIn("- launchApp:\n    permissions", out)

    def test_collapse_only_touches_an_empty_launchapp(self):
        self.assertEqual(sf.collapse_empty_launch(["- launchApp:", "- tapOn: a", "  - launchApp:", "      arguments: {}"]),
                         ["- launchApp", "- tapOn: a", "  - launchApp:", "      arguments: {}"])


class FailureReporting(unittest.TestCase):
    LOG = ("> Incorrect Command Format: launchApp\n\n/x/f.yaml:9\n╭──╮\n│ 9 | - launchApp:   │\n│ ╭────╮ │\n"
           "│ │ The command `launchApp` requires additional options. │ │\n")

    def test_a_flow_maestro_rejected_is_named_and_not_retried(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "m.log"; log.write_text(self.LOG)
            msg = sf.no_result(log)
        self.assertIn("rejected the flow", msg); self.assertIn("launchApp", msg)
        self.assertFalse(sf.is_infra_error(msg))

    def test_a_missing_log_is_still_no_result(self):
        self.assertEqual(sf.no_result("/nonexistent/m.log"), "no result (see maestro log)")

    def test_device_screenshot_is_taken_only_when_maestro_left_none(self):
        class Emu: serial = "emulator-5702"
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(sf.subprocess, "run", return_value=mock.Mock(returncode=0, stdout=b"\x89PNG...")) as run:
                png = sf.device_failure_screenshot(Emu(), d, "f0")
            self.assertEqual(png.read_bytes()[:4], b"\x89PNG"); self.assertEqual(sf.failure_screenshot(d, "f0"), png)
            with mock.patch.object(sf.subprocess, "run") as run2:
                self.assertEqual(sf.device_failure_screenshot(Emu(), d, "f0"), png); run2.assert_not_called()
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf.subprocess, "run", return_value=mock.Mock(returncode=1, stdout=b"")):
            self.assertIsNone(sf.device_failure_screenshot(Emu(), d, "f0"))

    def test_partial_sets_are_named_in_the_summary(self):
        report = {"locales": {"en": {}, "de": {"skipped_screenshots": ["x"]}}}
        final = {"en": {"ok": False, "screenshots": 2}, "de": {"ok": False, "screenshots": 1}, "fr": {"ok": True, "screenshots": 5}, "ja": {"ok": False, "screenshots": 0}}
        self.assertEqual(sf.partial_note(final, report, 5), "; incomplete sets kept in raw/: en 2 of 5, de 1 of 4")
        self.assertEqual(sf.partial_note({"fr": {"ok": True, "screenshots": 5}}, report, 5), "")


class Noise(unittest.TestCase):
    def test_regex_looking_selectors_are_not_reported_as_untranslated(self):
        for t in ("1:00.PM", "1:00.PM.*", ".*Mon.Tue"): self.assertTrue(sf.looks_like_pattern(t), t)
        for t in ("Settings", "Mr. Smith", "Next", "Nothing like [0-9]+", "Nope.*"): self.assertFalse(sf.looks_like_pattern(t), t)
        _, missing, _ = sf.translate_flow('- extendedWaitUntil:\n    visible: "1:00.PM.*"\n- tapOn: "Nope"\n', {"a": "Next"}, {"a": "Weiter"})
        self.assertEqual(missing, ["Nope"])

    def test_doctor_sees_locale_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.toml"
            p.write_text('[android]\napk="a"\n[inputs]\nname="x"\n[inputs.de]\nname="y"\n'); self.assertTrue(sf.config_has_locale_inputs(p))
            p.write_text('[inputs]\nname="x"\n'); self.assertFalse(sf.config_has_locale_inputs(p))
            self.assertFalse(sf.config_has_locale_inputs(Path(d) / "none.toml"))


class DevicesFlag(unittest.TestCase):
    def test_pick_devices(self):
        self.assertEqual(sf.pick_devices(["phone", "tablet"], ["tablet"], "x"), ["tablet"])
        self.assertEqual(sf.pick_devices(["phone", "tablet"], None, "x"), ["phone", "tablet"])
        with self.assertRaisesRegex(sf.Fail, r"--devices tv: not in the config's x \(phone, tablet\)"): sf.pick_devices(["phone", "tablet"], ["tv"], "x")

    def test_run_passes_the_flag_on(self):
        seen = []
        with mock.patch.object(sf, "cmd_run", lambda *a, **k: seen.append(sf.DEVICES_ONLY) or 0), \
             mock.patch.object(sf, "maestro_cmd", return_value=None):
            sf.main(["run", "x.toml", "--devices", "phone, tablet"])
        self.assertEqual(seen, [["phone", "tablet"]])
        sf.DEVICES_ONLY = None


class RelativeApk(unittest.TestCase):
    def test_the_no_apk_error_says_where_a_relative_path_was_looked_for(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "sub" / "shotfleet.toml"; cfg.parent.mkdir()
            (cfg.parent / "flow.yaml").write_text("appId: x\n---\n- launchApp\n")
            cfg.write_text('[android]\napk = "app/build/x.apk"\n')
            with self.assertRaisesRegex(sf.Fail, r"no APK at .*next to the config file, in .*sub"): sf.load_config(str(cfg))


if __name__ == "__main__":
    unittest.main()
