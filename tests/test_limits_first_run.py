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


if __name__ == "__main__":
    unittest.main()
