"""0.1.9: `run` and `init`, like `check`, do not carry on with a Flutter, React Native, MAUI or Unity build and no `strings`.
Found while fixing `check` (test_019_rn_check): run and init printed the hint and went on with the libraries' own strings, so the
pre-check complained about text that was never the app's. Fakes and fixtures only: no device, no lock, no simulator.

Run: python3 -m unittest tests.test_019_run_init
"""
import contextlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf
from tests.test_018_capture_check import quiet
from tests.test_019_rn_check import BUILDS, apk, ios_app, LIB

IOS = {"React Native": "React-Core_privacy.bundle/PrivacyInfo.xcprivacy", "Flutter": "Frameworks/App.framework/flutter_assets/AssetManifest.bin",
       "Unity": "Frameworks/UnityFramework.framework/UnityFramework", ".NET MAUI": "Microsoft.Maui.dll"}


class Reached(Exception): pass  # raised by the first step after the strings are read: the run got past the guard


class RunNeedsStrings(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.path = lambda p=".": self.d / p

    def go(self, kind, build, **cfg):
        """Run the strings step of run for an iOS app or an APK; no device is ever touched (Reached comes right after the strings)."""
        key, inner = ("app", sf.ios_run_inner) if kind == "ios" else ("apk", sf.android_run_inner)
        cfg = {key: str(build), "flow": "flow.yaml", "package": "com.x", "bundle_id": "com.x", **cfg}
        with contextlib.ExitStack() as st:
            st.enter_context(mock.patch.object(sf, "note_partly_translated", side_effect=Reached))
            st.enter_context(mock.patch.object(sf, "resolve_base", return_value="en"))
            st.enter_context(mock.patch.object(sf, "latest_ios_runtime", return_value="ios"))
            st.enter_context(mock.patch.object(sf, "default_device_type", return_value="iphone"))
            st.enter_context(mock.patch.object(sf, "make_pool", side_effect=AssertionError("a simulator was booted")))
            st.enter_context(mock.patch.object(sf, "android_pool", side_effect=AssertionError("an emulator was booted")))
            st.enter_context(mock.patch.object(sf, "load_strings_apk", return_value=LIB))
            st.enter_context(mock.patch.object(sf, "load_strings", return_value=LIB))
            (self.d / "flow.yaml").write_text("appId: x\n---\n- launchApp\n")
            return quiet(inner, cfg, self.path, None, None) if kind == "ios" else quiet(inner, cfg, self.path, self.d / "out", None, None)

    def test_every_framework_apk_asks_for_strings_in_the_config(self):
        for name, (member, glob) in BUILDS.items():
            with self.subTest(name), self.assertRaises(sf.Fail) as e: self.go("android", apk(self.d, member))
            self.assertIn(f"This is a {name} build: set strings = '{glob}' in shotfleet.toml", str(e.exception))
            self.assertNotIn("--strings", str(e.exception))  # run has no such option

    def test_every_framework_ios_app_asks_for_strings_in_the_config(self):
        for name, member in IOS.items():
            with self.subTest(name), self.assertRaises(sf.Fail) as e: self.go("ios", ios_app(self.d, member, f"{name.split()[-1]}.app"))
            self.assertIn(f"This is a {name} build: set strings = '{BUILDS[name][1]}' in shotfleet.toml", str(e.exception))

    def test_a_config_strings_key_is_enough(self):
        (self.d / "l10n").mkdir()
        for lp in ("en", "de"): (self.d / f"l10n/app_{lp}.arb").write_text(json.dumps({"@@locale": lp, "hello": "Hello" if lp == "en" else "Hallo"}))
        for kind, build in (("android", apk(self.d, BUILDS["Flutter"][0])), ("ios", ios_app(self.d, IOS["Flutter"]))):
            with self.subTest(kind), self.assertRaises(Reached): self.go(kind, build, strings="l10n/*.arb")

    def test_an_ordinary_build_still_reads_its_own_strings(self):
        for kind, build in (("android", apk(self.d, "classes.dex", "plain.apk")), ("ios", ios_app(self.d, "Base.lproj/Main.storyboardc", "Plain.app"))):
            with self.subTest(kind), self.assertRaises(Reached): self.go(kind, build)

    def test_the_apk_base_locale_still_reaches_the_reader(self):
        with mock.patch.object(sf, "load_strings_apk", return_value=LIB) as read:
            sf.build_strings(apk(self.d, "classes.dex", "plain.apk"), "fr")
        self.assertEqual(read.call_args.args[1], "fr")


class InitNeedsStrings(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); self.dest = self.d / "cfg"

    def init(self, build, **kw):
        with mock.patch.object(sf, "detect_project", return_value=kw.get("project")), mock.patch.object(sf, "maestro_cmd", return_value="maestro"), \
             mock.patch.object(sf, "load_strings", return_value=LIB), mock.patch.object(sf, "load_strings_apk", return_value=LIB), \
             mock.patch.object(sf, "aapt2", return_value="aapt2"), mock.patch.object(sf, "sh", return_value=mock.Mock(stdout="package: name='com.x'")):
            return quiet(sf.cmd_init, [str(build)], self.dest)

    def test_a_framework_build_without_strings_writes_the_config_then_asks(self):
        for name, member in IOS.items():
            dest = self.dest = self.d / name.split()[-1]
            with self.subTest(name), self.assertRaises(sf.Fail) as e: self.init(ios_app(self.d, member, f"{name.split()[-1]}.app"))
            self.assertIn(f"set strings = '{BUILDS[name][1]}'", str(e.exception))
            toml = (dest / "shotfleet.toml").read_text()
            self.assertIn(f'# strings = "{BUILDS[name][1]}"', toml)  # the file holds the app's path and the line to fill in
            self.assertTrue((dest / "flow.yaml").is_file())

    def test_no_languages_are_listed_from_the_libraries_strings(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out), self.assertRaises(sf.Fail):
            with mock.patch.object(sf, "detect_project", return_value=None), mock.patch.object(sf, "load_strings", return_value=LIB):
                sf.cmd_init([str(ios_app(self.d, IOS["Flutter"]))], self.dest)
        self.assertNotIn("languages (", out.getvalue())

    def test_an_apk_is_treated_the_same(self):
        with self.assertRaises(sf.Fail) as e: self.init(apk(self.d, BUILDS["React Native"][0]))
        self.assertIn("set strings = 'src/locales/*/translation.json'", str(e.exception))
        self.assertIn("[android]", (self.dest / "shotfleet.toml").read_text())

    def test_translation_files_found_in_the_project_are_enough(self):
        project = sf.Project("Flutter", "lib/l10n/*.arb")
        (self.d / "proj/lib/l10n").mkdir(parents=True)
        for lp in ("en", "de"): (self.d / f"proj/lib/l10n/app_{lp}.arb").write_text(json.dumps({"@@locale": lp, "hello": lp}))
        with mock.patch.object(sf.Path, "cwd", return_value=self.d / "proj"):
            code, out = self.init(ios_app(self.d, IOS["Flutter"]), project=project)
        self.assertEqual(code, 0)
        self.assertIn('strings = "', (self.dest / "shotfleet.toml").read_text()); self.assertIn("2 languages", out)

    def test_a_config_that_is_already_there_with_strings_is_enough(self):
        self.dest.mkdir()
        (self.dest / "shotfleet.toml").write_text('[ios]\napp = "x.app"\nstrings = "l10n/*.arb"\n')
        code, _ = self.init(ios_app(self.d, IOS["Flutter"]))
        self.assertEqual(code, 0)

    def test_an_existing_config_without_strings_still_asks(self):
        self.dest.mkdir()
        (self.dest / "shotfleet.toml").write_text('[ios]\napp = "x.app"\n')
        with self.assertRaises(sf.Fail): self.init(ios_app(self.d, IOS["Flutter"]))
        self.assertEqual((self.dest / "shotfleet.toml").read_text(), '[ios]\napp = "x.app"\n')  # init never rewrites a config

    def test_an_ordinary_build_is_unchanged(self):
        code, out = self.init(ios_app(self.d, "Base.lproj/Main.storyboardc", "Plain.app"))
        self.assertEqual(code, 0); self.assertIn("languages (", out)
        self.assertNotIn("# strings", (self.dest / "shotfleet.toml").read_text())


if __name__ == "__main__": unittest.main()
