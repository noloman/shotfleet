"""An Android system image below API 33 is refused before the emulator boots (research/limits-platform-reach-2026-10-05.md):
`cmd locale set-app-locales` needs API 33, so an API 31 emulator would boot (minutes), then fail at the first language.
No emulator or SDK is touched.

Run: python3 -m unittest tests.test_api33_refusal
"""
import sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


class OlderAndroidThan33(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.avds = Path(tmp.name)
        for p in (mock.patch.object(sf, "avd_home", return_value=self.avds), mock.patch.object(sf, "java_env", return_value={}),
                  mock.patch.object(sf, "start_emu", side_effect=self.Booted)):
            p.start(); self.addCleanup(p.stop)

    class Booted(Exception): pass

    def avd(self, name, sysdir):
        d = self.avds / f"{name}.avd"; d.mkdir(); (d / "config.ini").write_text(f"hw.lcd.width=1080\nimage.sysdir.1={sysdir}\n")

    def test_a_config_image_older_than_33_is_refused_before_avdmanager_runs(self):
        with mock.patch.object(sf, "sh") as shell, self.assertRaises(sf.Fail) as e:
            sf.android_pool(1, {"system_image": "system-images;android-31;google_apis;x86_64"}, [])
        shell.assert_not_called()
        msg = str(e.exception)
        for part in ("API 31", "set-app-locales", "API 33", "minSdk", "system_image"): self.assertIn(part, msg)

    def test_an_existing_emulator_on_an_old_image_is_refused_by_name(self):
        self.avd("shotfleet_android", "system-images/android-30/google_apis/arm64-v8a/")
        with self.assertRaises(sf.Fail) as e: sf.android_pool(1, {}, [])
        self.assertIn("the emulator shotfleet_android is Android API 30", str(e.exception))

    def test_33_and_newer_images_and_unreadable_configs_go_on_to_boot(self):
        for sysdir in ("system-images/android-33/google_apis/x86_64/", "system-images/android-36.1/google_apis/arm64-v8a/"):
            d = self.avds / "shotfleet_android.avd"
            if d.exists(): (d / "config.ini").unlink(); d.rmdir()
            self.avd("shotfleet_android", sysdir)
            with self.assertRaises(self.Booted): sf.android_pool(1, {}, [])  # got past the check; the fake emulator start stops it
        (self.avds / "shotfleet_android.avd/config.ini").unlink()           # a user's AVD without a readable config: not our call to refuse
        with self.assertRaises(self.Booted): sf.android_pool(1, {}, [])


if __name__ == "__main__":
    unittest.main()
