"""Android screen text from Maestro's per-step hierarchy (research/limits-text.md 1d, 1f). No device, no Maestro: the
hierarchy files are canned in tests/fixtures/android-hierarchy (the shape Maestro 2.11.0 wrote in experiment A)."""
import contextlib, io, json, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

FIX = Path(__file__).resolve().parent / "fixtures/android-hierarchy"
STRINGS = {"en": {"welcome": "Welcome", "next": "Next", "tag": "Your screenshots, in every language."},
           "ja": {"welcome": "ようこそ", "next": "次へ", "tag": "あなたのスクリーンショットを、すべての言語で。"},
           "ar": {"welcome": "مرحبًا", "next": "التالي", "tag": "لقطات شاشتك بكل اللغات"}}


PNG = b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR" + (1320).to_bytes(4, "big") + (2868).to_bytes(4, "big") + bytes([8, 2]) + b"\0" * 8 + b"IDAT"


def debug_run(dbg, flow, shots, markers=True):
    """<dbg>/.maestro/tests/<run>/<flow>/ as Maestro 2.11 writes it: commands.json plus screen-hierarchy/. shots = [(name, fixture)]."""
    d = Path(dbg) / ".maestro/tests/2026-10-04_000000" / flow; (d / "screen-hierarchy").mkdir(parents=True)
    cmds = [{"command": {"applyConfigurationCommand": {"config": {"appId": "x", "name": flow}}}, "metadata": {"status": "COMPLETED"}},
            {"command": {"launchAppCommand": {"appId": "x"}}, "metadata": {"status": "COMPLETED"}}]
    for i, (name, fixture) in enumerate(shots):
        cmds.append({"command": {"takeScreenshotCommand": {"path": f"{flow}/{name}"}},
                     "metadata": {"status": "COMPLETED", "artifacts": [{"type": "TAKE_SCREENSHOT", "path": f"takeScreenshot/{flow}/{name}.png"}]}})
        if markers:
            art = f"screen-hierarchy/step-{i + 5:03}-assertCondition.json"; shutil.copy(FIX / fixture, d / art)
            cmds.append({"command": {"assertConditionCommand": {"condition": {"scriptCondition": "${false}"}, "label": f"shotfleet:hier:{name}", "optional": True}},
                         "metadata": {"status": "WARNED", "artifacts": [{"type": "SCREEN_HIERARCHY", "path": art}, {"type": "SCREENSHOT", "path": "screenshots/x.png"}]}})
    (d / "commands.json").write_text(json.dumps(cmds))


class Markers(unittest.TestCase):
    FLOW = "appId: x\n---\n- launchApp\n- takeScreenshot: 01_welcome\n- tapOn: Next\n- takeScreenshot:\n    path: 02_settings\n    cropOn:\n      text: Settings\n- tapOn: Done\n"

    def marker(self, name):
        return f'- assertTrue:\n    condition: ${{false}}\n    label: "shotfleet:hier:{name}"\n    optional: true\n'

    def test_one_marker_after_every_screenshot_step_scalar_and_map_form(self):
        body = sf.android_flow(self.FLOW, "f", Path("/o"), hierarchy=True).split("\n---\n")[1]
        self.assertIn("- takeScreenshot: '/o/01_welcome'\n" + self.marker("01_welcome") + "- tapOn: Next\n", body)
        # the map form's other keys stay inside their step: the marker goes after the whole step
        self.assertIn("    cropOn:\n      text: Settings\n" + self.marker("02_settings") + "- tapOn: Done\n", body)
        self.assertEqual(body.count("shotfleet:hier:"), 2)

    def test_a_screenshot_as_the_last_step_and_a_nested_one_get_markers_at_their_own_indent(self):
        out = sf.android_flow("appId: x\n---\n- launchApp\n- runFlow:\n    when:\n      visible: A\n    commands:\n      - takeScreenshot: a\n- takeScreenshot: b",
                              "f", Path("/o"), hierarchy=True)
        self.assertIn("      - takeScreenshot: '/o/a'\n      - assertTrue:\n          condition: ${false}\n", out)
        self.assertTrue(out.endswith(self.marker("b")), out)

    def test_no_markers_unless_asked(self):
        self.assertNotIn("assertTrue", sf.android_flow(self.FLOW, "f", Path("/o")))

    def test_hierarchy_needs_maestro_2_7(self):
        for v, ok in (("2.11.0", True), ("2.7.0", True), ("2.10.3", True), ("3.0", True), ("2.6.0", False), ("2.0.10", False), ("1.9.9", False), (None, False), ("", False)):
            with self.subTest(v=v): self.assertEqual(sf.hierarchy_supported(v), ok)


