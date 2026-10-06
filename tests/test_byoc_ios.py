"""Bring your own capture on iOS ([capture]): shotfleet runs a team's own XCUITest screenshot tests on its simulator pool.
No simulator, xcodebuild or Maestro is used: every xcrun call is faked. The device test is tools/fixture-byoc-e2e.sh (opt-in)."""
import contextlib, io, json, os, plistlib, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf
sf.USE_DEVICE_LOCK = False

CAPTURE = '[capture]\nbuild = "true"\nxctestrun = "build/Build/Products/*.xctestrun"\n'


def write(d, text):
    (Path(d) / "shotfleet.toml").write_text(text)
    return str(Path(d) / "shotfleet.toml")


class CaptureConfig(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def load(self, text):
        with mock.patch.object(sf, "maestro_cmd", return_value=None):  # capture mode must not need Maestro
            return sf.load_config(write(self.d, text))

    def fails(self, text, words):
        with self.assertRaises(sf.Fail) as cm: self.load(text)
        self.assertIn(words, str(cm.exception))

    def test_capture_without_flow_or_app_loads_and_needs_no_maestro(self):
        platform, cfg, _ = self.load('[ios]\nlocales = ["de", "ja"]\n' + CAPTURE)
        self.assertEqual(platform, "ios")
        self.assertEqual(cfg["_capture"]["xctestrun"], "build/Build/Products/*.xctestrun")
        self.assertNotIn("flow", cfg)

    def test_flow_and_capture_together_are_refused(self):
        self.fails('[ios]\nflow = "flow.yaml"\n' + CAPTURE, "Use one")

    def test_a_flow_config_without_capture_still_needs_app_and_flow(self):
        self.fails('[ios]\nlocales = ["de"]\n', "missing: app")

    def test_capture_needs_build_and_xctestrun(self):
        self.fails('[ios]\n[capture]\nxctestrun = "x/*.xctestrun"\n', "missing build")
        self.fails('[ios]\n[capture]\nbuild = "make"\n', "missing xctestrun")
        self.fails('[ios]\n[capture]\nbuild = " "\nxctestrun = "x"\n', "missing build")

    def test_bad_screenshots_value_typo_and_types_are_refused(self):
        self.fails('[ios]\n' + CAPTURE + 'screenshots = "both"\n', '"auto" (both), not \'both\'')
        self.fails('[ios]\n' + CAPTURE + 'screenshot = "auto"\n', "did you mean 'screenshots'?")
        self.fails('[ios]\n' + CAPTURE + 'timeout = "900"\n', "timeout in shotfleet.toml should be a whole number")
        self.fails('[ios]\n' + CAPTURE + 'timeout = 0\n', "1 or more seconds")
        self.fails('[ios]\n' + CAPTURE + 'only_testing = "A/B"\n', "only_testing in shotfleet.toml should be a list")
        self.fails('[ios]\n' + CAPTURE + 'only_testing = [1]\n', "list of test names")

    def test_every_screenshots_value_is_accepted(self):
        for v in sf.CAPTURE_SHOTS:
            self.assertEqual(self.load('[ios]\n' + CAPTURE + f'screenshots = "{v}"\n')[1]["_capture"]["screenshots"], v)

    def test_capture_is_ios_only(self):
        (Path(self.d) / "a.apk").write_bytes(b"")
        self.fails('[android]\napk = "a.apk"\n' + CAPTURE, "needs an [ios] section")

    def test_android_section_next_to_capture_keeps_its_flow(self):
        with mock.patch.object(sf, "sh", return_value=mock.Mock(stdout="package: name='a.b'")), mock.patch.object(sf, "aapt2", return_value="aapt2"), \
             mock.patch.object(sf, "maestro_cmd", return_value="maestro"):
            (Path(self.d) / "a.apk").write_bytes(b""); (Path(self.d) / "flow.yaml").write_text("- launchApp\n")
            _, cfg, _ = sf.load_config(write(self.d, '[ios]\n[android]\napk = "a.apk"\n' + CAPTURE), "android")
        self.assertIsNone(cfg["_capture"]); self.assertEqual(cfg["flow"], "flow.yaml")


# manifest.json as `xcrun xcresulttool export attachments` wrote it in experiment E4 (Xcode 27.0), one test, 2 screenshots
MANIFEST = [{"attachments": [
    {"configurationName": "Test Scheme Action", "deviceId": "49AA2BD4-B262-4891-9B05-E3FA06093FD8", "deviceName": "byoc-e4-de",
     "exportedFileName": "3B27D4D2-C9D8-47FC-B942-6F27E7F1A9EA.png", "isAssociatedWithFailure": False,
     "suggestedHumanReadableName": "02Settings_0_6232EC24-4CAA-4AFA-B012-EFE755D104BD.png", "timestamp": 1791304707.732},
    {"configurationName": "Test Scheme Action", "deviceId": "49AA2BD4-B262-4891-9B05-E3FA06093FD8", "deviceName": "byoc-e4-de",
     "exportedFileName": "19473290-4472-47B4-9DF6-239A2308A41D.png", "isAssociatedWithFailure": False,
     "suggestedHumanReadableName": "01Welcome_0_17023C40-2DA9-4EEC-B1BF-B5F48E30CDB1.png", "timestamp": 1791304707.109}],
    "testIdentifier": "ScreenshotTests/testScreenshots()"}]


def fake_export(manifest, files):
    """A stand-in for `xcrun xcresulttool export attachments`: writes manifest.json and the <UUID>.png files into --output-path."""
    calls = []
    def sh(cmd, **kw):
        calls.append(cmd)
        out = Path(cmd[cmd.index("--output-path") + 1])
        (out / "manifest.json").write_text(json.dumps(manifest))
        for name, data in files.items(): (out / name).write_bytes(data)
        return sf.subprocess.CompletedProcess(cmd, 0, "", "")
    return sh, calls


class AttachmentCollector(unittest.TestCase):
    def test_names_come_from_the_manifest_without_the_index_and_uuid(self):
        sh, calls = fake_export(MANIFEST, {"3B27D4D2-C9D8-47FC-B942-6F27E7F1A9EA.png": b"settings", "19473290-4472-47B4-9DF6-239A2308A41D.png": b"welcome"})
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "sh", sh):
            dst = Path(d) / "raw/de"
            names = sf.xcresult_pngs(Path(d) / "de.xcresult", dst)
            self.assertEqual(sorted(names), ["01Welcome.png", "02Settings.png"])
            self.assertEqual((dst / "01Welcome.png").read_bytes(), b"welcome")
            self.assertEqual(sorted(p.name for p in dst.iterdir()), ["01Welcome.png", "02Settings.png"])
        self.assertEqual(calls[0][:4], ["xcrun", "xcresulttool", "export", "attachments"])
        self.assertEqual(calls[0][-2:], ["--filter", "*.png"])

    def test_a_name_used_twice_keeps_both_and_warns(self):
        twice = [{"attachments": [dict(MANIFEST[0]["attachments"][1], exportedFileName="A.png"),
                                  dict(MANIFEST[0]["attachments"][1], exportedFileName="B.png")]}]
        sh, _ = fake_export(twice, {"A.png": b"a", "B.png": b"b"})
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "sh", sh), contextlib.redirect_stdout(io.StringIO()) as out:
            names = sf.xcresult_pngs(Path(d) / "x.xcresult", Path(d) / "raw")
        self.assertEqual(names, ["01Welcome.png", "01Welcome-2.png"])
        self.assertIn("two screenshots are named 01Welcome", out.getvalue())

    def test_an_empty_manifest_is_no_screenshots(self):  # SnapshotHelper never attaches: E5 got an empty manifest
        sh, _ = fake_export([], {})
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "sh", sh):
            self.assertEqual(sf.xcresult_pngs(Path(d) / "x.xcresult", Path(d) / "raw"), [])
            self.assertFalse((Path(d) / "raw").exists())


