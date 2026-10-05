"""The program must start on a Mac with nothing installed: no Android SDK, no Homebrew tools, an empty home and a bare PATH.
A NameError at import (find_sdk ran before is_mac existed) crashed `shotfleet --version` for every buyer without an Android SDK."""
import os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class StartsOnABareMachine(unittest.TestCase):
    def test_version_prints_with_an_empty_environment_and_an_empty_home(self):
        home = tempfile.mkdtemp()
        env = {"HOME": home, "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}  # no ANDROID_HOME, no ANDROID_SDK_ROOT, no adb
        r = subprocess.run([sys.executable, str(ROOT / "shotfleet.py"), "--version"], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-600:])
        self.assertRegex(r.stdout.strip(), r"^shotfleet \d+\.\d+\.\d+")

    def test_doctor_and_check_help_also_start_with_an_empty_environment(self):
        home = tempfile.mkdtemp()
        env = {"HOME": home, "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}
        for args in (["doctor", "--help"], ["check", "--help"], ["run", "--help"]):
            r = subprocess.run([sys.executable, str(ROOT / "shotfleet.py"), *args], env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, (args, r.stderr[-400:]))


if __name__ == "__main__":
    unittest.main()
