"""Custom Android device sizes and landscape (#83): `devices` entries can be tables with a size, density and orientation."""
import sys, tempfile, unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


class CustomDevices(unittest.TestCase):
    def tearDown(self):
        for n in [n for n in sf.ANDROID_DEVICES if n not in sf.BUILTIN_ANDROID_DEVICES]: del sf.ANDROID_DEVICES[n]

    def test_names_pass_through_and_a_table_is_registered(self):
        names = sf.custom_android_devices(["phone", {"name": "tablet-10-landscape", "base": "tablet", "size": "2560x1600", "density": 320, "orientation": "landscape"}], "w")
        self.assertEqual(names, ["phone", "tablet-10-landscape"])
        d = sf.ANDROID_DEVICES["tablet-10-landscape"]
        self.assertEqual((d["size"], d["folder"], d["landscape"]), ((2560, 1600, 320), "tenInchScreenshots", True))
        self.assertIn("2560x1600_320", d["avd"])

    def test_landscape_swaps_a_portrait_size_and_portrait_swaps_back(self):
        sf.custom_android_devices([{"name": "a", "base": "tablet", "orientation": "landscape"}, {"name": "b", "size": "2400x1080", "orientation": "portrait"}, {"name": "c", "size": "1080x2400"}], "w")
        self.assertEqual(sf.ANDROID_DEVICES["a"]["size"][:2], (2560, 1440))   # the tablet's own size, turned
        self.assertEqual(sf.ANDROID_DEVICES["b"]["size"][:2], (1080, 2400))
        self.assertFalse(sf.ANDROID_DEVICES["c"]["landscape"])
        self.assertEqual(sf.ANDROID_DEVICES["c"]["folder"], "phoneScreenshots")   # base defaults to phone

    def test_a_changed_size_gets_another_emulator_name(self):
        sf.custom_android_devices([{"name": "x", "size": "1080x2400"}], "w"); first = sf.ANDROID_DEVICES["x"]["avd"]
        sf.custom_android_devices([{"name": "x", "size": "1080x2424"}], "w")
        self.assertNotEqual(first, sf.ANDROID_DEVICES["x"]["avd"])

    def test_mistakes_say_the_fix(self):
        bad = [({"name": "phone"}, "built in"), ({"size": "1080x2400"}, "needs a name"), ({"name": "a", "size": "big"}, "2560x1600"),
               ({"name": "a", "size": "100x2000"}, "320 to 3840"), ({"name": "a", "base": "watch"}, "base of"), ({"name": "a", "density": 5}, "density"),
               ({"name": "a", "orientation": "sideways"}, "orientation"), ({"name": "a", "sise": "1x1"}, "did you mean 'size'")]
        for entry, text in bad:
            with self.subTest(entry=entry), self.assertRaisesRegex(sf.Fail, text): sf.custom_android_devices([entry], "w")

    def test_the_config_accepts_tables_and_load_config_turns_them_into_names(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "shotfleet.toml"; (Path(d) / "flow.yaml").write_text("appId: x\n---\n- launchApp\n"); (Path(d) / "a.apk").write_bytes(b"x")
            cfg.write_text('[android]\napk = "a.apk"\ndevices = ["phone", {name = "land", base = "tablet", orientation = "landscape"}]\n')
            with mock.patch.object(sf, "aapt2", return_value="aapt2"), mock.patch.object(sf, "maestro_cmd", return_value="maestro"), mock.patch.object(sf, "sh", return_value=mock.Mock(stdout="package: name='x.y' ")):
                _, c, _ = sf.load_config(str(cfg))
        self.assertEqual(c["devices"], ["phone", "land"])
        self.assertIn("land", sf.ANDROID_DEVICES)
        with self.assertRaises(sf.Fail): sf.check_section({"app": "a.app", "device_types": [{"name": "x"}]}, "ios", "shotfleet.toml")


if __name__ == "__main__":
    unittest.main()
