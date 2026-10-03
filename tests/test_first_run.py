"""What a new user hits in the first hour (research/first-run.md, research/cold-test-2.md, research/setup-friction.md): wrong builds,
wrong language names, a PATH without sysctl, no Xcode runtime, a config init does not overwrite. Every check here fails on the
program as it was before 2026-10-03. Nothing boots a simulator; the iOS-only paths run on mocks.

Run: python3 -m unittest tests.test_first_run
"""
import contextlib, io, json, os, plistlib, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


class Tree(unittest.TestCase):
    """A temp folder with simulator and device builds in it; the working folder is that folder."""
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.d = Path(tmp.name).resolve()
        cwd = os.getcwd(); os.chdir(self.d); self.addCleanup(os.chdir, cwd)

    def app(self, name="My.app", platform="iphonesimulator", langs=None, extra=None):
        app = self.d / name; app.mkdir(parents=True, exist_ok=True)
        (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": f"com.example.{Path(name).stem}", "DTPlatformName": platform}))
        for lp, word in (langs or {"en": "Next", "de": "Weiter"}).items():
            (app / f"{lp}.lproj").mkdir(exist_ok=True); (app / f"{lp}.lproj/Localizable.strings").write_text(f'"next" = "{word}";\n"back" = "Back {lp}";\n')
        for rel, text in (extra or {}).items():
            (app / rel).parent.mkdir(parents=True, exist_ok=True); (app / rel).write_text(text)
        return app

    def fails(self, fn, *args):
        with self.assertRaises(sf.Fail) as cm: fn(*args)
        return str(cm.exception)

    def init(self, *builds, dest="."):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()): sf.cmd_init(list(builds), dest)
        return out.getvalue()


class WrongBuilds(Tree):
    """first-run 3 and 5, cold-test 10: say what the file is and where the right one is."""
    def test_init_says_a_device_app_is_a_device_build_and_how_to_build_for_the_simulator(self):
        msg = self.fails(sf.cmd_init, [str(self.app("Dev.app", "iphoneos"))], str(self.d / "out"))
        self.assertIn("Dev.app is a device build", msg); self.assertIn("-sdk iphonesimulator", msg); self.assertNotIn("not an archive", msg)

    def test_an_archive_and_a_stray_file_name_where_the_simulator_app_lives(self):
        (self.d / "A.xcarchive").mkdir(); (self.d / "notes.txt").write_text("x")
        for build in ("A.xcarchive", "notes.txt"):
            with self.subTest(build=build):
                msg = self.fails(sf.cmd_init, [build], str(self.d / "out"))
                self.assertIn("Debug-iphonesimulator", msg)
        self.assertIn("gradlew assembleDebug", self.fails(sf.cmd_init, ["notes.txt"], str(self.d / "out")))

    def test_a_folder_that_holds_the_app_is_not_an_app_and_the_message_names_the_app(self):
        self.app("Build/Products/Debug-iphonesimulator/My.app")
        msg = self.fails(sf.cmd_init, ["Build"], str(self.d / "out"))
        self.assertIn("folder, not an .app", msg); self.assertIn("My.app", msg)

    def test_a_config_that_names_an_ipa_or_an_archive_is_not_told_the_path_is_missing(self):
        (self.d / "flow.yaml").write_text("- launchApp\n")
        (self.d / "App.ipa").write_text("x"); (self.d / "A.xcarchive").mkdir(); (self.d / "app.aab").write_text("x")
        for build, want in (("App.ipa", "an .ipa is a device build"), ("A.xcarchive", "not an archive"), ("app.aab", "other platform")):
            with self.subTest(build=build):
                (self.d / "shotfleet.toml").write_text(f'[ios]\napp = "{build}"\n')
                msg = self.fails(sf.load_config, str(self.d / "shotfleet.toml"))
                self.assertIn("isn't a simulator app", msg); self.assertIn(want, msg); self.assertNotIn("no simulator app at", msg)

    def test_an_android_section_that_names_an_ios_app_or_a_bundle_says_what_to_pass(self):
        (self.d / "flow.yaml").write_text("- launchApp\n"); (self.d / "app.aab").write_text("x")
        for build, want in (("app.aab", "can't be installed directly"), (str(self.app()), "other platform")):
            with self.subTest(build=build):
                (self.d / "shotfleet.toml").write_text(f'[android]\napk = "{build}"\n')
                msg = self.fails(sf.load_config, str(self.d / "shotfleet.toml"))
                self.assertIn("isn't an APK", msg); self.assertIn(want, msg)
        (self.d / "shotfleet.toml").write_text('[android]\napk = "nope.apk"\n')
        self.assertIn("no APK at", self.fails(sf.load_config, str(self.d / "shotfleet.toml")))  # a missing file is still just missing

    def test_a_broken_zip_is_one_line_not_four(self):
        (self.d / "a.zip").write_text("")
        msg = self.fails(sf.unpack_build, self.d / "a.zip", self.d / "into")
        self.assertNotIn("\n", msg); self.assertIn("isn't a valid .zip or .tar.gz", msg)


