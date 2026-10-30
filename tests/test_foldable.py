"""#99: foldable emulators (fold, fold-book, fold-tabletop) and the inner-display capture bridge."""
import sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


class FakeEmu:
    def __init__(self): self.calls = []
    def adb(self, *a, **k): self.calls.append(a)


class Foldable(unittest.TestCase):
    def test_devices_exist_and_share_one_emulator(self):
        for n in ("fold", "fold-book", "fold-tabletop"):
            k = sf.ANDROID_DEVICES[n]
            self.assertIsNone(k["size"]); self.assertEqual(k["avd"], "shotfleet_android_fold"); self.assertEqual(k["folder"], "tenInchScreenshots")
        self.assertEqual(sf.android_avd_name({}, "fold-book"), "shotfleet_android_fold")
        self.assertEqual(sf.android_avd_name({"avd_fold": "mine"}, "fold"), "mine")
        self.assertEqual(sf.android_avd_name({"avd": "p"}, "phone"), "p")

    def test_postures(self):
        e = FakeEmu(); sf.fold_state(e, sf.ANDROID_DEVICES["fold"])
        self.assertNotIn(("emu", "posture", "3"), e.calls); self.assertTrue(any("KEYCODE_WAKEUP" in c[1] for c in e.calls))
        e = FakeEmu(); sf.fold_state(e, sf.ANDROID_DEVICES["fold-book"])
        self.assertIn(("emu", "posture", "3"), e.calls)
        e = FakeEmu(); sf.fold_state(e, sf.ANDROID_DEVICES["fold-tabletop"])
        self.assertIn(("emu", "posture", "2"), e.calls)
        self.assertTrue(any(c[:4] == ("shell", "settings", "put", "system") and "user_rotation" in c for c in e.calls))
        e = FakeEmu(); sf.fold_state(e, sf.ANDROID_DEVICES["phone"]); self.assertEqual(e.calls, [])

    def test_custom_device_cannot_be_based_on_a_fold(self):
        with self.assertRaises(sf.Fail): sf.custom_android_devices([{"name": "x", "base": "fold"}], "[android]")

    def test_flow_gets_an_inner_shot_step_after_each_screenshot(self):
        out = sf.android_flow("appId: x\n---\n- launchApp\n- takeScreenshot: 01_home\n", "r1_f0", Path("r1_f0"), inner={"port": 1234, "dev": "emulator-5702"})
        self.assertIn("file: shotfleet_inner.js", out); self.assertIn('PORT: "1234"', out); self.assertIn("emulator-5702", out)
        plain = sf.android_flow("appId: x\n---\n- launchApp\n- takeScreenshot: 01_home\n", "r1_f0", Path("r1_f0"))
        self.assertNotIn("shotfleet_inner", plain)

    def test_inner_server_takes_the_picture_and_rejects_bad_names(self):
        import urllib.request, urllib.error
        with tempfile.TemporaryDirectory() as d:
            s = sf.InnerShots(); s.folder = Path(d); s.start()
            try:
                def fake_sh(cmd, **k):
                    Path(cmd[-1], "shot.png").write_bytes(b"png"); return mock.Mock(returncode=0)
                with mock.patch.object(sf, "sh", fake_sh), mock.patch.object(sf, "adb_cmd", lambda: "adb"):
                    r = urllib.request.urlopen(f"http://127.0.0.1:{s.port}/shot?dev=emulator-5702&name=r1_f0/01_home")
                    self.assertEqual(r.read(), b"ok")
                    self.assertEqual((Path(d) / "r1_f0" / "01_home.png").read_bytes(), b"png")
                    with self.assertRaises(urllib.error.HTTPError) as c:
                        urllib.request.urlopen(f"http://127.0.0.1:{s.port}/shot?dev=emulator-1;rm&name=a/b")
                    self.assertEqual(c.exception.code, 400)
            finally: s.stop()
            self.assertFalse(s)

    def test_use_inner_shots_replaces_only_existing_names(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d, "src"), Path(d, "dst"); src.mkdir(); dst.mkdir()
            (src / "a.png").write_bytes(b"inner"); (src / "b.png").write_bytes(b"inner"); (dst / "a.png").write_bytes(b"black")
            sf.use_inner_shots(src, dst)
            self.assertEqual((dst / "a.png").read_bytes(), b"inner"); self.assertFalse((dst / "b.png").exists())
            sf.use_inner_shots(Path(d, "none"), dst)

    def test_avd_fold_is_a_known_key(self):
        self.assertIn("avd_fold", sf.KEYS["android"])


if __name__ == "__main__": unittest.main()
