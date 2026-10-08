"""0.1.9: `check` on any Flutter, React Native, MAUI or Unity build without --strings asks for --strings (exit 2), on Android and iOS,
whichever way the build is found. Found on the Obytes Expo template: --app app-release.apk printed the hint and then reported
"ar: the app has no ar translation". Fakes and fixtures only: no device, no text recognition.

Run: python3 -m unittest tests.test_019_rn_check
"""
import contextlib, json, plistlib, sys, tempfile, unittest, zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf
from tests.test_018_capture_check import check_fakes, quiet
from tests.test_shotfleet import shots_with_texts

LIB = {"en": {"ok": "OK"}, "de": {"ok": "OK"}, "fr": {"ok": "OK"}}  # what the libraries inside a framework build bring: no "ar", no app text
BUILDS = {  # framework -> (a file the build has, the folder the message must name)
    "React Native": ("assets/index.android.bundle", "src/locales/*/translation.json"),
    "Flutter": ("assets/flutter_assets/AssetManifest.bin", "lib/l10n/*.arb"),
    "Unity": ("assets/bin/Data/UnityPlayer.dll", "Localization/*.csv"),
    ".NET MAUI": ("assemblies/Microsoft.Maui.dll", "Resources/Strings/*.resx"),
}


def apk(d, member, name="app-release.apk"):
    p = Path(d) / name
    with zipfile.ZipFile(p, "w") as z: z.writestr(member, b"x"); z.writestr("resources.arsc", b"x")
    return p


def ios_app(d, member, name="App.app"):
    p = Path(d) / name; (p / member).parent.mkdir(parents=True); (p / member).write_bytes(b"x")
    (p / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.x", "UIDeviceFamily": [1]}))
    return p


class FrameworkBuildNeedsStrings(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        shots_with_texts(self.d, {"en": {"01_home": ["Home"]}, "ar": {"01_home": ["Home"]}})  # an ar listing the library strings don't have
        self.shots = self.d / "shots"

    def check(self, **kw):
        with contextlib.ExitStack() as st:
            for f in check_fakes(("en", "ar")): st.enter_context(f)
            st.enter_context(mock.patch.object(sf, "load_strings_apk", return_value=LIB))
            st.enter_context(mock.patch.object(sf, "load_strings", return_value=LIB))  # an iOS framework build with some plugin's .lproj strings
            return quiet(sf.cmd_check, self.shots, report_dir=self.d / "rep", **kw)

    def assert_asks_for_strings(self, e, name, glob):
        self.assertIn(f"This is a {name} build: pass --strings '{glob}'", str(e.exception))
        self.assertFalse((self.d / "rep/check.json").exists())  # nothing was checked, so no "no ar translation" problem

    def test_every_framework_apk_asks_for_strings(self):
        for name, (member, glob) in BUILDS.items():
            with self.subTest(name), self.assertRaises(sf.Fail) as e: self.check(app=apk(self.d, member))
            self.assert_asks_for_strings(e, name, glob)

    def test_every_framework_ios_app_asks_for_strings(self):
        ios = {"React Native": "React-Core_privacy.bundle/PrivacyInfo.xcprivacy", "Flutter": "Frameworks/App.framework/flutter_assets/AssetManifest.bin",
               "Unity": "Frameworks/UnityFramework.framework/UnityFramework", ".NET MAUI": "Microsoft.Maui.dll"}
        for name, member in ios.items():
            with self.subTest(name), self.assertRaises(sf.Fail) as e: self.check(app=ios_app(self.d, member, f"{name.split()[-1]}.app"))
            self.assert_asks_for_strings(e, name, BUILDS[name][1])

    def test_the_build_a_run_used_asks_for_strings_too(self):
        (self.shots / "run.json").write_text(json.dumps({"platform": "android", "apk": str(apk(self.d, BUILDS["React Native"][0])), "app": None}))
        with self.assertRaises(sf.Fail) as e: self.check()
        self.assert_asks_for_strings(e, "React Native", BUILDS["React Native"][1])

    def test_a_build_found_in_the_folder_is_not_compared_with(self):
        cwd = self.d / "proj"; cwd.mkdir()
        (self.shots / "metadata/android").mkdir(parents=True)
        with mock.patch.object(sf, "detect_project", return_value=None), mock.patch.object(sf, "find_builds", return_value=[str(apk(cwd, BUILDS["React Native"][0]))]):
            app, files, strings, line = sf.check_build(self.shots, cwd)
        self.assertEqual((app, files, strings), (None, None, None))
        self.assertIn("React Native build", line); self.assertIn("--strings 'src/locales/*/translation.json'", line)

    def test_an_ordinary_apk_still_reads_its_strings(self):
        plain = apk(self.d, "classes.dex", "plain.apk")
        code, out = self.check(app=plain)
        self.assertEqual(code, 1, out)  # LIB has no ar: here that is a real finding
        self.assertIn("ar", json.loads((self.d / "rep/check.json").read_text())["problems"][0])


if __name__ == "__main__": unittest.main()