class LocaleNames(Tree):
    """cold-test 15: the languages the error offers are the app's own, the ones init counts."""
    def run_locales(self, only, **cfg_extra):
        app = self.app(langs={"en": "Next", "de": "Weiter"}, extra={"Frameworks/X.framework/ar.lproj/Localizable.strings": '"cancel" = "x";\n'})
        (self.d / "flow.yaml").write_text("- launchApp\n- tapOn: Next\n")
        extra = "".join(f"{k} = {v}\n" for k, v in cfg_extra.items())
        (self.d / "shotfleet.toml").write_text(f'[ios]\napp = "{app}"\n{extra}')
        with mock.patch.object(sf, "maestro_cmd", return_value="maestro"), mock.patch.object(sf, "make_pool", side_effect=sf.Fail("BOOT")), \
             mock.patch.object(sf, "latest_ios_runtime", side_effect=AssertionError("asked xcrun although the config names a runtime")), \
             mock.patch.object(sf, "shutdown_sims"), contextlib.redirect_stdout(io.StringIO()):
            return self.fails(sf.cmd_run, str(self.d / "shotfleet.toml"), only)

    def test_the_error_lists_what_the_app_ships_not_what_a_framework_brought(self):
        msg = self.run_locales(["de-DE"], runtime='"rt"')
        self.assertIn("It ships: de, en (", msg)  # not ar, which only a framework inside the app brings
        self.assertIn("case and region matter", msg)

    def test_a_config_that_names_the_runtime_does_not_need_xcrun(self):
        self.assertEqual(self.run_locales(["de"], runtime='"rt"'), "BOOT")  # latest_ios_runtime would have raised AssertionError


class NoSysctl(unittest.TestCase):
    """cold-test 7: a cron or CI PATH has no /usr/sbin."""
    def test_sysctl_is_found_by_its_absolute_path_when_the_path_lacks_it(self):
        def run(cmd, **kw):
            if cmd[0] == "sysctl": raise FileNotFoundError(2, "No such file or directory", "sysctl")
            return subprocess.CompletedProcess(cmd, 0, "2\n", "")
        with mock.patch.object(sf.subprocess, "run", run):
            self.assertEqual(sf.memory_pressure(), "2")
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(sf.fit_parallel(4), 2)

    def test_no_sysctl_at_all_means_no_pressure_not_a_crash(self):
        with mock.patch.object(sf.subprocess, "run", side_effect=FileNotFoundError(2, "No such file or directory", "sysctl")):
            self.assertEqual(sf.memory_pressure(), ""); self.assertEqual(sf.fit_parallel(4), 4); self.assertEqual(sf.overload_note(4, 4), "")


class SimulatorSetup(unittest.TestCase):
    """first-run 6: no Xcode, no runtime, a device type this Xcode lacks: each says so and what to run."""
    def sh_with(self, runtimes=None, rc=0, err="", missing=False):
        def fake(cmd, **kw):
            if missing: raise FileNotFoundError(2, "No such file or directory", "xcrun")
            return subprocess.CompletedProcess(cmd, rc, json.dumps({"runtimes": runtimes}) if runtimes is not None else "", err)
        return mock.patch.object(sf, "sh", fake)

    def test_no_xcrun_is_a_sentence_not_an_errno(self):
        with self.sh_with(missing=True): self.assertIn("iOS simulators need a Mac with Xcode", self._fail())

    def test_xcrun_that_fails_and_a_mac_with_no_ios_runtime(self):
        with self.sh_with(rc=72, err="xcrun: error: unable to find utility \"simctl\"\nmore"): msg = self._fail()
        self.assertIn("unable to find utility", msg); self.assertNotIn("more", msg)
        with self.sh_with(runtimes=[{"platform": "watchOS", "isAvailable": True, "identifier": "w"}]):
            self.assertIn("xcodebuild -downloadPlatform iOS", self._fail())

    def test_the_newest_available_ios_runtime_is_used(self):
        rts = [{"platform": "iOS", "isAvailable": True, "identifier": "a"}, {"platform": "iOS", "isAvailable": False, "identifier": "b"}]
        with self.sh_with(runtimes=rts): self.assertEqual(sf.latest_ios_runtime(), "a")

    def _fail(self):
        with self.assertRaises(sf.Fail) as cm: sf.latest_ios_runtime()
        return str(cm.exception)

    def test_a_simulator_that_cannot_be_created_says_why_and_where_the_valid_names_are(self):
        def fake(cmd, **kw):
            out = json.dumps({"devices": {}}) if "list" in cmd else ""
            return subprocess.CompletedProcess(cmd, 0 if "list" in cmd else 1, out, "" if "list" in cmd else "Invalid device type: iPhone-17-Pro-Max")
        with mock.patch.object(sf, "sh", fake), self.assertRaises(RuntimeError) as cm: sf.make_pool(1, "iPhone-17-Pro-Max", "rt")
        self.assertIn("Invalid device type: iPhone-17-Pro-Max", str(cm.exception)); self.assertIn("simctl list devicetypes", str(cm.exception))


