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


if __name__ == "__main__":
    unittest.main()
