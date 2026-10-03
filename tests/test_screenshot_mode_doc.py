"""docs/screenshot-mode.md: its flow examples really work with shotfleet, and it stays honest about what is not built."""
import re, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

DOC = (ROOT / "docs/screenshot-mode.md").read_text()


class ScreenshotModeDoc(unittest.TestCase):
    def test_yaml_examples_survive_the_language_rewrite_and_keep_the_users_arguments(self):
        flows = re.findall(r"```yaml\n(.*?)```", DOC, re.S)
        self.assertTrue(flows)
        for flow in flows:
            out = sf.localize_flow(flow, "de", Path("/o"))
            self.assertIn('SCREENSHOT_MODE: "1"', out)   # the user's argument stays
            self.assertIn("AppleLanguages", out)          # shotfleet's language arguments are added

    def test_string_values_are_what_the_document_tells_people_to_write(self):
        self.assertIn('SCREENSHOT_MODE: "1"', DOC)
        self.assertNotIn("SCREENSHOT_MODE: true", re.sub(r"`SCREENSHOT_MODE: true`", "", DOC))

    def test_features_that_are_built_are_described_as_built_and_the_rest_as_planned(self):
        # [android] shell and the [expect] tables exist (README "Device setup", "Expected content"): the document must say so
        self.assertIn("[android] shell", DOC)
        self.assertIn("[expect.<screenshot>]", DOC)
        self.assertNotIn("cannot run a per-device", DOC)
        self.assertNotIn("is planned and is not available yet", DOC)
        self.assertIn("shell", sf.KEYS["android"]); self.assertIn("simctl", sf.KEYS["ios"]); self.assertIn("expect", sf.TABLES)
        self.assertIn("have **not** been run through shotfleet on a device", DOC)   # the honesty caveat stays

    def test_no_em_dash(self):
        self.assertNotIn("—", DOC)


if __name__ == "__main__":
    unittest.main()
