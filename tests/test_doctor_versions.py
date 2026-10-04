"""Gate 8 and the doctor-under-load fix: `doctor` and `run` say which Maestro shotfleet was tested with and warn outside it,
and a slow or empty text-recognition warm-up is a note, not a PROBLEM.

A fake `maestro` on PATH and a fake OCR helper; no simulator, no emulator, no Maestro run.

Run: python3 -m unittest tests.test_doctor_versions
"""
import contextlib, io, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

# These tests describe the Mac and Apple-silicon behaviour (Vision, Homebrew, arm64 images); the same code on Linux is in
# test_portable.py. The patches last for this module only.
_MAC = [mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "SYSTEM_SDKS", ()),
        mock.patch.object(sf, "ABI", "arm64-v8a"), mock.patch.object(sf, "DEFAULT_IMAGE", "system-images;android-36;google_apis;arm64-v8a")]
def setUpModule():
    for p in _MAC: p.start()
def tearDownModule():
    for p in reversed(_MAC): p.stop()


def script(path, body):
    path.write_text("#!/bin/sh\n" + body + "\n"); path.chmod(0o755)
    return path


class Fakes(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.d = Path(tmp.name).resolve(); self.bin = self.d / "bin"; self.bin.mkdir()
        self.sdk = self.d / "sdk"; self.sdk.mkdir()

    def maestro(self, body): return script(self.bin / "maestro", body)

    def doctor(self, ocr_body="echo Ready", timeout=None):
        """Run cmd_doctor with the fake maestro and the fake OCR helper really executed; everything else answers 'ok'."""
        ocr = script(self.d / "ocr", ocr_body)
        real = sf.sh
        def fake_sh(cmd, **kw):
            if cmd[0] in ("maestro", str(ocr)): return real(cmd, **kw)
            return subprocess.CompletedProcess(cmd, 0, "Ready\n", "")
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"PATH": f"{self.bin}:{os.environ['PATH']}"}), mock.patch.object(sf, "SDK", self.sdk), \
             mock.patch.object(sf, "java_env", return_value={}), mock.patch.object(sf, "find_java", return_value=(True, None)), \
             mock.patch.object(sf, "ocr_tool", return_value=str(ocr)), mock.patch.object(sf, "latest_release", return_value=None), \
             mock.patch.object(sf, "sh", fake_sh), mock.patch.object(sf, "DOCTOR_OCR_TIMEOUT_S", timeout or sf.DOCTOR_OCR_TIMEOUT_S), \
             contextlib.redirect_stdout(out):
            code = sf.cmd_doctor()
        return code, out.getvalue()


class MaestroVersion(Fakes):
    def test_the_tested_version_is_one_constant_and_it_is_2_0_10(self):
        self.assertEqual(sf.MAESTRO_TESTED, ("2.0.10",))

    def test_parsing_survives_noise_around_the_version(self):
        for text, want in (("2.0.10\n", "2.0.10"), ("v2.11.0\n", "2.11.0"), ("WARNING: illegal reflective access\n2.0.10\n", "2.0.10"),
                           ("maestro 2.0.10", "2.0.10"), ("1.40.3", "1.40.3"), ("2.0.10 (build abc)", "2.0.10"),
                           ("", None), ("Ready", None), ("command not found", None), ("Error: JAVA_HOME is not set", None)):
            self.assertEqual(sf.parse_maestro_version(text), want, text)
        self.assertEqual(sf.parse_maestro_version("", "2.0.10"), "2.0.10")  # a version on stderr counts

    def test_same_version_prints_it_with_the_tested_one_and_no_warning(self):
        self.maestro("echo 2.0.10")
        code, out = self.doctor()
        self.assertIn("ok   maestro 2.0.10 (tested: 2.0.10)", out)
        self.assertNotIn("not the version shotfleet was tested with", out)
        self.assertNotIn("could not read", out)

    def test_a_newer_version_warns_in_one_line_that_names_the_tested_one_and_does_not_fail_doctor(self):
        self.maestro("echo 2.11.0")
        code, out = self.doctor()
        self.assertIn("ok   maestro 2.11.0 (tested: 2.0.10)", out)
        warn = [l for l in out.splitlines() if "not the version shotfleet was tested with" in l]
        self.assertEqual(len(warn), 1, out)
        self.assertIn("(2.0.10)", warn[0]); self.assertIn("may work", warn[0]); self.assertIn("2.11.0", warn[0])
        self.assertNotIn("MISSING maestro", out)
        # the exit code is not driven by the version: same as with the tested one
        self.maestro("echo 2.0.10")
        self.assertEqual(self.doctor()[0], code)

    def test_an_older_2_x_warns_but_maestro_1_is_still_refused(self):
        self.maestro("echo 2.0.9")
        code, out = self.doctor()
        self.assertIn("ok   maestro 2.0.9", out); self.assertIn("may work", out)
        self.maestro("echo 1.40.3")
        code, out = self.doctor()
        self.assertIn("MISSING maestro 1.40.3", out)

    def test_garbage_output_is_installed_but_unreadable_not_missing(self):
        self.maestro("echo 'Segmentation banana'")
        code, out = self.doctor()
        self.assertNotIn("MISSING maestro", out)
        self.assertIn("maestro (version unknown; tested: 2.0.10)", out)
        self.assertIn("could not read Maestro's version", out); self.assertIn("2.0.10", out); self.assertIn("may work", out)

    def test_no_maestro_is_still_missing_with_the_install_command(self):
        code, out = self.doctor()  # nothing on the fake bin; skip if the machine's PATH has a real maestro
        if "MISSING maestro" not in out: self.skipTest("a real maestro is on the PATH")
        self.assertIn("get.maestro.mobile.dev", out)

    def run_note(self, version_body):
        self.maestro(version_body)
        args = type("A", (), {"cmd": "run", "config": "x.toml", "locales": None, "parallel": None, "platform": None, "no_hooks": False})()
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"PATH": f"{self.bin}:{os.environ['PATH']}"}), mock.patch.object(sf, "java_env", return_value={}), \
             mock.patch.object(sf, "apply_free_tier"), mock.patch.object(sf, "cmd_run", return_value=0) as run, contextlib.redirect_stderr(err):
            code = sf.main_dispatch(args)
        self.assertEqual(code, 0); run.assert_called_once()
        return err.getvalue()

    def test_run_prints_the_note_once_to_stderr_only_when_the_version_differs(self):
        err = self.run_note("echo 2.5.0")
        self.assertEqual(err.count("not the version shotfleet was tested with"), 1, err)
        self.assertIn("(2.0.10)", err); self.assertIn("may work", err)
        self.assertEqual(self.run_note("echo 2.0.10"), "")
        self.assertIn("could not read", self.run_note("echo nonsense"))


