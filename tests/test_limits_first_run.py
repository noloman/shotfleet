"""First-run friction found on 2026-10-05 by walking install.sh to the first `init` from a clean HOME (research/limits-first-run-2026-10-05.md).
Nothing here touches a simulator, an emulator or the network.

Run: python3 -m unittest tests.test_limits_first_run
"""
import contextlib, io, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

INSTALL = (Path(__file__).resolve().parent.parent / "site/public/install.sh").read_text()


class InstallerWording(unittest.TestCase):
    def test_the_path_hint_says_a_new_terminal_is_needed(self):
        """~/.zshrc is read by new shells only, so the shell that ran the installer says 'command not found' until the buyer opens another."""
        line = next(l for l in INSTALL.splitlines() if "add it to your PATH" in l)
        self.assertIn("open a new Terminal window", line)

    def test_the_next_step_is_doctor_then_init_in_the_app_folder(self):
        line = next(l for l in INSTALL.splitlines() if l.startswith('echo "next:'))
        self.assertLess(line.index("shotfleet doctor"), line.index("shotfleet init"))
        self.assertIn("shotfleet activate", line)


class XcodeNotSelected(unittest.TestCase):
    """Xcode installed but `xcode-select -p` still on the Command Line Tools: simctl is 'not found' and doctor used to say 'install Xcode'."""
    def hint(self, apps):
        d = Path(tempfile.mkdtemp()); self.addCleanup(__import__("shutil").rmtree, d, True)
        paths = []
        for name, real in apps:
            (d / name).mkdir(); paths.append(str(d / name))
            if real: (d / name / "Contents/Developer").mkdir(parents=True)
        with mock.patch.object(sf.glob, "glob", lambda pat: paths):
            return sf.xcode_hint()

    def test_an_installed_xcode_is_named_with_the_command_that_selects_it(self):
        self.assertRegex(self.hint([("Xcode.app", True)]), r"installed but not selected: sudo xcode-select -s \S+/Xcode.app/Contents/Developer")

    def test_the_xcodes_manager_app_is_not_mistaken_for_xcode(self):
        self.assertIn("install Xcode from the App Store", self.hint([("Xcodes.app", False)]))

    def test_no_xcode_says_to_get_it_and_open_it_once(self):
        out = self.hint([])
        self.assertIn("App Store", out); self.assertIn("open it once", out)

    def test_doctor_puts_the_hint_on_the_simctl_line(self):
        out = io.StringIO()
        fail = subprocess.CompletedProcess([], 1, "", "xcrun: error: unable to find utility \"simctl\"")
        with mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "xcode_hint", lambda: "HINT-X"), mock.patch.object(sf, "sh", lambda *a, **k: fail), \
                mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "latest_release", lambda: None), \
                mock.patch.object(sf, "maestro_cmd", lambda: None), mock.patch.object(sf, "find_java", lambda: (True, None)), \
                contextlib.redirect_stdout(out):
            sf.cmd_doctor()
        self.assertRegex(out.getvalue(), r"MISSING xcrun simctl\s+\(iOS\)\s+-> HINT-X")


class DoctorForAnIosOnlyBuyer(unittest.TestCase):
    """A Mac with Xcode and nothing else (no Homebrew, no Android SDK): the report must say what iOS needs apart from Android's list."""
    def doctor(self, maestro, brew=False, java=True):
        d = Path(tempfile.mkdtemp()); self.addCleanup(__import__("shutil").rmtree, d, True)
        out = io.StringIO()
        ok = lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, "Ready\n" if "--warmup" in cmd else '{"runtimes": []}', "")
        with mock.patch.object(sf, "SDK", d / "sdk"), mock.patch.object(sf, "BREW", d / "brew"), mock.patch.object(sf.Path, "home", return_value=d / "home"), \
                mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "SYSTEM_SDKS", ()), \
                mock.patch.object(sf.shutil, "which", lambda c, **k: f"/usr/bin/{c}" if c in ("xcrun", "swiftc") or (brew and c == "brew") else None), \
                mock.patch.object(sf, "find_java", return_value=(java, None)), mock.patch.object(sf, "java_env", return_value={}), \
                mock.patch.object(sf, "sh", ok), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "latest_release", lambda: None), \
                mock.patch.object(sf, "ios_runtimes", lambda: ["iOS 26.4"]), mock.patch.object(sf, "maestro_cmd", lambda: "/m" if maestro else None), \
                mock.patch.object(sf, "read_maestro_version", return_value="2.11.0"), contextlib.redirect_stdout(out):
            code = sf.cmd_doctor()
        return code, out.getvalue()

    def test_ios_ready_android_not_lists_only_androids_parts_under_android(self):
        code, out = self.doctor(maestro=True)
        self.assertEqual(code, 0)
        self.assertIn("iOS: ready   Android: not ready", out)
        self.assertNotIn("iOS still needs", out)
        self.assertRegex(out, r"Android still needs: adb, emulator, avdmanager, aapt2, system image")
        self.assertIn("skip this if you only capture iOS", out)

    def test_without_maestro_both_lists_start_with_it_and_next_names_doctor_fix(self):
        code, out = self.doctor(maestro=False)
        self.assertEqual(code, 2)
        self.assertRegex(out, r"iOS still needs: maestro\n")
        self.assertRegex(out, r"Android still needs: maestro, adb")
        self.assertIn("next: fix the MISSING lines above (shotfleet doctor --fix fetches Maestro, Java", out)

    def test_no_homebrew_says_the_brew_line_will_not_work_and_what_to_run_instead(self):
        self.assertIn("No Homebrew on this Mac", self.doctor(maestro=True)[1])
        self.assertNotIn("No Homebrew", self.doctor(maestro=True, brew=True)[1])

    def test_the_java_line_offers_doctor_fix_before_brew(self):
        out = self.doctor(maestro=True, java=False)[1]
        self.assertRegex(out, r"MISSING java 17\+\s+\(both\)\s+-> shotfleet doctor --fix .*brew install openjdk@21")


if __name__ == "__main__":
    unittest.main()
