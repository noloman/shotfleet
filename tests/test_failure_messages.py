"""What `run` says when a language's flow fails (0.1.6, from the AnywhereRoles dogfood run): the failing step, the failure screenshot,
the texts on that screen, and the iOS landscape tap hint. No device, no Maestro: tests/fixtures/maestro-failure/ipad-landscape.log is an
excerpt of the real iPad maestro.log (app id replaced), the rest is written here."""
import json, re, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

LOG = (Path(__file__).resolve().parent / "fixtures/maestro-failure/ipad-landscape.log").read_text()
FLOW = "appId: com.example.app\n---\n- launchApp\n- setOrientation: LANDSCAPE_LEFT\n- tapOn: \"Senior iOS Engineer\"\n"
HIER = {"attributes": {"bounds": "[0,0][0,0]"}, "children": [
    {"attributes": {"accessibilityText": "AnywhereRoles", "bounds": "[-344,344][1032,1376]"}, "children": [
        {"attributes": {"accessibilityText": "Filter jobs"}}, {"attributes": {"text": "4 jobs"}}, {"attributes": {"text": "·"}},
        *({"attributes": {"text": f"Job {i}"}} for i in range(20))]}]}


def debug_dir(root, log=LOG, flow="en", hierarchy=True, shot=True):
    """<root>/.maestro/tests/<run>/ the way Maestro 2.0.x writes a failed flow: maestro.log in one folder, commands and the ❌ screenshot in the next."""
    a, b = Path(root) / ".maestro/tests/2026-10-06_182041", Path(root) / ".maestro/tests/2026-10-06_182042"
    a.mkdir(parents=True); b.mkdir(parents=True)
    (a / "maestro.log").write_text(log)
    err = {"message": "Assertion is false: id: jobDecision.title is visible", **({"hierarchyRoot": HIER} if hierarchy else {})}
    (b / f"commands-({flow}).json").write_text(json.dumps([
        {"command": {"tapOnElement": {}}, "metadata": {"status": "COMPLETED"}},
        {"command": {"assertConditionCommand": {}}, "metadata": {"status": "FAILED", "error": err}}]))
    png = b / f"screenshot-❌-1791303700267-({flow}).png"
    if shot: png.write_bytes(b"\x89PNG")
    return png


class LandscapeHint(unittest.TestCase):
    def details(self, log=LOG, flow_text=FLOW, platform="ios"):
        with tempfile.TemporaryDirectory() as d:
            debug_dir(d, log)
            return sf.failure_details(d, "en", flow_text, platform)

    def test_the_real_ipad_failure_gets_the_hint(self):
        self.assertIn(sf.LANDSCAPE_HINT, self.details())
        self.assertIn("Maestro taps at portrait coordinates in iOS landscape (a Maestro issue): capture iPad in portrait, "
                      "or open the screen with a launch argument or deep link.", sf.LANDSCAPE_HINT)

    def test_no_hint_without_setorientation_landscape_in_the_flow(self):
        self.assertNotIn(sf.LANDSCAPE_HINT, self.details(flow_text=FLOW.replace("LANDSCAPE_LEFT", "PORTRAIT")))

    def test_no_hint_when_the_log_never_turned_the_screen(self):
        self.assertNotIn(sf.LANDSCAPE_HINT, self.details(log=LOG.replace("Set orientation LANDSCAPE_LEFT COMPLETED", "Set orientation LANDSCAPE_LEFT FAILED")))

    def test_no_hint_when_maestro_reports_a_landscape_frame(self):
        self.assertNotIn(sf.LANDSCAPE_HINT, self.details(log=LOG.replace("widthPoints=1032, heightPoints=1376", "widthPoints=1376, heightPoints=1032")))

    def test_no_hint_when_the_tap_was_not_on_the_reported_bounds(self):
        self.assertNotIn(sf.LANDSCAPE_HINT, self.details(log=LOG.replace("Tapping at (97, 677)", "Tapping at (441, 333)")))

    def test_no_hint_when_the_failure_came_before_any_tap(self):
        cut = LOG[:LOG.index("Tap on \"Senior iOS Engineer\" RUNNING")].rsplit("\n", 1)[0] + "\n"
        self.assertNotIn(sf.LANDSCAPE_HINT, self.details(log=cut + LOG.splitlines()[-1] + "\n"))

    def test_no_hint_on_android(self):
        self.assertNotIn(sf.LANDSCAPE_HINT, self.details(platform="android"))

    def test_sharded_log_reads_only_this_flows_steps_and_an_ambiguous_tap_gives_no_hint(self):
        tagged = re.sub(r"(runFlow\S*: ) ?", r"\1[shard 2] ", LOG)
        other = ("18:21:01.000 [ INFO] maestro.cli.runner.TestSuiteInteractor.runFlow: [shard 1]  Running flow de\n"
                 "18:21:50.000 [ INFO] maestro.cli.runner.TestSuiteInteractor.runFlow$lambda$18$lambda$10: [shard 1] Tap on \"Weiter\" FAILED\n")
        with tempfile.TemporaryDirectory() as d:
            debug_dir(d, other + tagged)
            got = sf.failure_details(d, "en", FLOW)
            self.assertIn("failed step: Assert that id: jobDecision.title is visible", got)
            self.assertIn(sf.LANDSCAPE_HINT, got)
        # another shard's tap lands inside this flow's tap window: which tap was whose is not in the log, so say nothing
        busy = tagged.replace("Tapping at (97, 677)", "Tapping at (97, 677) using x\n18:21:08.548 [ INFO] maestro.Maestro.screenshotBasedTap-hbl3e4M: Tapping at (186, 352)")
        with tempfile.TemporaryDirectory() as d:
            debug_dir(d, other + busy)
            self.assertNotIn(sf.LANDSCAPE_HINT, sf.failure_details(d, "en", FLOW))


