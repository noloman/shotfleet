"""The default iPhone type falls back to the newest `iPhone N Pro Max` this Xcode lists when it has no iPhone 17 Pro Max;
an explicit device_type is never changed (research/limits-platform-reach-2026-10-05.md). No simulator is touched.

Run: python3 -m unittest tests.test_device_type_fallback
"""
import json, subprocess, sys, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf
from tests import test_claims_unit as cu


def types(*names):
    return json.dumps({"devicetypes": [{"name": n, "identifier": "com.apple.CoreSimulator.SimDeviceType." + n.replace(" ", "-").replace("(", "").replace(")", "")} for n in names]})


class DefaultDeviceType(unittest.TestCase):
    def test_xcode_with_the_iphone_17_pro_max_keeps_the_old_default(self):
        self.assertEqual(sf.default_device_type(types("iPhone 16 Pro Max", "iPhone 17 Pro Max", "iPad Pro 13-inch (M5)")), sf.DEFAULT_IPHONE)

    def test_an_older_xcode_gets_its_newest_pro_max_not_a_missing_type(self):
        listed = types("iPhone 15 Pro Max", "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 9 Pro Max", "iPad Pro 13-inch (M4)")
        self.assertEqual(sf.default_device_type(listed), "com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro-Max")  # 16, not the string-sorted 9

    def test_nothing_usable_or_unreadable_falls_back_to_the_old_default_and_simctl_names_the_problem(self):
        for listed in (types("iPad Pro 13-inch (M4)"), "", "not json", "[]"):
            self.assertEqual(sf.default_device_type(listed), sf.DEFAULT_IPHONE)

    def test_it_asks_simctl_once_with_a_timeout_and_survives_a_dead_simctl(self):
        seen = []
        def ok(cmd, **kw): seen.append((cmd, kw.get("timeout"))); return subprocess.CompletedProcess(cmd, 0, types("iPhone 16 Pro Max"), "")
        with mock.patch.object(sf, "sh", ok):
            self.assertTrue(sf.default_device_type().endswith("iPhone-16-Pro-Max"))
        self.assertEqual(seen, [(["xcrun", "simctl", "list", "devicetypes", "-j"], 60)])
        with mock.patch.object(sf, "sh", side_effect=subprocess.TimeoutExpired("x", 60)):
            self.assertEqual(sf.default_device_type(), sf.DEFAULT_IPHONE)
        with mock.patch.object(sf, "sh", side_effect=FileNotFoundError("xcrun")):
            self.assertEqual(sf.default_device_type(), sf.DEFAULT_IPHONE)


class RunUsesIt(cu.FleetCase):
    """Through `run`: the simulator pool gets the fallback type only when the config names no device_type."""
    OLD = "com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro-Max"

    def run_ios(self, ios=""):
        with mock.patch.object(sf, "default_device_type", return_value=self.OLD) as default:
            code, out, err = self.main("run", self.config(ios=ios, android=None))
        self.assertEqual(code, 0, err)
        return default

    def test_no_device_type_in_the_config_gets_the_fallback(self):
        self.run_ios()
        self.assertEqual(set(self.device_types), {self.OLD})

    def test_an_explicit_device_type_is_never_changed(self):
        explicit = "com.apple.CoreSimulator.SimDeviceType.iPhone-15-Pro"
        default = self.run_ios(ios=f'device_type = "{explicit}"\n')
        self.assertEqual(set(self.device_types), {explicit})
        default.assert_not_called()


if __name__ == "__main__":
    unittest.main()
