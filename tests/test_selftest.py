"""tools/selftest.sh: syntax, --help, and a run against a FAKE release folder. No network, nothing installed outside its own temp dir."""
import glob, os, subprocess, sys, tempfile, unittest
from pathlib import Path

SH = Path(__file__).resolve().parent.parent / "tools/selftest.sh"
FAKE = """#!/bin/sh
case "$1" in
  --version) echo "shotfleet 9.9.9" ;;
  doctor) echo "ok   text recognition (fake)"; exit 2 ;;
  check) while [ $# -gt 0 ]; do [ "$1" = --report ] && R=$2; shift; done
         mkdir -p "$R"; echo '{}' > "$R/check.json"; echo "checked 2 screenshots (fake)" ;;
esac
"""


def sh(*a, **kw):
    return subprocess.run(["sh", str(SH), *a], capture_output=True, text=True, timeout=300, **kw)


class Selftest(unittest.TestCase):
    def test_syntax(self):
        self.assertEqual(subprocess.run(["sh", "-n", str(SH)]).returncode, 0)

    def test_help_and_usage_errors_need_no_mac(self):
        r = sh("--help"); self.assertEqual(r.returncode, 0); self.assertIn("--download", r.stdout)
        self.assertEqual(sh("--bogus").returncode, 2)
        self.assertEqual(sh().returncode, 2)

    @unittest.skipUnless(sys.platform == "darwin", "the script is for macOS")
    def test_fake_release_folder_passes_and_cleans_up(self):
        before = set(glob.glob("/tmp/shotfleet-selftest.*"))
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d, "shotfleet"); exe.write_text(FAKE); exe.chmod(0o755)
            r = sh("--folder", d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("===== shotfleet selftest: PASS =====", r.stdout)
        self.assertIn("--version: ok   shotfleet 9.9.9", r.stdout)
        self.assertEqual(set(glob.glob("/tmp/shotfleet-selftest.*")), before)

    @unittest.skipUnless(sys.platform == "darwin", "the script is for macOS")
    def test_empty_folder_fails(self):
        with tempfile.TemporaryDirectory() as d:
            r = sh("--folder", d)
        self.assertEqual(r.returncode, 1); self.assertIn("selftest: FAIL", r.stdout)


if __name__ == "__main__":
    unittest.main()