class FailureLine(unittest.TestCase):
    def test_names_the_step_the_screenshot_and_up_to_12_texts_from_the_hierarchy(self):
        with tempfile.TemporaryDirectory() as d:
            png = debug_dir(d)
            with mock.patch.object(sf, "screenshot_texts", side_effect=AssertionError("no OCR when a hierarchy exists")):
                got = sf.failure_details(d, "en", FLOW)
        self.assertEqual(got[0], "failed step: Assert that id: jobDecision.title is visible")
        self.assertEqual(got[1], f"failure screenshot: {png}")
        texts = got[2].removeprefix("on screen: ").split(" | ")
        self.assertEqual(texts[:4], ["AnywhereRoles", "Filter jobs", "4 jobs", "Job 0"])
        self.assertEqual(len(texts), 12)
        self.assertNotIn("·", texts)

    def test_without_a_hierarchy_the_screenshot_is_read_once(self):
        with tempfile.TemporaryDirectory() as d:
            png = debug_dir(d, hierarchy=False)
            with mock.patch.object(sf, "screenshot_texts", return_value=["Jobs", "Saved", "Select a job to view details"]) as ocr:
                got = sf.failure_details(d, "en", FLOW)
        ocr.assert_called_once_with(png)
        self.assertIn("on screen: Jobs | Saved | Select a job to view details", got)

    def test_no_texts_line_when_there_is_nothing_to_read(self):
        with tempfile.TemporaryDirectory() as d:
            debug_dir(d, hierarchy=False, shot=False)
            with mock.patch.object(sf, "screenshot_texts", side_effect=AssertionError("no screenshot to read")):
                got = sf.failure_details(d, "en", FLOW)
        self.assertFalse(any(l.startswith(("on screen", "failure screenshot")) for l in got))

    def test_ocr_is_skipped_while_macos_is_compiling_its_model(self):
        with mock.patch.object(sf, "vision_available", return_value=True), mock.patch.object(sf, "ane_state", return_value=(True, 3.0)), \
             mock.patch.object(sf, "read_text", side_effect=AssertionError("must not wait on a busy reader")):
            self.assertEqual(sf.screenshot_texts(Path("x.png")), [])

    def test_ocr_reads_lines_within_the_budget_and_gives_up_quietly(self):
        with mock.patch.object(sf, "vision_available", return_value=True), mock.patch.object(sf, "ane_state", return_value=(False, 0)), \
             mock.patch.object(sf, "ocr_tool", return_value="ocr"):
            with mock.patch.object(sf, "read_text", return_value={"text": "A\nB", "lines": [{"text": "A"}, {"text": "B"}]}) as rt:
                self.assertEqual(sf.screenshot_texts(Path("x.png")), ["A", "B"])
            self.assertEqual(rt.call_args.kwargs, {"timeout": 20, "patience": 0})
            with mock.patch.object(sf, "read_text", side_effect=sf.OcrBusy("busy")):
                self.assertEqual(sf.screenshot_texts(Path("x.png")), [])
        with mock.patch.object(sf, "vision_available", return_value=False):
            self.assertEqual(sf.screenshot_texts(Path("x.png")), [])


class MemoryNote(unittest.TestCase):
    def loaded(self):
        return mock.patch.object(sf, "memory_pressure", return_value="4")

    def test_a_plain_assertion_failure_gets_no_memory_note(self):
        with self.loaded():
            self.assertEqual(sf.overload_note(2, 1, ["Assertion is false: id: jobDecision.title is visible"]), "")
            self.assertEqual(sf.overload_note(1, 1, [None]), "")

    def test_the_note_comes_with_the_errors_it_explains(self):
        with self.loaded():
            self.assertIn("short of memory", sf.overload_note(1, 1, ["Unable to clear state for app com.example.app"]))
            self.assertIn("short of memory", sf.overload_note(1, 1, ["Unknown error"]))
        with mock.patch.object(sf, "memory_pressure", return_value="1"):
            self.assertEqual(sf.overload_note(2, 2, ["Unknown error"]), "")


if __name__ == "__main__":
    unittest.main()
