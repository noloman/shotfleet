"""Capture reliability (research/limits-capture-reliability-2026-10-05.md): hangs and leftovers, tested with stubs. No device, simulator or Maestro."""
import json, os, signal, subprocess, sys, time, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shotfleet as sf
from test_claims_unit import FleetCase


class RunGuarded(unittest.TestCase):
    def test_a_helper_that_keeps_the_output_open_does_not_block_the_return(self):
        # a daemonised process that inherited Maestro's stdout and outlives it (found on 2026-10-05: communicate() waited 8 s here, for ever in real life)
        helper = "import subprocess; subprocess.Popen(['sleep', '8'], start_new_session=True)"
        t = time.monotonic()
        r = sf.run_guarded(["/bin/sh", "-c", f"python3 -c \"{helper}\"; echo done"], timeout=60)
        self.assertEqual(r.stdout, "done\n"); self.assertLess(time.monotonic() - t, 5)

    def test_the_output_of_a_killed_run_is_kept(self):
        with self.assertRaises(subprocess.TimeoutExpired) as e:
            sf.run_guarded(["/bin/sh", "-c", "echo before; sleep 30"], timeout=1)
        self.assertIn("before", e.exception.output)


class PoolBoot(unittest.TestCase):
    def test_a_simulator_that_wedges_while_booting_leaves_none_booted(self):
        shut = []
        class FakeSim:
            def __init__(self, udid): self.udid = udid
            def run(self, *a, check=True):
                if a[0] == "bootstatus" and a[1] == "U2": raise RuntimeError("simctl bootstatus did not answer within 900 s")
                return ""
        def fake_sh(cmd, **k):
            if "list" in cmd: return subprocess.CompletedProcess(cmd, 0, json.dumps({"devices": {"rt": []}}), "")
            if "shutdown" in cmd: shut.append(cmd[-1])
            n = fake_sh.n = getattr(fake_sh, "n", 0) + 1
            return subprocess.CompletedProcess(cmd, 0, f"U{n - 0}" if "create" in cmd else "", "")
        with mock.patch.object(sf, "sh", fake_sh), mock.patch.object(sf, "Sim", FakeSim), mock.patch.object(sf, "OUR_SIMS", set()):
            with self.assertRaises(RuntimeError): sf.make_pool(3, "dt", "rt")
            booted = set(sf.OUR_SIMS)
            sf.shutdown_sims()
        self.assertEqual(len(booted), 3)  # all three were booted before the wait began, so all three are shut down
        self.assertEqual(set(shut), booted)


class OneRunPerDeviceSet(unittest.TestCase):
    def test_a_second_run_on_the_same_devices_is_refused_until_the_first_ends(self):
        key = f"test-{os.getpid()}"
        try:
            with sf.device_lock(key):
                with self.assertRaises(sf.Fail) as e:
                    with sf.device_lock(key): self.fail("two runs at once")
                self.assertIn("another shotfleet run", str(e.exception)); self.assertIn(f"pid {os.getpid()}", str(e.exception))
                with sf.device_lock(key + "-other"): pass  # other devices are free
            with sf.device_lock(key): pass  # released
        finally:
            for k in (key, key + "-other"): Path(f"/tmp/shotfleet-{k}.lock").unlink(missing_ok=True)

    def test_a_lock_file_that_cannot_be_made_does_not_stop_the_run(self):
        with mock.patch.object(os, "open", side_effect=PermissionError("no /tmp")):
            with sf.device_lock("x"): pass


class Cleanup(unittest.TestCase):
    def test_an_emulator_that_does_not_answer_adb_does_not_keep_the_others_running(self):
        stuck = subprocess.Popen(["sleep", "60"])
        calls = []
        class Emu:
            def __init__(self, serial, proc): self.serial, self.proc = serial, proc
            def adb(self, *a, check=True, timeout=180):
                calls.append(self.serial)
                if self.serial == "emulator-5702": raise subprocess.TimeoutExpired("adb", timeout)
        try:
            with mock.patch.object(sf, "EMU_STOP_WAIT_S", 1):
                sf.stop_emulators([Emu("emulator-5702", stuck), Emu("emulator-5704", None)])
            self.assertEqual(calls, ["emulator-5702", "emulator-5704"])
            self.assertIsNotNone(stuck.wait(timeout=10))  # its process tree was killed
        finally:
            if stuck.poll() is None: stuck.kill()

    def test_closing_the_terminal_cleans_up_like_ctrl_c(self):
        seen = {}
        def dispatch(a): seen["hup"] = signal.getsignal(signal.SIGHUP); return 0
        old = {s: signal.getsignal(s) for s in (signal.SIGHUP, signal.SIGTERM)}
        try:
            with mock.patch.object(sf, "main_dispatch", dispatch): sf.main_cmd(None)
        finally:
            for s, h in old.items(): signal.signal(s, h)
        self.assertIs(seen["hup"], sf.on_sigterm)


class PartialResults(FleetCase):
    """An emulator or simulator that stops answering in the middle of a run must not throw away what the earlier steps captured."""
    def test_android_emulator_hanging_in_round_two_keeps_round_one_and_reports_the_rest(self):
        test = self
        def pool_with_a_hang(n, cfg, pool):
            class Emu:
                serial = "emulator-5702"
                def adb(self, *a, check=True, timeout=180):
                    if a[:3] == ("shell", "pm", "clear"):
                        test.clears = getattr(test, "clears", 0) + 1
                        if test.clears == 2: raise RuntimeError("adb shell did not answer within 180 s: emulator-5702 is not responding")
                    return ""
            pool.append(Emu())
        self.buy()
        with mock.patch.object(sf, "android_pool", side_effect=pool_with_a_hang):
            code, out, err = self.main("run", self.config(), "--platform", "android", "--parallel", "1")
        self.assertEqual(code, 1, out + err)  # a failed run, not a crash (exit 2)
        report = json.loads((self.d / "out-android" / "run.json").read_text())["locales"]
        self.assertEqual(sum(bool(v.get("ok")) for v in report.values()), 1)
        self.assertEqual(sum("not captured" in (v.get("error") or "") for v in report.values()), 3)
        self.assertIn("emulators stopped answering in r2", out)
        self.assertEqual(len(list((self.d / "out-android" / "raw").glob("*/*.png"))), 1)


if __name__ == "__main__":
    unittest.main()