class Reading(unittest.TestCase):
    def test_flattening_drops_the_status_bar_and_keeps_every_line_exact(self):
        ja = sf.hierarchy_lines(json.loads((FIX / "ja-welcome.json").read_text()))
        self.assertEqual(ja, ["ようこそ", "あなたのスクリーンショットを、すべての言語で。", "次へ"])
        ar = sf.hierarchy_lines(json.loads((FIX / "ar-welcome.json").read_text()))
        self.assertEqual(ar, ["مرحبًا", "لقطات شاشتك بكل اللغات", "التالي", "ابحث"])  # the two lines of one node are split; the duplicate is dropped

    def test_each_marker_is_paired_with_the_screenshot_before_it(self):
        with tempfile.TemporaryDirectory() as d:
            debug_run(d, "r1_f0", [("01_welcome", "ja-welcome.json"), ("02_settings", "ar-welcome.json")])
            debug_run(d, "r1_f1", [("01_welcome", "ar-welcome.json")])  # another shard's flow is not mixed in
            got = sf.hierarchy_texts(d, "r1_f0")
        self.assertEqual(sorted(got), ["01_welcome", "02_settings"])
        self.assertEqual(got["01_welcome"][0], "ようこそ"); self.assertEqual(got["02_settings"][0], "مرحبًا")

    def test_a_screenshot_whose_marker_never_ran_gets_no_text(self):
        with tempfile.TemporaryDirectory() as d:
            debug_run(d, "f", [("01", "ja-welcome.json")], markers=False)
            self.assertEqual(sf.hierarchy_texts(d, "f"), {})
            (Path(d) / "x").mkdir(); (Path(d) / "x/commands.json").write_text("not json")  # a half-written file is skipped, not fatal
            self.assertEqual(sf.hierarchy_texts(d, "f"), {})

    def test_texts_are_saved_next_to_the_png_only(self):
        with tempfile.TemporaryDirectory() as d:
            debug_run(Path(d) / "dbg", "f", [("01", "ja-welcome.json"), ("02", "ja-welcome.json")])
            dst = Path(d) / "raw/ja"; dst.mkdir(parents=True); (dst / "01.png").write_bytes(b"png")  # 02.png was never collected
            self.assertEqual(sf.save_hierarchy_texts(Path(d) / "dbg", "f", dst), 1)
            self.assertEqual(json.loads((dst / "01.texts.json").read_text())[2], "次へ")
            self.assertFalse((dst / "02.texts.json").exists())


class Check(unittest.TestCase):
    """cmd_check uses the hierarchy text when it is there (no OCR, any script) and says so; OCR is the fallback."""
    def run_check(self, d, ocr_text=None):
        fake = mock.Mock(side_effect=lambda _o, png, timeout=120: {"text": ocr_text, "chars": len(ocr_text), "lang": "en", "langs": {"en": 0.9}})
        with mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "warm_up_ocr", return_value=True), \
             mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "read_text", fake), \
             mock.patch.object(sf, "readable_languages", return_value={"en"}), mock.patch.object(sf, "tesseract_languages", return_value=frozenset()), \
             contextlib.redirect_stdout(io.StringIO()):
            sf.cmd_check(Path(d) / "raw", strings=STRINGS, report_dir=Path(d) / "rep")
        return json.loads((Path(d) / "rep/check.json").read_text()), fake

    def shots(self, d, fixtures):
        for lp, fx in fixtures.items():
            png = Path(d) / "raw" / lp / "01_welcome.png"; png.parent.mkdir(parents=True)
            png.write_bytes(PNG + lp.encode())  # a PNG header (1320x2868, a size the store rules accept) and a different image per language
            if fx: png.with_suffix(".texts.json").write_text(json.dumps(sf.hierarchy_lines(json.loads((FIX / fx).read_text())), ensure_ascii=False))

    def test_japanese_and_arabic_are_proven_from_the_hierarchy_without_ocr(self):
        with tempfile.TemporaryDirectory() as d:
            self.shots(d, {"ja": "ja-welcome.json", "ar": "ar-welcome.json"})
            report, ocr = self.run_check(d, "unused")
        self.assertEqual(report["problems"], [])
        self.assertEqual({r["file"]: r["evidence"] for r in report["screenshots"]}, {"ja/01_welcome.png": "hierarchy", "ar/01_welcome.png": "hierarchy"})
        self.assertEqual({r["file"]: r["lang"] for r in report["screenshots"]}, {"ja/01_welcome.png": "ja", "ar/01_welcome.png": "ar"})
        ocr.assert_not_called()

    def test_the_wrong_language_is_found_from_the_hierarchy_too(self):
        with tempfile.TemporaryDirectory() as d:
            self.shots(d, {"ja": "ar-welcome.json", "ar": "ar-welcome.json"})  # the Japanese listing shows Arabic
            report, _ = self.run_check(d, "unused")
        self.assertTrue(any(p.startswith("ja/01_welcome.png:") for p in report["problems"]), report["problems"])

    def test_a_screenshot_without_hierarchy_falls_back_to_ocr_and_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            self.shots(d, {"ja": "ja-welcome.json", "ar": None})
            report, ocr = self.run_check(d, "مرحبًا\nالتالي")
        self.assertEqual({r["file"]: r["evidence"] for r in report["screenshots"]}, {"ja/01_welcome.png": "hierarchy", "ar/01_welcome.png": "ocr"})
        self.assertEqual(ocr.call_count, 1)


if __name__ == "__main__":
    unittest.main()
