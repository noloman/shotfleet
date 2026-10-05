"""A simulator that stops answering ends the run with a message that names it; it must not hang the run."""
import contextlib, io, subprocess, sys, time, unittest
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
            sf.Sim("U").run("install", "U", "/x"); sf.Sim("U").run("bootstatus", "U", "-b"); sf.Sim("U").run("uninstall", "U", "x.y")
        self.assertEqual(seen, [("install", sf.SIM_TIMEOUT_S), ("bootstatus", sf.SIM_BOOT_TIMEOUT_S), ("uninstall", 60)])  # uninstall is the first call on a wedged one

    def test_installs_run_at_once_so_wedged_simulators_cost_one_timeout_not_one_each(self):
        sims = [sf.Sim(f"U{i}") for i in range(4)]
        sf.OUR_SIMS.update(s.udid for s in sims); self.addCleanup(sf.OUR_SIMS.clear)
        def install(group):  # U0 and U1 hang (stand-in for the 300 s timeout), the others answer
            time.sleep(0.5)
            if group[0].udid in ("U0", "U1"): raise RuntimeError("simctl terminate did not answer within 300 s")
        t0 = time.monotonic()
        with mock.patch.object(sf, "sh"), contextlib.redirect_stdout(io.StringIO()):
            pool = sf.healthy_installs(sims, 4, install)
        self.assertLess(time.monotonic() - t0, 1.5)  # one round of 0.5 s, not 4 x 0.5 s in turn
        self.assertEqual([s.udid for s in pool], ["U2", "U3"])
        with mock.patch.object(sf, "sh"), contextlib.redirect_stdout(io.StringIO()):  # k < pool: a dead one is replaced by the next, in pool order
            self.assertEqual([s.udid for s in sf.healthy_installs(sims, 2, install)], ["U2", "U3"])

    def test_shutting_down_a_wedged_simulator_does_not_hang_the_cleanup(self):
        sf.OUR_SIMS.update({"A", "B"})
        err = io.StringIO()
        with mock.patch.object(sf, "sh", side_effect=hang), contextlib.redirect_stderr(err):
            sf.shutdown_sims()
        self.assertEqual(sf.OUR_SIMS, set())
        self.assertIn("xcrun simctl shutdown", err.getvalue())


if __name__ == "__main__":
    unittest.main()
