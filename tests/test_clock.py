"""[android] root and clock (#81, #82): the config is validated, the emulator gets root, auto time off, the date, and the status bar shows the same time."""
import sys, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


class FakeEmu:
    serial = "emulator-5702"
    def __init__(self, root_reply=""): self.calls, self.root_reply = [], root_reply
    def adb(self, *a, check=True):
        self.calls.append(a)
        return self.root_reply if a[0] == "root" else ""


class Clock(unittest.TestCase):
    def test_parse_clock(self):
        self.assertEqual(sf.parse_clock("2026-10-27 10:00", "x").hour, 10)
        self.assertEqual(sf.parse_clock("2026-10-27 10:00:30", "x").second, 30)
        for bad in ("10:00", "27/10/2026 10:00", "2026-10-27", ""):
            with self.subTest(bad=bad), self.assertRaisesRegex(sf.Fail, r'clock = "2026-10-27 10:00"'): sf.parse_clock(bad, "[android] clock")

    def test_config_accepts_clock_and_root_and_refuses_a_bad_clock(self):
        sf.check_section({"apk": "a.apk", "clock": "2026-10-27 10:00", "root": True}, "android", "shotfleet.toml")
        sf.check_section({"app": "a.app", "clock": "2026-10-27 10:00"}, "ios", "shotfleet.toml")
        with self.assertRaisesRegex(sf.Fail, "clock"): sf.check_section({"apk": "a.apk", "clock": "tomorrow"}, "android", "shotfleet.toml")
        with self.assertRaises(sf.Fail): sf.check_section({"app": "a.app", "root": True}, "ios", "shotfleet.toml")  # Android only

    def test_demo_mode_shows_the_clock_time_and_defaults_to_941(self):
        when = sf.parse_clock("2026-10-27 10:05", "x")
        self.assertIn("am broadcast -a com.android.systemui.demo -e command clock -e hhmm 1005", sf.demo_mode(when))
        self.assertEqual(sf.demo_mode(), sf.DEMO_MODE)
        self.assertTrue(any("hhmm 0941" in c for c in sf.DEMO_MODE))

    def test_android_clock_turns_auto_time_off_then_sets_the_date(self):
        e = FakeEmu(); sf.android_clock(e, sf.parse_clock("2026-10-27 10:00", "x"))
        self.assertEqual([c[1] for c in e.calls], ["settings put global auto_time 0", "settings put global auto_time_zone 0", "date 102710002026.00"])

    def test_root_is_refused_with_the_reason_on_a_play_store_image(self):
        e = FakeEmu("adbd cannot run as root in production builds")
        with self.assertRaisesRegex(sf.Fail, "Google APIs"): sf.android_root(e)

    def test_root_waits_for_adbd(self):
        e = FakeEmu("restarting adbd as root")
        with mock.patch.object(sf, "sh") as sh: sf.android_root(e)
        self.assertIn("wait-for-device", sh.call_args[0][0])

    def test_ios_status_bar_gets_the_clock_time(self):
        calls = []
        class Sim:
            def __init__(self, udid): self.udid = udid
            def run(self, *a, check=True): calls.append(a)
        listing = '{"devices": {"rt": []}}'
        with mock.patch.object(sf, "simctl_sh", return_value=mock.Mock(stdout=listing, stderr="")), mock.patch.object(sf, "Sim", Sim), \
             mock.patch.object(sf, "OUR_SIMS", set()), mock.patch.object(sf, "run_setup"):
            # the pool is created through simctl_sh("create"): its stdout is the udid
            with mock.patch.object(sf, "simctl_sh", side_effect=lambda *a: mock.Mock(stdout=listing if a[0] == "list" else "U1", stderr="")):
                sf.make_pool(1, "dt", "rt", clock=sf.parse_clock("2026-10-27 00:05", "x"))
        bar = [c for c in calls if c[0] == "status_bar"][0]
        self.assertEqual(bar[bar.index("--time") + 1], "0:05")


if __name__ == "__main__":
    unittest.main()
