"""Tests for research/proposed-ocr/shotfleet-ocr.patch. Run: python3 research/proposed-ocr/test_proposed_ocr.py
Copies shotfleet.py to a temp folder, applies the patch there (the repo file is not touched) and imports the copy.
Uses fake helper scripts only: no Vision, no Tesseract, no Neural Engine; `ps` is mocked."""
import importlib.util, os, shutil, stat, subprocess, sys, tempfile, textwrap, time, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TMP = Path(tempfile.mkdtemp())
shutil.copy(ROOT / "shotfleet.py", TMP / "shotfleet.py")
subprocess.run(["patch", "-s", "-p1", "-d", str(TMP), "-i", str(HERE / "shotfleet-ocr.patch")], check=True)
spec = importlib.util.spec_from_file_location("sf_patched", TMP / "shotfleet.py")
sf = importlib.util.module_from_spec(spec); spec.loader.exec_module(sf)


def fake_helper(body):
    p = TMP / f"fake{len(list(TMP.glob('fake*')))}"
    p.write_text("#!/bin/sh\n" + textwrap.dedent(body))
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def ps(cpu, time_):
    return subprocess.CompletedProcess([], 0, f"{cpu} {time_} /System/.../ANECompilerService\n  0.0 0:01.00 /usr/bin/other\n", "")


class AneState(unittest.TestCase):
    def test_ps_time_formats(self):
        for t, minutes in (("18:10.86", 18.18), ("1:03:22.10", 63.37), ("2-03:00:00.00", 2 * 1440 + 180)):
            with mock.patch.object(sf, "sh", return_value=ps("97.0", t)):
                busy, m = sf.ane_state()
            self.assertTrue(busy); self.assertAlmostEqual(m, minutes, delta=0.05)

    def test_not_running_or_idle(self):
        with mock.patch.object(sf, "sh", return_value=subprocess.CompletedProcess([], 0, "  0.0 0:01.00 /usr/bin/other\n", "")):
            self.assertEqual(sf.ane_state(), (False, 0))
        with mock.patch.object(sf, "sh", return_value=ps("0.0", "18:10.86")):
            self.assertFalse(sf.ane_state()[0])

    def test_messages_tell_what_to_do(self):
        for state, must in (((True, 700), "Restart the Mac"), ((True, 5), "Run check again in a few minutes"), ((False, 0), "overloaded")):
            with mock.patch.object(sf, "ane_state", return_value=state):
                self.assertIn(must, sf.ocr_not_answering())
        with mock.patch.object(sf, "ane_state", return_value=(True, 700)):
            self.assertIn("stuck", sf.ocr_not_answering()); self.assertNotIn("Tesseract", sf.ocr_not_answering())


class WarmUp(unittest.TestCase):
    def run_warm(self, helper, state, **kw):
        t0 = time.time()
        with mock.patch.object(sf, "ane_state", return_value=state):
            return sf.warm_up_ocr(helper, **kw), time.time() - t0

    def test_hung_and_idle_gives_up_at_timeout(self):
        ok, took = self.run_warm(fake_helper("sleep 30\n"), (False, 0), timeout=0.5, patience=20)
        self.assertFalse(ok); self.assertLess(took, 3)

    def test_slow_compile_is_waited_for_while_service_works(self):
        ok, took = self.run_warm(fake_helper("sleep 1.5; echo Ready\n"), (True, 5), timeout=0.5, patience=20)
        self.assertTrue(ok); self.assertGreater(took, 1.4)

    def test_patience_is_a_ceiling(self):
        ok, took = self.run_warm(fake_helper("sleep 30\n"), (True, 5), timeout=0.5, patience=2)
        self.assertFalse(ok); self.assertLess(took, 5)

    def test_stuck_service_is_not_waited_for(self):
        ok, took = self.run_warm(fake_helper("sleep 30\n"), (True, 700), timeout=0.5, patience=20)
        self.assertFalse(ok); self.assertLess(took, 3)

    def test_default_patience_is_off(self):  # callers and tests that pass only timeout behave as before
        ok, took = self.run_warm(fake_helper("sleep 30\n"), (True, 5), timeout=0.5)
        self.assertFalse(ok); self.assertLess(took, 3)


class ReadText(unittest.TestCase):
    def test_vision_failure_is_an_error_not_an_empty_screen(self):
        h = fake_helper("echo 'Vision failed: Code=13' >&2; exit 2\n")
        with self.assertRaisesRegex(RuntimeError, "Vision failed: Code=13"):
            sf.read_text(h, "x.png", timeout=5)

    def test_good_answer(self):
        h = fake_helper("""echo '{"lang": "de", "chars": 3, "text": "abc"}'\n""")
        self.assertEqual(sf.read_text(h, "x.png", timeout=5)["chars"], 3)

    def test_hang_is_retried_once_then_names_the_cause(self):
        h = fake_helper("sleep 30\n")
        with mock.patch.object(sf, "ane_state", return_value=(True, 700)), self.assertRaisesRegex(RuntimeError, "stuck"):
            sf.read_text(h, "x.png", timeout=0.3)


class Languages(unittest.TestCase):
    """macOS 14's reader list (INFERENCE: 7 to 20 languages, no Catalan) on a Mac."""
    def judge(self, lp, ocr, listed=("en", "de")):
        with mock.patch.object(sf, "readable_languages", return_value=set(listed)), mock.patch.object(sf, "vision_available", return_value=True):
            return sf.judge_screen(lp, {"chars": 99, "text": "x", "ocr": "vision", **ocr}, sf.string_tables({"en": {"a": "Advanced"}, lp: {"a": "Avançat"}}))

    def test_catalan_screen_that_is_english_is_flagged_like_on_macos_15(self):
        got, problem = self.judge("ca", {"lang": "en", "langs": {"en": 0.862}})
        self.assertEqual(got, "en"); self.assertIn("text looks like 'en', expected 'ca'", problem)

    def test_real_catalan_passes(self):
        self.assertEqual(self.judge("ca", {"lang": "ca", "langs": {"ca": 0.97}}), ("ca", None))

    def test_croatian_read_as_slovenian_is_not_a_finding(self):
        self.assertEqual(self.judge("hr", {"lang": "sl", "langs": {"sl": 0.9, "hr": 0.05}}), ("hr", None))

    def test_unreadable_script_is_still_skipped(self):
        self.assertEqual(self.judge("el", {"lang": "en", "langs": {"en": 0.862}}), (None, None))

    def test_not_on_linux(self):  # Tesseract names no language, so the Latin rule is for macOS only
        with mock.patch.object(sf, "readable_languages", return_value={"en"}), mock.patch.object(sf, "vision_available", return_value=False):
            self.assertFalse(sf.can_read("ca"))


if __name__ == "__main__":
    try: unittest.main()
    finally: shutil.rmtree(TMP, ignore_errors=True)