class FastlaneCollector(unittest.TestCase):
    def test_takes_only_this_simulators_files_and_strips_the_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            cache, dst = Path(d) / "screenshots", Path(d) / "raw/de"; cache.mkdir()
            for n in ("shotfleet-1-01Home.png", "shotfleet-1-02Prices.png", "shotfleet-10-01Home.png", "shotfleet-2-01Home.png", "shotfleet-1-notes.txt"):
                (cache / n).write_bytes(n.encode())
            self.assertEqual(sf.fastlane_pngs(cache, "shotfleet-1", dst), ["01Home.png", "02Prices.png"])
            self.assertEqual((dst / "01Home.png").read_bytes(), b"shotfleet-1-01Home.png")
            self.assertEqual(sorted(p.name for p in cache.iterdir()), ["shotfleet-1-notes.txt", "shotfleet-10-01Home.png", "shotfleet-2-01Home.png"])

    def test_settings_files_are_moved_aside_and_put_back(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / "screenshots"; cache.mkdir(); (cache / "language.txt").write_text("de-DE"); (cache / "locale.txt").write_text("de_DE")
            with sf.fastlane_cache(cache) as folder:
                self.assertEqual(folder, cache)
                self.assertFalse((cache / "language.txt").exists()); self.assertFalse((cache / "locale.txt").exists())
            self.assertEqual((cache / "language.txt").read_text(), "de-DE"); self.assertEqual((cache / "locale.txt").read_text(), "de_DE")
            self.assertEqual(sorted(p.name for p in cache.iterdir()), ["language.txt", "locale.txt"])  # no aside folder left

    def test_settings_files_come_back_when_the_run_fails(self):
        for err in (RuntimeError("xcodebuild died"), KeyboardInterrupt()):
            with tempfile.TemporaryDirectory() as d:
                cache = Path(d) / "screenshots"; cache.mkdir(); (cache / "snapshot-launch_arguments.txt").write_text("-x")
                with self.assertRaises(type(err)), sf.fastlane_cache(cache): raise err
                self.assertEqual((cache / "snapshot-launch_arguments.txt").read_text(), "-x")

    def test_a_folder_shotfleet_made_is_removed_and_one_that_existed_is_kept(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / "tools.fastlane/screenshots"
            with sf.fastlane_cache(cache): self.assertTrue(cache.is_dir())
            self.assertFalse((Path(d) / "tools.fastlane").exists())  # the parent was made too, so it goes too
            cache.mkdir(parents=True)
            with sf.fastlane_cache(cache): pass
            self.assertTrue(cache.is_dir())

    def test_files_a_killed_run_left_aside_are_put_back_first(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / "screenshots"; (cache / ".shotfleet-aside").mkdir(parents=True); (cache / ".shotfleet-aside/language.txt").write_text("ja")
            with sf.fastlane_cache(cache): self.assertFalse((cache / "language.txt").exists())
            self.assertEqual((cache / "language.txt").read_text(), "ja")



def xctestrun_plist(fmt=1, app="__TESTROOT__/Debug-iphonesimulator/My.app"):
    target = {"BlueprintName": "MyUITests", "IsUITestBundle": True, "UITargetAppPath": app, "UITargetAppCommandLineArguments": ["-demo"],
              "DependentProductPaths": ["__TESTROOT__/Debug-iphonesimulator/MyUITests-Runner.app", app]}
    if fmt == 2:
        target.pop("UITargetAppPath")  # subscrifi's format-2 file had none: the app comes from DependentProductPaths
        return {"TestConfigurations": [{"Name": "Test Scheme Action", "TestTargets": [target]}], "__xctestrun_metadata__": {"FormatVersion": 2}}
    return {"MyUITests": target, "__xctestrun_metadata__": {"FormatVersion": 1}}


class XctestrunCopy(unittest.TestCase):
    def test_copy_sits_beside_the_original_with_the_language_arguments_in_both_formats(self):
        for fmt in (1, 2):
            with tempfile.TemporaryDirectory() as d:
                src = Path(d) / "Build/Products/My_iphonesimulator27.0-arm64.xctestrun"; src.parent.mkdir(parents=True)
                src.write_bytes(plistlib.dumps(xctestrun_plist(fmt)))
                copy = sf.xctestrun_with_language(src, "pt-BR")
                self.assertEqual(copy.parent, src.parent)  # a moved .xctestrun fails: __TESTROOT__ is its own folder
                self.assertEqual(copy.name, "My_iphonesimulator27.0-arm64.shotfleet-pt-BR.xctestrun")
                target = sf.xctestrun_targets(plistlib.loads(copy.read_bytes()))[0]
                self.assertEqual(target["UITargetAppCommandLineArguments"], ["-demo", "-AppleLanguages", "(pt-BR)", "-AppleLocale", "pt_BR"])
                self.assertEqual(sf.xctestrun_targets(plistlib.loads(src.read_bytes()))[0]["UITargetAppCommandLineArguments"], ["-demo"])  # original untouched
                self.assertEqual(sf.xctestrun_app(src), src.parent / "Debug-iphonesimulator/My.app")

    def test_the_glob_must_match_one_file_and_ignores_shotfleets_copies(self):
        with tempfile.TemporaryDirectory() as d:
            path = lambda p: Path(d) / p
            with self.assertRaises(sf.Fail) as cm: sf.find_xctestrun("P/*.xctestrun", path)
            self.assertIn("no .xctestrun matches P/*.xctestrun", str(cm.exception))
            (Path(d) / "P").mkdir(); (Path(d) / "P/A.xctestrun").write_bytes(b""); (Path(d) / "P/A.shotfleet-de.xctestrun").write_bytes(b"")
            self.assertEqual(sf.find_xctestrun("P/*.xctestrun", path).name, "A.xctestrun")
            (Path(d) / "P/B.xctestrun").write_bytes(b"")
            with self.assertRaises(sf.Fail) as cm: sf.find_xctestrun("P/*.xctestrun", path)
            self.assertIn("2 .xctestrun files match", str(cm.exception))


class SimulatorLanguage(unittest.TestCase):
    def test_the_simulators_global_language_and_locale_are_written(self):
        calls = []
        class S:
            udid = "U1"
            def run(self, *a, check=True): calls.append(a)
        for lp in ("pt-BR", "de", "zh-Hans"): sf.set_sim_language(S(), lp)
        self.assertEqual(calls, [
            ("spawn", "U1", "defaults", "write", "-g", "AppleLanguages", "-array", "pt-BR"), ("spawn", "U1", "defaults", "write", "-g", "AppleLocale", "-string", "pt_BR"),
            ("spawn", "U1", "defaults", "write", "-g", "AppleLanguages", "-array", "de"), ("spawn", "U1", "defaults", "write", "-g", "AppleLocale", "-string", "de_DE"),
            ("spawn", "U1", "defaults", "write", "-g", "AppleLanguages", "-array", "zh-Hans"), ("spawn", "U1", "defaults", "write", "-g", "AppleLocale", "-string", "zh_CN")])

    def test_simctl_goes_through_the_timed_simulator_wrapper(self):  # a wedged simulator must raise, not hang
        seen = []
        def sh(cmd, **kw): seen.append((cmd, kw.get("timeout"))); return sf.subprocess.CompletedProcess(cmd, 0, "", "")
        with mock.patch.object(sf, "sh", sh): sf.set_sim_language(sf.Sim("U9"), "ja")
        self.assertEqual(seen[0][0][:4], ["xcrun", "simctl", "spawn", "U9"]); self.assertEqual(seen[0][1], sf.SIM_TIMEOUT_S)


WORDS = {"en": "Next", "de": "Weiter", "ja": "次へ", "tr": "İleri"}


class CaptureRun(unittest.TestCase):
    """`shotfleet run` with [capture], every device and xcrun call faked."""
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()).resolve()
        products = self.d / "build/Build/Products"; app = products / "Debug-iphonesimulator/My.app"
        for lp, word in WORDS.items():
            (app / f"{lp}.lproj").mkdir(parents=True); (app / f"{lp}.lproj/Localizable.strings").write_text(f'"next" = "{word}";\n')
        (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.example.my", "CFBundleLocalizations": list(WORDS)}))
        self.xctestrun = products / "My_iphonesimulator27.0-arm64.xctestrun"; self.xctestrun.write_bytes(plistlib.dumps(xctestrun_plist()))
        self.cache = self.d / "home/Library/Caches/tools.fastlane/screenshots"
        self.shots = {"de": ["01Welcome", "02Settings"], "ja": ["01Welcome", "02Settings"], "tr": ["01Welcome", "02Settings"]}
        self.sim_calls, self.xcodebuild, self.builds, self.mode = [], [], [], "attachments"
        for p in (mock.patch.object(sf, "make_pool", side_effect=self.fake_make_pool), mock.patch.object(sf, "run_guarded", side_effect=self.fake_run),
                  mock.patch.object(sf, "xcresult_pngs", side_effect=self.fake_attachments), mock.patch.object(sf, "FASTLANE_CACHE", self.cache),
                  mock.patch.object(sf, "fit_parallel", side_effect=lambda n: n), mock.patch.object(sf, "capacity_warn"),
                  mock.patch.object(sf, "kill_stale_drivers"), mock.patch.object(sf, "shutdown_sims"), mock.patch.object(sf, "OUR_SIMS", set()),
                  mock.patch.object(sf, "latest_ios_runtime", return_value="com.apple.CoreSimulator.SimRuntime.iOS-27-0"),
                  mock.patch.object(sf, "default_device_type", return_value=sf.DEFAULT_IPHONE), mock.patch.object(sf, "maestro_cmd", return_value=None),
                  mock.patch.object(sf, "cmd_check", return_value=0), mock.patch.object(sf, "LOCALE_CAP", None), mock.patch.object(sf, "NO_BUILD", False),
                  mock.patch.dict(os.environ, {"SHOTFLEET_HOME": str(self.d / "sfhome")})):
            p.start(); self.addCleanup(p.stop)

    def config(self, extra="", ios='locales = ["de", "ja"]\nparallel = 2\n'):
        return write(self.d, f'[ios]\n{ios}\n[capture]\nbuild = "make screenshots-build"\nxctestrun = "build/Build/Products/*.xctestrun"\n'
                             f'only_testing = ["MyUITests/ScreenshotTests"]\nscreenshots = "{self.mode}"\n{extra}')

    def fake_make_pool(self, n, device_type, runtime, prefix="shotfleet", simctl=()):
        calls = self.sim_calls
        class S:
            def __init__(self, i): self.udid, self.name = f"U{i}", f"{prefix}-{i}"
            def run(self, *a, check=True): calls.append((self.udid, *a)); return ""
        return [S(i + 1) for i in range(n)]

    def fake_run(self, cmd, timeout=None, env=None, cwd=None, progress=None, stall_s=None):
        if cmd[0] == "/bin/sh":
            self.builds.append((cmd[2], cwd)); return sf.subprocess.CompletedProcess(cmd, 0, "built", "")
        run_file = Path(cmd[cmd.index("-xctestrun") + 1]); udid = cmd[cmd.index("-destination") + 1][3:]
        args = sf.xctestrun_targets(plistlib.loads(run_file.read_bytes()))[0]["UITargetAppCommandLineArguments"]
        lp = args[args.index("-AppleLanguages") + 1].strip("()")
        self.xcodebuild.append({"udid": udid, "lp": lp, "cmd": cmd, "run_file": run_file, "timeout": timeout, "started": time.monotonic()})
        time.sleep(0.05)  # long enough for two simulators to overlap
        if self.mode != "attachments":  # SnapshotHelper: <simulator name>-<shot>.png in the one shared folder
            for shot in self.shots.get(lp, []): (self.cache / f"shotfleet-{udid[1:]}-{shot}.png").write_bytes(f"{lp}/{shot}".encode())
        Path(cmd[cmd.index("-resultBundlePath") + 1]).mkdir(parents=True)
        return sf.subprocess.CompletedProcess(cmd, 0, "** TEST SUCCEEDED **", "")

    def fake_attachments(self, bundle, dst):
        names = [] if self.mode == "fastlane" else self.shots.get(Path(bundle).stem, [])
        for n in names: Path(dst).mkdir(parents=True, exist_ok=True); (Path(dst) / f"{n}.png").write_bytes(f"{Path(bundle).stem}/{n}".encode())
        return [f"{n}.png" for n in names]

    def run_it(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            code = sf.main(["run", self.config(), *args])
        return code, out.getvalue() + err.getvalue()

    def test_builds_once_then_runs_each_language_on_its_own_simulator_in_parallel(self):
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.builds, [("make screenshots-build", self.d)])
        self.assertEqual(sorted(r["lp"] for r in self.xcodebuild), ["de", "ja"])
        self.assertEqual(len({r["udid"] for r in self.xcodebuild}), 2)
        a, b = self.xcodebuild
        self.assertLess(abs(a["started"] - b["started"]), 0.05)  # at once, not one after the other
        for r in self.xcodebuild:
            cmd = r["cmd"]
            self.assertEqual(cmd[:2], ["xcodebuild", "test-without-building"])
            self.assertEqual(r["run_file"].parent, self.xctestrun.parent)
            self.assertIn("-only-testing:MyUITests/ScreenshotTests", cmd)
            self.assertTrue(cmd[cmd.index("-resultBundlePath") + 1].endswith(f"attempt1/{r['lp']}.xcresult"))
            self.assertEqual(r["timeout"], sf.CAPTURE_TIMEOUT_S)
            # the simulator's own language was set before its test ran, and the app uninstalled for a fresh start
            mine = [c[1:] for c in self.sim_calls if c[0] == r["udid"]]
            self.assertIn(("spawn", r["udid"], "defaults", "write", "-g", "AppleLanguages", "-array", r["lp"]), mine)
            self.assertIn(("uninstall", r["udid"], "com.example.my"), mine)
        self.assertNotIn("-testLanguage", sum((r["cmd"] for r in self.xcodebuild), []))  # ignored with -xctestrun (experiment E4)
        for lp in ("de", "ja"):
            self.assertEqual(sorted(p.name for p in (self.d / "out/raw" / lp).iterdir()), ["01Welcome.png", "02Settings.png"])
        self.assertEqual(sorted(p.name for p in self.xctestrun.parent.glob("*.xctestrun")), [self.xctestrun.name])  # copies removed
        run = json.loads((self.d / "out/run.json").read_text())
        self.assertEqual(run["app"], str(self.xctestrun.parent / "Debug-iphonesimulator/My.app"))
        self.assertTrue(all(v["ok"] and v["screenshots"] == 2 for v in run["locales"].values()))
        sf.cmd_check.assert_called_once()

    def test_more_languages_than_simulators_take_turns(self):
        code, out = self.run_it("--locales", "de,ja,tr", "--parallel", "2")
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(r["lp"] for r in self.xcodebuild), ["de", "ja", "tr"])
        self.assertEqual(len({r["udid"] for r in self.xcodebuild}), 2)

    def test_no_build_skips_the_build(self):
        code, out = self.run_it("--no-build")
        self.assertEqual(code, 0, out); self.assertEqual(self.builds, [])

    def test_a_failing_build_stops_before_any_simulator(self):
        def fail(cmd, **kw): return sf.subprocess.CompletedProcess(cmd, 65, "error: no such module 'RevenueCat'\n** TEST BUILD FAILED **", "")
        with mock.patch.object(sf, "run_guarded", side_effect=fail): code, out = self.run_it()
        self.assertEqual(code, 2); self.assertIn("the [capture] build failed (exit 65)", out); self.assertIn("no such module", out)
        self.assertEqual(self.sim_calls, [])

    def test_zero_screenshots_fails_the_language_with_the_hint_even_though_the_test_passed(self):
        self.shots = {"de": [], "ja": ["01Welcome"]}
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL de", out); self.assertIn("saved no screenshots", out)
        self.assertEqual(sorted(r["lp"] for r in self.xcodebuild), ["de", "de", "ja"])  # retried once, like a failed flow
        run = json.loads((self.d / "out/run.json").read_text())
        self.assertFalse(run["locales"]["de"]["ok"]); self.assertIn(".keepAlways", run["locales"]["de"]["error"])
        self.assertTrue(run["locales"]["ja"]["ok"])

    def test_nothing_at_all_says_so_and_does_not_check(self):
        self.shots = {}
        code, out = self.run_it()
        self.assertEqual(code, 1); self.assertIn("see the errors above and the xcodebuild logs", out); sf.cmd_check.assert_not_called()

    def test_a_screen_missing_in_one_language_fails_that_language(self):
        self.shots = {"de": ["01Welcome", "02Settings"], "ja": ["01Welcome"]}
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        run = json.loads((self.d / "out/run.json").read_text())
        self.assertTrue(run["locales"]["de"]["ok"])
        self.assertEqual(run["locales"]["ja"]["error"], "missing 02Settings (other languages saved them)")

    def test_a_failing_test_fails_the_language_and_keeps_its_log(self):
        real = self.fake_run
        def fails_for_ja(cmd, **kw):
            r = real(cmd, **kw)
            return sf.subprocess.CompletedProcess(cmd, 65, "** TEST FAILED **", "") if cmd[0] == "xcodebuild" and "shotfleet-ja" in cmd[3] else r
        with mock.patch.object(sf, "run_guarded", side_effect=fails_for_ja): code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("xcodebuild failed (exit 65", out)
        self.assertIn("TEST FAILED", (self.d / "out/.work/capture/attempt2/ja.log").read_text())

    def test_a_hung_simulator_is_stopped_and_the_language_retried(self):
        real, hung = self.fake_run, []
        def stalls_once(cmd, **kw):
            if cmd[0] == "xcodebuild" and not hung:
                hung.append(cmd); e = sf.subprocess.TimeoutExpired(cmd, 900, output="Testing started"); e.stalled = True; raise e
            return real(cmd, **kw)
        with mock.patch.object(sf, "run_guarded", side_effect=stalls_once): code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertIn("retrying 1", out)
        self.assertEqual(len(self.xcodebuild), 2)  # the stalled call never reached the fake

    def test_fastlane_snapshot_files_are_collected_per_simulator_and_its_settings_restored(self):
        self.mode = "fastlane"
        self.cache.mkdir(parents=True); (self.cache / "language.txt").write_text("en-US")
        (self.cache / "shotfleet-1-old.png").write_bytes(b"from an interrupted run")
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        for lp in ("de", "ja"):
            self.assertEqual(sorted(p.name for p in (self.d / "out/raw" / lp).iterdir()), ["01Welcome.png", "02Settings.png"])
            self.assertEqual((self.d / "out/raw" / lp / "01Welcome.png").read_bytes(), f"{lp}/01Welcome".encode())
        self.assertEqual(sorted(p.name for p in self.cache.iterdir()), ["language.txt"])
        self.assertEqual((self.cache / "language.txt").read_text(), "en-US")

    def test_auto_collects_both_and_removes_the_fastlane_folder_it_made(self):
        self.mode = "auto"
        self.shots = {"de": ["01Welcome"], "ja": ["01Welcome"]}  # the fake writes both an attachment and a SnapshotHelper file
        code, out = self.run_it()
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(p.name for p in (self.d / "out/raw/de").iterdir()), ["01Welcome.png"])  # same name: the fastlane file replaces the attachment
        self.assertFalse(self.cache.parent.exists())

    def test_attachments_only_never_touches_the_fastlane_folder(self):
        code, out = self.run_it()
        self.assertEqual(code, 0, out); self.assertFalse(self.cache.parent.exists())

    def test_without_a_licence_three_languages_become_two_like_a_maestro_run(self):
        with mock.patch.object(sf.sys, "frozen", True, create=True), mock.patch.object(sf, "LICENCE_FILE", self.d / "no-licence.json"), \
             mock.patch.dict(os.environ, {"SHOTFLEET_KEY": ""}):
            code, out = self.run_it("--locales", "de,ja,tr")
        self.assertEqual(code, 0, out)
        self.assertEqual(sf.LOCALE_CAP, sf.FREE_LANGUAGES)
        self.assertIn("free tier: capturing 2 of 3 languages", out)
        self.assertEqual(sorted(r["lp"] for r in self.xcodebuild), ["de", "ja"])

    def test_two_languages_without_a_licence_are_free(self):
        with mock.patch.object(sf.sys, "frozen", True, create=True), mock.patch.object(sf, "LICENCE_FILE", self.d / "no-licence.json"), \
             mock.patch.dict(os.environ, {"SHOTFLEET_KEY": ""}):
            code, out = self.run_it()
        self.assertEqual(code, 0, out); self.assertNotIn("free tier: capturing", out)
        self.assertEqual(sorted(r["lp"] for r in self.xcodebuild), ["de", "ja"])

    def test_check_stays_free_on_capture_output(self):
        self.run_it()
        with mock.patch.object(sf.sys, "frozen", True, create=True), mock.patch.object(sf, "LICENCE_FILE", self.d / "no-licence.json"), \
             mock.patch.object(sf, "require_licence", side_effect=AssertionError("check must not ask for a licence")):
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(sf.main(["check", str(self.d / "out")]), 0)



class Doctor(unittest.TestCase):
    """doctor reads the config it is pointed at (default ./shotfleet.toml) to see which mode is in use."""
    def doctor(self, toml, *args, fix=False):
        d = Path(tempfile.mkdtemp())
        ocr = d / "ocr"; ocr.write_text("#!/bin/sh\necho Ready\n"); ocr.chmod(0o755)
        if toml is not None: (d / "shotfleet.toml").write_text(toml)
        out, plans = io.StringIO(), []
        with mock.patch.object(sf, "maestro_cmd", lambda: None), mock.patch.object(sf, "find_java", lambda: (False, None)), \
             mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf.sys, "frozen", True, create=True), \
             mock.patch.object(sf.shutil, "which", lambda c: f"/usr/bin/{c}"), mock.patch.object(sf, "simctl_works", lambda: True), \
             mock.patch.object(sf, "ios_runtimes", lambda: ["iOS 26.4"]), mock.patch.object(sf, "ocr_tool", lambda: str(ocr)), \
             mock.patch.object(sf, "latest_release", lambda: None), mock.patch.object(sf, "run_fix_plan", lambda plan, yes: plans.append(plan) or 0), \
             contextlib.redirect_stdout(out):
            cwd = os.getcwd(); os.chdir(d)
            try: code = sf.cmd_doctor(fix, False, *args)
            finally: os.chdir(cwd)
        return code, out.getvalue(), plans

    def test_capture_config_makes_ios_ready_without_maestro_or_java(self):
        code, out, _ = self.doctor('[ios]\n' + CAPTURE)
        self.assertEqual(code, 0, out)
        self.assertIn("iOS: ready", out)
        self.assertIn("runs your XCUITest tests on iOS ([capture]), so iOS needs Xcode, not Maestro or Java", out)
        self.assertRegex(out, r"MISSING maestro +\(Android\)")

    def test_a_flow_config_or_none_still_needs_maestro_for_ios(self):
        for toml in ('[ios]\napp = "My.app"\n', None):
            code, out, _ = self.doctor(toml)
            self.assertIn("iOS: not ready", out); self.assertRegex(out, r"MISSING maestro +\(both\)"); self.assertNotIn("[capture]", out)

    def test_a_config_named_on_the_command_line_is_the_one_read(self):
        d = Path(tempfile.mkdtemp()); write(d, '[ios]\n' + CAPTURE)
        _, out, _ = self.doctor(None, str(d / "shotfleet.toml"))
        self.assertIn("iOS: ready", out)

    def test_fix_offers_no_maestro_for_an_ios_capture_config_but_does_for_its_android_section(self):
        _, _, plans = self.doctor('[ios]\n' + CAPTURE, fix=True)
        self.assertFalse(any("Maestro" in what or "Java" in what for what, _ in plans[0]))
        _, _, plans = self.doctor('[ios]\n[android]\napk = "a.apk"\n' + CAPTURE, fix=True)
        self.assertTrue(any("Maestro" in what for what, _ in plans[0]))

    def test_an_unreadable_config_is_the_flow_mode(self):
        self.assertEqual(sf.capture_mode("/nonexistent/shotfleet.toml"), (False, True))
        d = Path(tempfile.mkdtemp()); (d / "x.toml").write_text("[ios\n")
        self.assertEqual(sf.capture_mode(d / "x.toml"), (False, True))


