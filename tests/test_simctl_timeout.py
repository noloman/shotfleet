"""A simulator that stops answering ends the run with a message that names it; it must not hang the run."""
import contextlib, io, json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf


def hang(cmd, **kw):
    raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))


class SimctlTimeout(unittest.TestCase):
    def setUp(self):  # hung-simulator markers go to a throwaway SHOTFLEET_HOME, never the real ~/.shotfleet
        self.home = Path(tempfile.mkdtemp())
        p = mock.patch.dict(os.environ, {"SHOTFLEET_HOME": str(self.home)}); p.start(); self.addCleanup(p.stop)

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

    def test_a_simulator_that_stopped_answering_is_marked_and_replaced_at_the_next_run(self):
        sims = [sf.Sim("U0"), sf.Sim("U1")]
        def install(group):
            if group[0].udid == "U0": raise RuntimeError("simctl uninstall did not answer within 60 s")
        with mock.patch.object(sf, "sh"), contextlib.redirect_stdout(io.StringIO()):
            sf.healthy_installs(sims, 2, install)
        self.assertTrue(sf.hung_marker("U0").exists()); self.assertFalse(sf.hung_marker("U1").exists())
        sf.mark_hung("MINE")  # a marker on someone else's simulator (not a pool name) must never get it deleted
        devices = [{"name": n, "udid": u, "isAvailable": True, "deviceTypeIdentifier": "dt"}
                   for n, u in (("shotfleet-1", "U0"), ("shotfleet-2", "U1"), ("My iPhone", "MINE"))]
        calls = []
        def fake(cmd, **kw):
            calls.append(cmd[2:])
            return subprocess.CompletedProcess(cmd, 0, json.dumps({"devices": {"rt": devices}}) if "-j" in cmd else "NEW", "")
        with mock.patch.object(sf, "sh", fake), mock.patch.object(sf.Sim, "run", return_value=""), contextlib.redirect_stdout(io.StringIO()) as out:
            pool = sf.make_pool(2, "dt", "rt")
        self.addCleanup(sf.OUR_SIMS.clear)
        self.assertEqual([s.udid for s in pool], ["NEW", "U1"])  # U0 deleted and recreated under its name, U1 reused
        self.assertEqual([c for c in calls if c[0] in ("shutdown", "delete", "create")],
                         [["shutdown", "U0"], ["delete", "U0"], ["create", "shotfleet-1", "dt", "rt"]])
        self.assertIn("shotfleet-1 stopped answering last run", out.getvalue())
        self.assertFalse(sf.hung_marker("U0").exists()); self.assertTrue(sf.hung_marker("MINE").exists())

    def test_a_hung_simulator_that_cannot_be_deleted_is_used_as_before_and_stays_marked(self):
        sf.mark_hung("U0")
        devices = [{"name": "shotfleet-1", "udid": "U0", "isAvailable": True, "deviceTypeIdentifier": "dt"}]
        def fake(cmd, **kw):
            if "delete" in cmd: raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
            return subprocess.CompletedProcess(cmd, 0, json.dumps({"devices": {"rt": devices}}), "")
        with mock.patch.object(sf, "sh", fake), mock.patch.object(sf.Sim, "run", return_value=""), contextlib.redirect_stdout(io.StringIO()) as out:
            pool = sf.make_pool(1, "dt", "rt")
        self.addCleanup(sf.OUR_SIMS.clear)
        self.assertEqual([s.udid for s in pool], ["U0"])
        self.assertIn("xcrun simctl delete U0", out.getvalue()); self.assertTrue(sf.hung_marker("U0").exists())

    def test_shutting_down_a_wedged_simulator_does_not_hang_the_cleanup(self):
        sf.OUR_SIMS.update({"A", "B"})
        err = io.StringIO()
        with mock.patch.object(sf, "sh", side_effect=hang), contextlib.redirect_stderr(err):
            sf.shutdown_sims()
        self.assertEqual(sf.OUR_SIMS, set())
        self.assertIn("xcrun simctl shutdown", err.getvalue())


if __name__ == "__main__":
    unittest.main()
