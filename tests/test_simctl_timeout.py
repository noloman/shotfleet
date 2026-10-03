"""A simulator that stops answering ends the run with a message that names it; it must not hang the run."""
import contextlib, io, subprocess, sys, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf


def hang(cmd, **kw):
    raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))


class SimctlTimeout(unittest.TestCase):
    def test_a_hung_simctl_call_becomes_an_error_that_names_the_simulator_and_the_fix(self):
        with mock.patch.object(sf, "sh", side_effect=hang), self.assertRaises(RuntimeError) as cm:
            sf.Sim("UDID-1").run("install", "UDID-1", "/x/App.app")
        msg = str(cm.exception)
        self.assertIn("UDID-1", msg); self.assertIn("not responding", msg); self.assertIn("xcrun simctl shutdown UDID-1", msg)

    def test_every_call_has_a_timeout_and_boot_status_waits_longer(self):
        seen = []
        def ok(cmd, **kw): seen.append((cmd[2], kw.get("timeout"))); return subprocess.CompletedProcess(cmd, 0, "", "")
        with mock.patch.object(sf, "sh", side_effect=ok):
            sf.Sim("U").run("install", "U", "/x"); sf.Sim("U").run("bootstatus", "U", "-b")
        self.assertEqual(seen, [("install", sf.SIM_TIMEOUT_S), ("bootstatus", sf.SIM_BOOT_TIMEOUT_S)])

    def test_shutting_down_a_wedged_simulator_does_not_hang_the_cleanup(self):
        sf.OUR_SIMS.update({"A", "B"})
        err = io.StringIO()
        with mock.patch.object(sf, "sh", side_effect=hang), contextlib.redirect_stderr(err):
            sf.shutdown_sims()
        self.assertEqual(sf.OUR_SIMS, set())
        self.assertIn("xcrun simctl shutdown", err.getvalue())


if __name__ == "__main__":
    unittest.main()