SCHEME = """<?xml version="1.0" encoding="UTF-8"?>
<Scheme><BuildAction/><TestAction><Testables>
  <TestableReference skipped="NO"><BuildableReference BuildableIdentifier="primary" BuildableName="MyAppTests.xctest" BlueprintName="MyAppTests"/></TestableReference>
  <TestableReference skipped="NO"><BuildableReference BuildableIdentifier="primary" BuildableName="MyAppUITests.xctest" BlueprintName="MyAppUITests"/></TestableReference>
</Testables></TestAction>
<LaunchAction><BuildableProductRunnable><BuildableReference BuildableName="MyApp.app" BlueprintName="MyApp"/></BuildableProductRunnable></LaunchAction></Scheme>
"""


class InitCapture(unittest.TestCase):
    def init(self, setup=None, builds=()):
        d = Path(tempfile.mkdtemp()).resolve()
        if setup: setup(d)
        cwd = os.getcwd(); os.chdir(d)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(out): code = sf.main(["init", "--capture", *builds])
        finally: os.chdir(cwd)
        return d, code, out.getvalue()

    def test_writes_a_capture_config_from_the_shared_scheme_with_ui_tests(self):
        def project(d):
            schemes = d / "MyApp.xcodeproj/xcshareddata/xcschemes"; schemes.mkdir(parents=True)
            (schemes / "MyApp.xcscheme").write_text(SCHEME.replace("MyAppUITests", "Nope").replace("<TestableReference skipped=\"NO\"><BuildableReference BuildableIdentifier=\"primary\" BuildableName=\"Nope.xctest\" BlueprintName=\"Nope\"/></TestableReference>", ""))
            (schemes / "MyApp-shared.xcscheme").write_text(SCHEME)
        d, code, out = self.init(project)
        self.assertEqual(code, 0, out)
        self.assertFalse((d / "flow.yaml").exists())
        doc = sf.tomllib.loads((d / "shotfleet.toml").read_text())
        self.assertEqual(doc["capture"]["build"], "xcodebuild build-for-testing -project MyApp.xcodeproj -scheme MyApp-shared "
                         "-destination 'generic/platform=iOS Simulator' -derivedDataPath .shotfleet/build CODE_SIGNING_ALLOWED=NO")
        self.assertEqual(doc["capture"]["only_testing"], ["MyAppUITests"])
        self.assertEqual(doc["capture"]["screenshots"], "auto")
        with mock.patch.object(sf, "maestro_cmd", return_value=None):
            _, cfg, _ = sf.load_config(d / "shotfleet.toml")  # what init writes is a valid config
        self.assertEqual(cfg["_capture"]["timeout"], sf.CAPTURE_TIMEOUT_S)
        self.assertIn("scheme MyApp-shared, UI tests MyAppUITests", out)

    def test_without_a_project_it_writes_a_placeholder_and_says_so(self):
        d, code, out = self.init()
        self.assertEqual(code, 0)
        self.assertIn("-scheme '<scheme>'", (d / "shotfleet.toml").read_text())
        self.assertIn("# only_testing", (d / "shotfleet.toml").read_text())
        self.assertIn("no Xcode project or workspace found", out)

    def test_an_existing_config_is_kept_and_the_section_printed(self):
        d, code, out = self.init(lambda d: (d / "shotfleet.toml").write_text('[ios]\napp = "My.app"\n'))
        self.assertEqual((d / "shotfleet.toml").read_text(), '[ios]\napp = "My.app"\n')
        self.assertIn("keeping existing", out); self.assertIn("[capture]", out)

    def test_a_build_argument_is_refused(self):
        _, code, _ = self.init(builds=["My.app"])
        self.assertEqual(code, 2)