class DoctorUnderLoad(Fakes):
    def test_success_is_ok_with_the_time(self):
        self.maestro("echo 2.0.10")
        code, out = self.doctor("echo Ready")
        self.assertRegex(out, r"ok   text recognition   ready in \d+ s"); self.assertNotIn("PROBLEM", out)

    def test_a_slow_warm_up_is_a_note_with_the_exit_code_unaffected_and_doctor_does_not_block(self):
        self.maestro("echo 2.0.10")
        fast_code, _ = self.doctor("echo Ready")
        t0 = time.time()
        code, out = self.doctor("sleep 30; echo Ready", timeout=1)
        self.assertLess(time.time() - t0, 15, "doctor must stop waiting at its own timeout")
        self.assertNotIn("PROBLEM", out)
        line = next(l for l in out.splitlines() if "slow to start" in l)
        self.assertIn("text recognition: slow to start (the Mac is busy or this is the first run: it compiles a model once, up to a few minutes)", line)
        self.assertIn("waited 1 s", line)
        self.assertEqual(code, fast_code)

    def test_the_timeout_is_at_most_60_seconds(self):
        self.assertLessEqual(sf.DOCTOR_OCR_TIMEOUT_S, 60)

    def test_an_empty_answer_from_a_loaded_mac_is_the_same_note_not_a_problem(self):
        self.maestro("echo 2.0.10")
        code, out = self.doctor("echo ''")  # what the frozen helper printed on a loaded Mac
        self.assertNotIn("PROBLEM", out); self.assertIn("slow to start", out)

    def test_an_actual_error_is_still_a_problem(self):
        self.maestro("echo 2.0.10")
        code, out = self.doctor("echo 'Vision request failed' >&2; exit 3")
        self.assertIn("PROBLEM text recognition", out); self.assertIn("Vision request failed", out); self.assertNotIn("slow to start", out)

    def test_a_helper_that_cannot_start_is_a_problem(self):
        self.maestro("echo 2.0.10")
        ocr = self.d / "missing"
        real = sf.sh
        def fake_sh(cmd, **kw):
            if cmd[0] == "maestro": return real(cmd, **kw)
            if cmd[0] == str(ocr): raise OSError("no such file")
            return subprocess.CompletedProcess(cmd, 0, "Ready\n", "")
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"PATH": f"{self.bin}:{os.environ['PATH']}"}), mock.patch.object(sf, "SDK", self.sdk), \
             mock.patch.object(sf, "java_env", return_value={}), mock.patch.object(sf, "find_java", return_value=(True, None)), \
             mock.patch.object(sf, "ocr_tool", return_value=str(ocr)), mock.patch.object(sf, "latest_release", return_value=None), \
             mock.patch.object(sf, "sh", fake_sh), contextlib.redirect_stdout(out):
            sf.cmd_doctor()
        self.assertIn("PROBLEM text recognition   can't start", out.getvalue())


class Simctl(unittest.TestCase):
    def test_a_simctl_that_hangs_is_not_ready_instead_of_blocking_doctor(self):
        def hang(cmd, **kw): raise subprocess.TimeoutExpired(cmd, kw["timeout"])
        with mock.patch.object(sf, "sh", hang): self.assertFalse(sf.simctl_works())
        seen = {}
        def ok(cmd, **kw): seen.update(kw); return subprocess.CompletedProcess(cmd, 0, "", "")
        with mock.patch.object(sf, "sh", ok): self.assertTrue(sf.simctl_works())
        self.assertLessEqual(seen["timeout"], 120)


if __name__ == "__main__":
    unittest.main()

    def test_run_refuses_a_maestro_that_rejects_every_screenshot_path_and_names_the_fix(self):
        self.maestro("echo 2.11.0")
        args = type("A", (), {"cmd": "run", "config": "x.toml", "locales": None, "parallel": None, "platform": None, "no_hooks": False})()
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"PATH": f"{self.bin}:{os.environ['PATH']}"}), mock.patch.object(sf, "java_env", return_value={}), \
             mock.patch.object(sf, "apply_free_tier"), mock.patch.object(sf, "cmd_run", return_value=0) as run, contextlib.redirect_stderr(err):
            code = sf.main_dispatch(args)
        self.assertEqual(code, 2); run.assert_not_called()
        self.assertIn("shotfleet doctor --fix", err.getvalue()); self.assertIn("2.11.0", err.getvalue())

    def test_only_versions_from_2_11_are_blocked(self):
        for v in ("2.0.10", "2.7.0", "2.10.9", None, "garbage"): self.assertIsNone(sf.maestro_blocked(v), v)
        for v in ("2.11.0", "2.12.1", "3.0.0"): self.assertIn("doctor --fix", sf.maestro_blocked(v), v)

