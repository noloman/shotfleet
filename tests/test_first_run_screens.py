"""#94 `dismissIfVisible`, #87 other Gradle variants."""
import sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


class Dismiss(unittest.TestCase):
    def test_a_list_and_a_single_text_expand_to_repeats(self):
        out = sf.expand_dismiss_if_visible('- tapOn: a\n- dismissIfVisible: ["Not now", "Skip"]\n- dismissIfVisible: Looks right\n')
        self.assertEqual(out.count("- repeat:"), 3)
        self.assertIn('      visible: "Not now"\n    times: 4\n    commands:\n      - tapOn: "Not now"', out)
        self.assertIn('visible: "Looks right"', out)
        self.assertNotIn("dismissIfVisible", out)

    def test_indent_is_kept_and_other_steps_are_untouched(self):
        out = sf.expand_dismiss_if_visible("- runFlow:\n    commands:\n      - dismissIfVisible: [\"Skip\"]\n")
        self.assertIn("      - repeat:\n          while:", out)
        self.assertEqual(sf.expand_dismiss_if_visible("- tapOn: x\n"), "- tapOn: x\n")

    def test_a_bad_list_says_the_fix(self):
        with self.assertRaisesRegex(ValueError, "JSON-style list"): sf.expand_dismiss_if_visible("- dismissIfVisible: [Not now, Skip]\n")

    def test_the_texts_are_translated_with_the_rest_of_the_flow(self):
        flow = sf.with_app_id('- dismissIfVisible: ["Settings"]\n', "x")
        out, missing, _ = sf.translate_flow(flow, {"s": "Settings"}, {"s": "Einstellungen"})
        self.assertEqual(out.count("Einstellungen"), 2); self.assertEqual(missing, [])


class Variants(unittest.TestCase):
    def test_a_project_without_a_debug_apk_falls_back_to_its_other_variants(self):
        with tempfile.TemporaryDirectory() as d:
            for rel in ("app/build/outputs/apk/benchmarkRelease/app-benchmarkRelease.apk", "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"):
                f = Path(d) / rel; f.parent.mkdir(parents=True); f.write_bytes(b"x")
            found = [a.name for _, a in sf.gradle_apks(d)]
        self.assertEqual(found, ["app-benchmarkRelease.apk"])

    def test_a_debug_apk_still_wins(self):
        with tempfile.TemporaryDirectory() as d:
            for rel in ("app/build/outputs/apk/debug/app-debug.apk", "app/build/outputs/apk/release/app-release.apk"):
                f = Path(d) / rel; f.parent.mkdir(parents=True); f.write_bytes(b"x")
            self.assertEqual([a.name for _, a in sf.gradle_apks(d)], ["app-debug.apk"])

    def test_debuggable_is_read_from_badging(self):
        with mock.patch.object(sf, "aapt2", return_value="aapt2"), mock.patch.object(sf, "sh", return_value=mock.Mock(stdout="application-debuggable\n")):
            self.assertTrue(sf.apk_debuggable("a.apk"))
        with mock.patch.object(sf, "aapt2", return_value="aapt2"), mock.patch.object(sf, "sh", return_value=mock.Mock(stdout="package: name='x'\n")):
            self.assertFalse(sf.apk_debuggable("a.apk"))
        with mock.patch.object(sf, "aapt2", side_effect=sf.Fail("no aapt2")):
            self.assertTrue(sf.apk_debuggable("a.apk"))


if __name__ == "__main__":
    unittest.main()