ROOT = Path(__file__).resolve().parent.parent
E2E = ROOT / "tools/fixture-byoc-e2e.sh"


class DeviceTestScript(unittest.TestCase):
    """tools/fixture-byoc-e2e.sh boots simulators, so here it is only run where it refuses or explains itself."""
    def run_script(self, *args, env=None):
        return sf.subprocess.run(["sh", str(E2E), *args], capture_output=True, text=True, env={**os.environ, "SHOTFLEET_E2E": "", **(env or {})}, timeout=60)

    def test_it_refuses_without_the_opt_in_before_touching_anything(self):
        fake = Path(tempfile.mkdtemp()); (fake / "xcrun").write_text("#!/bin/sh\necho called >> \"$0.log\"\n"); (fake / "xcrun").chmod(0o755)
        r = self.run_script(env={"PATH": f"{fake}:{os.environ['PATH']}"})
        self.assertEqual(r.returncode, 2); self.assertIn("SHOTFLEET_E2E=1", r.stderr)
        self.assertFalse((fake / "xcrun.log").exists())

    def test_help_and_unknown_options(self):
        r = self.run_script("--help"); self.assertEqual(r.returncode, 0); self.assertIn("Hard limit", r.stdout)
        self.assertEqual(self.run_script("--nope").returncode, 2)

    def test_the_tests_it_names_exist_in_the_fixture(self):
        script, tests = E2E.read_text(), (ROOT / "tools/fixture-app/UITests/ScreenshotTests.swift").read_text()
        for cls in ("ScreenshotTests", "SnapshotStyleTests", "NoKeepTests"):
            self.assertIn(f" {cls} ", script); self.assertIn(f"final class {cls}: XCTestCase", tests)
        self.assertIn("a.lifetime = .keepAlways", tests)

    def test_init_capture_finds_the_fixtures_ui_test_scheme(self):
        self.assertEqual(sf.ui_test_scheme(ROOT / "tools/fixture-app/FleetFixture.xcodeproj"), ("FleetFixture", "FleetFixtureUITests"))


if __name__ == "__main__":
    unittest.main()
