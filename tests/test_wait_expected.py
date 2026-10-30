"""`- waitForExpected` (#84): waits, in every language, for the texts [expect.<screenshot>] lists, before that screenshot."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

EXPECT = {"02_chips": {"any": ["1:00 PM", "13:00"], "de": {"any": ["13:00 Uhr"]}, "all": ["Anna"]}}
FLOW = "- inputText: hi\n- waitForExpected: { timeout: 20000 }\n- takeScreenshot: 02_chips\n"


class WaitExpected(unittest.TestCase):
    def test_waits_for_the_any_and_all_texts_of_the_next_screenshot(self):
        out, notes = sf.expand_wait_expected(FLOW, EXPECT, ["en"])
        self.assertEqual(notes, [])
        self.assertIn("- extendedWaitUntil:\n    visible: '.*(13:00|1:00 PM).*'\n    timeout: 20000", out)
        self.assertIn("visible: '.*Anna.*'", out)
        self.assertNotIn("waitForExpected", out)
        self.assertTrue(out.rstrip().endswith("- takeScreenshot: 02_chips"))

    def test_the_language_table_is_added_and_several_languages_are_merged(self):
        out, _ = sf.expand_wait_expected(FLOW, EXPECT, ["de", "en"])
        self.assertIn("13:00 Uhr", out); self.assertIn("1:00 PM", out)

    def test_default_timeout_and_bare_number_form(self):
        self.assertIn("timeout: 30000", sf.expand_wait_expected("- waitForExpected\n- takeScreenshot: 02_chips\n", EXPECT, ["en"])[0])
        self.assertIn("timeout: 5000", sf.expand_wait_expected("- waitForExpected: 5000\n- takeScreenshot: 02_chips\n", EXPECT, ["en"])[0])

    def test_regex_characters_in_a_text_are_escaped(self):
        out, _ = sf.expand_wait_expected(FLOW, {"02_chips": {"all": ["(1) a.b"]}}, ["en"])
        self.assertIn(r"visible: '.*\(1\) a\.b.*'", out)

    def test_nothing_to_wait_for_drops_the_step_and_says_so(self):
        out, notes = sf.expand_wait_expected(FLOW, {}, ["en"])
        self.assertNotIn("waitForExpected", out); self.assertNotIn("extendedWaitUntil", out)
        self.assertIn("[expect.02_chips] has no any/all texts", notes[0])
        _, notes = sf.expand_wait_expected("- waitForExpected\n", EXPECT, ["en"])
        self.assertIn("no takeScreenshot", notes[0])

    def test_a_flow_without_the_step_is_unchanged(self):
        flow = "- tapOn: x\n- takeScreenshot: 02_chips\n"
        self.assertEqual(sf.expand_wait_expected(flow, EXPECT, ["en"])[0], flow)


if __name__ == "__main__":
    unittest.main()