class DoctorRuntime(unittest.TestCase):
    """first-run 6: doctor shows the iOS runtime it found, or says there is none and how to get one."""
    def doctor(self, runtimes):
        d = Path(tempfile.mkdtemp()); self.addCleanup(__import__("shutil").rmtree, d, True)
        def fake(cmd, **kw):
            if cmd[:4] == ["xcrun", "simctl", "list", "runtimes"]: return subprocess.CompletedProcess(cmd, 0, json.dumps({"runtimes": runtimes}), "")
            return subprocess.CompletedProcess(cmd, 0, "Ready\n", "")
        out = io.StringIO()
        with mock.patch.object(sf, "SDK", d / "sdk"), mock.patch.object(sf, "BREW", d / "brew"), mock.patch.object(sf.Path, "home", return_value=d / "home"), \
             mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "SYSTEM_SDKS", ()), \
             mock.patch.object(sf.shutil, "which", lambda c, **k: f"/usr/bin/{c}"), mock.patch.object(sf, "find_java", return_value=(True, None)), \
             mock.patch.object(sf, "sh", fake), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "latest_release", return_value=None), \
             mock.patch.object(sf, "read_maestro_version", return_value="2.0.10"), contextlib.redirect_stdout(out):
            sf.cmd_doctor()
        return out.getvalue()

    def test_a_runtime_is_named_and_none_is_missing_with_the_command(self):
        out = self.doctor([{"platform": "iOS", "isAvailable": True, "identifier": "x", "name": "iOS 26.4"}])
        self.assertRegex(out, r"ok\s+iOS Simulator runtime iOS 26.4")
        out = self.doctor([])
        self.assertRegex(out, r"MISSING iOS Simulator runtime\s+\(iOS\)\s+-> xcodebuild -downloadPlatform iOS")
        self.assertIn("iOS: not ready", out)


class CheckWording(Tree):
    def test_no_screenshots_found_says_jpg_counts_too(self):
        (self.d / "empty").mkdir()
        self.assertIn(".jpg", self.fails(sf.cmd_check, self.d / "empty"))

    def test_without_an_app_the_notice_says_the_verdict_is_a_hint(self):
        out = io.StringIO()
        (self.d / "empty").mkdir()
        with contextlib.redirect_stdout(out), mock.patch.object(sf, "cmd_check", return_value=0):
            sf.check_any(self.d / "empty")
        self.assertIn("misjudge short screens", out.getvalue())


class InitKeepsYourConfig(Tree):
    """cold-test 9: init does not overwrite a config, and says when that config is for another app."""
    def test_a_config_for_another_app_is_named_and_one_for_this_app_is_called_current(self):
        a, b = self.app("A.app"), self.app("B.app")
        self.init(str(a), dest="proj")
        same = self.init(str(a), dest="proj")
        self.assertIn("keeping existing proj/shotfleet.toml (it already points at this build)", same); self.assertNotIn("put this in it", same)
        other = self.init(str(b), dest="proj")
        self.assertIn("which points at", other); self.assertIn(str(a), other); self.assertIn(f"not at {b}", other); self.assertIn("put this in it", other)
        self.assertIn("A.app", (self.d / "proj/shotfleet.toml").read_text())  # still the old config

    def test_next_line_names_the_devices_the_builds_boot(self):
        self.assertIn("boots simulators,", self.init(str(self.app("A.app")), dest="p1"))
        apk = self.d / "a.apk"; apk.write_text("x")
        badging = subprocess.CompletedProcess([], 0, "package: name='com.example.a' versionCode='1'\n", "")
        real = sf.sh
        with mock.patch.object(sf, "aapt2", return_value="aapt2"), mock.patch.object(sf, "sh", lambda cmd, **kw: badging if cmd[0] == "aapt2" else real(cmd, **kw)), \
             mock.patch.object(sf, "load_strings_apk", return_value={"en": {"k": "v"}}):
            self.assertIn("boots emulators,", self.init(str(apk), dest="p2"))
            self.assertIn("boots simulators and emulators,", self.init(str(self.app("A.app")), str(apk), dest="p3"))

    def test_the_starter_flow_points_at_maestros_commands(self):
        self.assertIn("maestro.mobile.dev", sf.FLOW_TEMPLATE)


