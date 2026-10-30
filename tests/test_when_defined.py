"""`runFlow: when: { defined: <input> }` (#80): a block runs, or is left out, per language, by whether [inputs] has a value for it."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

INPUTS = {"phrase": "Lunch with Anna at 1 PM", "es": {"phrase": "Almuerzo con Ana a la 1"}, "pt": {"phrase": "Almoço"}}
FLOW = """- tapOn: Add
- runFlow:
    when: { defined: phrase }
    commands:
      - inputText: ${phrase}
      - takeScreenshot: 02_chips
- takeScreenshot: 03_end
"""


class WhenDefined(unittest.TestCase):
    def test_defined_keeps_the_block_without_the_when(self):
        out, skipped = sf.apply_when_defined(FLOW, INPUTS, "es", "en")
        self.assertEqual(skipped, [])
        self.assertIn("- runFlow:\n    commands:", out); self.assertNotIn("defined", out); self.assertIn("takeScreenshot: 02_chips", out)

    def test_undefined_drops_the_block_and_names_its_screenshots(self):
        out, skipped = sf.apply_when_defined(FLOW, INPUTS, "fr", "en")
        self.assertEqual(skipped, ["02_chips"])
        self.assertNotIn("runFlow", out); self.assertNotIn("inputText", out)
        self.assertEqual(out, "- tapOn: Add\n- takeScreenshot: 03_end\n")

    def test_region_uses_the_language_table_and_the_base_language_uses_the_default(self):
        self.assertEqual(sf.apply_when_defined(FLOW, INPUTS, "pt-BR", "en")[1], [])
        self.assertEqual(sf.apply_when_defined(FLOW, INPUTS, "en", "en")[1], [])
        self.assertEqual(sf.apply_when_defined(FLOW, INPUTS, "en-GB", "en")[1], [])
        self.assertEqual(sf.apply_when_defined(FLOW, INPUTS, "de", "en")[1], ["02_chips"])

    def test_with_no_table_for_the_name_the_default_serves_every_language(self):
        self.assertEqual(sf.apply_when_defined(FLOW, {"phrase": "x"}, "fr", "en")[1], [])
        self.assertEqual(sf.apply_when_defined(FLOW, {}, "fr", "en")[1], ["02_chips"])

    def test_two_line_form_and_flows_without_when_are_handled(self):
        flow = "- runFlow:\n    when:\n      defined: phrase\n    commands:\n      - takeScreenshot: a\n"
        self.assertEqual(sf.apply_when_defined(flow, INPUTS, "fr", "en"), ("\n", ["a"]))
        self.assertIn("commands:", sf.apply_when_defined(flow, INPUTS, "es", "en")[0])
        plain = "- runFlow:\n    file: other.yaml\n- takeScreenshot: z\n"
        self.assertEqual(sf.apply_when_defined(plain, INPUTS, "fr", "en"), (plain, []))

    def test_expected_count_is_per_language(self):
        report = {"locales": {"fr": {"skipped_screenshots": ["02_chips"]}, "es": {}}}
        self.assertEqual(sf.expected_for(report, "fr", 3), 2)
        self.assertEqual(sf.expected_for(report, "es", 3), 3)
        self.assertEqual(sf.expected_for(report, "de", 3), 3)


if __name__ == "__main__":
    unittest.main()