class OcrWait(Tree):
    """setup-friction 0.5: the first text recognition can take minutes; the screen must say why it is quiet."""
    def script(self, seconds):
        p = self.d / "ocr"; p.write_text(f"#!/bin/sh\nsleep {seconds}\necho Ready\n"); p.chmod(0o755); return str(p)

    def test_a_slow_first_recognition_says_so_once_and_a_fast_one_stays_quiet(self):
        out = io.StringIO()
        with mock.patch.object(sf, "OCR_NOTE_AFTER_S", 0.05), contextlib.redirect_stdout(out):
            self.assertTrue(sf.warm_up_ocr(self.script(0.5)))
        self.assertEqual(out.getvalue().count("preparing its text recognition"), 1)
        out = io.StringIO()
        with mock.patch.object(sf, "OCR_NOTE_AFTER_S", 5), contextlib.redirect_stdout(out):
            self.assertTrue(sf.warm_up_ocr(self.script(0)))
        self.assertEqual(out.getvalue(), "")


class ConfigValues(Tree):
    """The command line refuses --parallel 0 and an empty --locales; the same mistakes in shotfleet.toml used to start a run
    ("booting 0 simulators", every language instead of none)."""
    def load(self, body):
        (self.d / "flow.yaml").write_text("- launchApp\n")
        (self.d / "shotfleet.toml").write_text(f'[ios]\napp = "{self.app()}"\n{body}')
        return sf.load_config(str(self.d / "shotfleet.toml"))

    def test_zero_and_negative_counts_are_refused(self):
        for line in ("parallel = 0", "parallel = -1", "timeout_s = 0"):
            with self.subTest(line=line):
                with mock.patch.object(sf, "maestro_cmd", return_value="maestro"):
                    msg = self.fails(self.load, line)
                self.assertIn("should be 1 or more", msg); self.assertIn(line.split(" = ")[0], msg)

    def test_an_empty_locales_list_is_refused_and_a_list_of_numbers_too(self):
        with mock.patch.object(sf, "maestro_cmd", return_value="maestro"):
            self.assertIn("is empty. Remove the line", self.fails(self.load, "locales = []"))
            self.assertIn("should be a list of strings", self.fails(self.load, "locales = [1]"))
            self.assertEqual(self.load('locales = ["de"]\nparallel = 2')[1]["parallel"], 2)

    def test_a_device_type_name_without_xcrun_is_a_sentence(self):
        with mock.patch.object(sf, "sh", side_effect=FileNotFoundError(2, "No such file", "xcrun")):
            self.assertIn("iOS simulators need a Mac with Xcode", self.fails(sf.device_type_id, "iPad Pro 13-inch (M5)"))


class SdkCommandsInSentences(Tree):
    """A '# download ...' line pasted after 'Install it with:' made the whole line a shell comment."""
    def test_a_note_comes_first_and_is_not_a_comment(self):
        self.assertEqual(sf.commands_text(["# download X", "yes | a", "b"]), "download X, then run: yes | a; b")
        self.assertEqual(sf.commands_text(["brew install y", "b"]), "brew install y; b")

    def test_missing_avdmanager_on_linux_gives_a_line_you_can_paste(self):
        with mock.patch.object(sf, "is_mac", lambda: False), mock.patch.object(sf, "SDK", self.d / "sdk"), mock.patch.object(sf, "cmdline_tool", return_value=None), \
             mock.patch.object(sf.Path, "home", return_value=self.d / "home"), mock.patch.object(sf, "java_env", return_value={}):
            msg = self.fails(sf.android_pool, 1, {}, [])
        self.assertIn("avdmanager not found", msg); self.assertNotIn("with: #", msg); self.assertIn(", then run: yes | ", msg)


if __name__ == "__main__":
    unittest.main()
