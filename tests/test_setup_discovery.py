"""Roadmap X2 and X3: `shotfleet init` without a build argument, and the Android SDK / image / sdkmanager discovery in doctor.

Everything runs on fake directory trees in temp dirs (a fake home with DerivedData, fake Gradle outputs, fake SDK layouts,
a fake PATH). Nothing here boots a simulator, runs xcodebuild or gradle, or touches the real DerivedData or SDK.

Run: python3 -m unittest tests.test_setup_discovery
"""
import contextlib, io, os, plistlib, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

# These tests describe the Mac and Apple-silicon behaviour (Vision, Homebrew, arm64 images); the same code on Linux is in
# test_portable.py. The patches last for this module only.
_MAC = [mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "SYSTEM_SDKS", ()),
        mock.patch.object(sf, "ABI", "arm64-v8a"), mock.patch.object(sf, "DEFAULT_IMAGE", "system-images;android-36;google_apis;arm64-v8a")]
def setUpModule():
    for p in _MAC: p.start()
def tearDownModule():
    for p in reversed(_MAC): p.stop()


def touch(path, mtime=None, text="x"):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists(): path.write_text(text)
    path.chmod(0o755)
    if mtime is not None: os.utime(path, (mtime, mtime))
    return path


class Tree(unittest.TestCase):
    """A fake home (HOME is patched, so Path.home() is it) and a fake Homebrew prefix, all inside one temp dir."""
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.home, self.brew, self.proj = self.root / "home", self.root / "brew", self.root / "work/MyApp"
        for d in (self.home, self.brew, self.proj): d.mkdir(parents=True)
        for patch in (mock.patch.dict(os.environ, {"HOME": str(self.home), "PATH": ""}), mock.patch.object(sf, "BREW", self.brew)):
            patch.start(); self.addCleanup(patch.stop)
        os.environ.pop("ANDROID_HOME", None); os.environ.pop("ANDROID_SDK_ROOT", None)
        self.derived = self.home / "Library/Developer/Xcode/DerivedData"
        self.derived.mkdir(parents=True)

    def build(self, folder, workspace, name="MyApp", config="Debug", mtime=None, bundle_id="com.example.app", platform="iphonesimulator", plist=True):
        """A DerivedData folder pointing at `workspace`, with <name>.app built into <config>-iphonesimulator."""
        d = self.derived / folder
        if workspace is not None and plist: (d).mkdir(exist_ok=True); (d / "info.plist").write_bytes(plistlib.dumps({"WorkspacePath": str(workspace), "LastAccessedDate": 0}, fmt=plistlib.FMT_BINARY))
        app = d / f"Build/Products/{config}-iphonesimulator/{name}.app"
        app.mkdir(parents=True, exist_ok=True)
        (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": name, "CFBundleIdentifier": bundle_id, "DTPlatformName": platform}, fmt=plistlib.FMT_BINARY))
        touch(app / name)
        if mtime is not None:
            for p in (app / name, app / "Info.plist", app): os.utime(p, (mtime, mtime))
        return app

    def find(self, cwd=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out): builds = sf.find_builds(cwd or self.proj)
        return builds, out.getvalue()


class InitFindsBuilds(Tree):
    def test_picks_the_newest_debug_build_of_this_projects_xcode_project_and_says_why(self):
        xcodeproj = self.proj / "iosApp/MyApp.xcodeproj"; xcodeproj.mkdir(parents=True)
        now = time.time()
        old = self.build("MyApp-aaa", xcodeproj, mtime=now - 7200)
        new = self.build("MyApp-bbb", xcodeproj, mtime=now - 600)
        self.build("Other-ccc", self.root / "work/Other/Other.xcodeproj", mtime=now)                         # another project, newest of all
        self.build("MyApp-ddd", self.proj / ".claude/worktrees/x/iosApp/MyApp.xcodeproj", mtime=now)       # a worktree copy of this one
        self.build("MyApp-eee", xcodeproj, config="Release", mtime=now)                                    # not Debug
        self.build("MyApp-fff", self.proj / ".copy/MyApp.xcodeproj", mtime=now)                            # a hidden folder here
        self.build("MyApp-ggg", self.proj / "a/b/c/MyApp.xcodeproj", mtime=now)                            # too deep to be this project's
        builds, out = self.find()
        self.assertEqual(builds, [str(new)])
        self.assertNotEqual(builds, [str(old)])
        self.assertIn("iOS: using MyApp.app", out); self.assertIn("built 10 min ago", out)
        self.assertIn("newest of 2 Xcode build(s) of iosApp/MyApp.xcodeproj", out)

    def test_a_derived_data_folder_for_a_project_above_the_current_folder_matches_too(self):
        self.proj.joinpath("MyApp.xcodeproj").mkdir()
        app = self.build("MyApp-aaa", self.proj / "MyApp.xcodeproj")
        sub = self.proj / "Sources"; sub.mkdir()
        self.assertEqual(self.find(sub)[0], [str(app)])

    def test_a_folder_without_a_workspace_path_matches_by_the_project_name_prefix(self):
        (self.proj / "My App.xcodeproj").mkdir()
        app = self.build("My_App-abcdefgh", None)                       # no info.plist: Xcode never recorded the project
        self.build("Unrelated-zzz", None)
        self.assertEqual(self.find()[0], [str(app)])

    def test_test_runners_device_builds_and_other_configurations_are_never_chosen(self):
        xcodeproj = self.proj / "MyApp.xcodeproj"; xcodeproj.mkdir()
        self.build("MyApp-aaa", xcodeproj, name="MyAppUITests-Runner", bundle_id="com.example.app.xctrunner")
        self.build("MyApp-aaa", xcodeproj, name="DeviceApp", platform="iphoneos")
        self.build("MyApp-aaa", xcodeproj, name="Rel", config="Release")
        with self.assertRaisesRegex(sf.Fail, "no Debug simulator build or Gradle debug APK found for"):
            self.find()

    def test_newest_gradle_debug_apk_wins_the_wear_app_and_android_test_apks_do_not(self):
        now = time.time()
        phone = touch(self.proj / "app/build/outputs/apk/debug/app-debug.apk", now - 3600)
        touch(self.proj / "wearApp/build/outputs/apk/debug/wearApp-debug.apk", now - 60)                 # newer, but a watch app
        touch(self.proj / "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk", now)
        touch(self.proj / "app/build/outputs/apk/release/app-release.apk", now)
        touch(self.proj / ".claude/worktrees/w/app/build/outputs/apk/debug/app-debug.apk", now)
        with mock.patch.object(sf, "is_watch_apk", side_effect=lambda a: "wearApp" in str(a)):
            builds, out = self.find()
        self.assertEqual(builds, [str(phone)])
        self.assertIn("Android: using app/build/outputs/apk/debug/app-debug.apk", out); self.assertIn("newest of 1 Gradle debug APK", out)

    def test_apks_of_a_product_flavor_and_of_a_module_folder_next_to_cwd_are_found(self):
        flavor = touch(self.proj / "app/build/outputs/apk/free/debug/app-free-debug.apk")
        self.assertEqual(self.find()[0], [str(flavor)])
        module = touch(self.proj / "build/outputs/apk/debug/composeApp-debug.apk", time.time() + 5)
        self.assertEqual(self.find(self.proj)[0], [str(module)])

    def test_watch_badging_is_read_with_aapt2_only_to_tell_watch_apps_apart(self):
        badging = subprocess.CompletedProcess([], 0, "package: name='x'\nuses-feature: name='android.hardware.type.watch'\n", "")
        with mock.patch.object(sf, "aapt2", return_value="/aapt2"), mock.patch.object(sf, "sh", return_value=badging):
            self.assertTrue(sf.is_watch_apk("a.apk"))
        with mock.patch.object(sf, "aapt2", side_effect=sf.Fail("no aapt2")):
            self.assertFalse(sf.is_watch_apk("a.apk"))

    def test_ios_and_android_builds_are_both_returned_for_one_config(self):
        xcodeproj = self.proj / "MyApp.xcodeproj"; xcodeproj.mkdir()
        app = self.build("MyApp-aaa", xcodeproj); apk = touch(self.proj / "app/build/outputs/apk/debug/app-debug.apk")
        self.assertEqual(self.find()[0], [str(app), str(apk)])

    def test_nothing_found_prints_the_exact_commands_with_names_read_from_the_files_and_runs_no_build_tool(self):
        proj = self.proj / "iosApp/Kuokka.xcodeproj"
        scheme = proj / "xcshareddata/xcschemes/Kuokka.xcscheme"; scheme.parent.mkdir(parents=True)
        scheme.write_text('<Scheme><LaunchAction><BuildableProductRunnable><BuildableReference BuildableName = "Kuokka.app"/>'
                          '</BuildableProductRunnable></LaunchAction></Scheme>')
        touch(proj.parent / "Pods/Pods.xcodeproj/x"); touch(self.proj / "gradlew")
        with mock.patch.object(subprocess, "run", side_effect=AssertionError("init must not run anything")), \
             mock.patch.object(sf, "sh", side_effect=AssertionError("init must not run anything")):
            with self.assertRaises(sf.Fail) as e: self.find()
        msg = str(e.exception)
        self.assertIn("xcodebuild -project iosApp/Kuokka.xcodeproj -scheme Kuokka -sdk iphonesimulator -configuration Debug build", msg)
        self.assertIn("./gradlew assembleDebug", msg); self.assertNotIn("Pods", msg)

    def test_a_workspace_is_preferred_and_a_project_without_a_shared_scheme_gets_a_placeholder(self):
        (self.proj / "ios/Runner.xcodeproj").mkdir(parents=True); (self.proj / "ios/Runner.xcworkspace").mkdir()
        with self.assertRaises(sf.Fail) as e: self.find()
        self.assertIn("xcodebuild -workspace ios/Runner.xcworkspace -scheme '<scheme>' -sdk iphonesimulator -configuration Debug build", str(e.exception))
        self.assertNotIn("gradlew", str(e.exception))  # no gradlew here: no Android advice

    def test_an_unrecognised_folder_shows_both_generic_commands(self):
        with self.assertRaises(sf.Fail) as e: self.find()
        self.assertIn("xcodebuild -scheme <scheme> -sdk iphonesimulator -configuration Debug build", str(e.exception))
        self.assertIn("./gradlew assembleDebug", str(e.exception))

    def test_the_missing_platform_gets_a_note_with_its_command_when_the_other_was_found(self):
        xcodeproj = self.proj / "MyApp.xcodeproj"; xcodeproj.mkdir(); touch(self.proj / "gradlew")
        self.build("MyApp-aaa", xcodeproj)
        builds, out = self.find()
        self.assertEqual(len(builds), 1)
        self.assertIn("note: no Gradle debug APK yet; to make one: ./gradlew assembleDebug", out)

    def test_init_without_builds_writes_only_into_dir_and_reads_the_build_it_found(self):
        xcodeproj = self.proj / "MyApp.xcodeproj"; xcodeproj.mkdir()
        app = self.build("MyApp-aaa", xcodeproj, mtime=time.time())
        dest, before = self.root / "out", sorted(p.relative_to(self.root) for p in self.root.rglob("*") if "home" not in p.parts)
        cwd = os.getcwd(); self.addCleanup(os.chdir, cwd); os.chdir(self.proj)
        with mock.patch.object(sf, "load_strings", return_value={"en": {"a": "A"}, "de": {"a": "B"}}), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sf.cmd_init([], dest), 0)
        self.assertEqual(sorted(p.name for p in dest.iterdir()), ["flow.yaml", "shotfleet.toml"])
        self.assertIn(f"app = {sf.json.dumps(sf.config_path(app, dest))}", (dest / "shotfleet.toml").read_text())
        self.assertIn("com.example.app: 2 languages (de, en)", out.getvalue())
        after = sorted(p.relative_to(self.root) for p in self.root.rglob("*") if "home" not in p.parts and "out" not in p.parts)
        self.assertEqual([p for p in before if "out" not in p.parts], after)  # the project folder is untouched

    def test_init_with_nothing_to_find_creates_no_files(self):
        dest = self.root / "out"
        cwd = os.getcwd(); self.addCleanup(os.chdir, cwd); os.chdir(self.proj)
        with self.assertRaises(sf.Fail): sf.cmd_init([], dest)
        self.assertFalse(dest.exists())
        err = io.StringIO()
        with contextlib.redirect_stderr(err): self.assertEqual(sf.main(["init", "--dir", str(dest)]), 2)  # never silent: one error line, exit 2
        self.assertIn("shotfleet: no Debug simulator build or Gradle debug APK found for", err.getvalue())

    def test_explicit_builds_never_look_around_and_no_argument_is_accepted_by_the_parser(self):
        with mock.patch.object(sf, "find_builds", side_effect=AssertionError("explicit builds win")), \
             self.assertRaisesRegex(sf.Fail, "no simulator app at"):
            sf.cmd_init(["Nope.app"], self.root / "o")
        with mock.patch.object(sf, "cmd_init", return_value=0) as init:
            sf.main(["init"]); sf.main(["init", "A.app", "--dir", "d"])
        self.assertEqual([c.args for c in init.call_args_list], [([], "."), (["A.app"], "d")])


class AndroidSdkDiscovery(Tree):
    def sdk(self, where, *parts):
        for part in parts or ("platform-tools",): (Path(where) / part).mkdir(parents=True, exist_ok=True)
        return Path(where)

    def test_places_are_tried_in_order(self):
        home_sdk = self.sdk(self.home / "Library/Android/sdk")
        brew_sdk = self.sdk(self.brew / "share/android-commandlinetools", "cmdline-tools")
        cask = self.sdk(self.brew / "Caskroom/android-commandlinetools/13114758", "cmdline-tools")
        root, home_env = self.sdk(self.root / "root"), self.sdk(self.root / "home_env")
        self.assertEqual(sf.find_sdk({"ANDROID_HOME": str(home_env), "ANDROID_SDK_ROOT": str(root), "PATH": ""}), home_env)
        self.assertEqual(sf.find_sdk({"ANDROID_SDK_ROOT": str(root), "PATH": ""}), root)
        self.assertEqual(sf.find_sdk({"ANDROID_HOME": str(self.root / "gone"), "PATH": ""}), home_sdk)     # a path with no SDK in it is skipped
        import shutil; shutil.rmtree(home_sdk)
        self.assertEqual(sf.find_sdk({"PATH": ""}), brew_sdk)
        shutil.rmtree(brew_sdk)
        self.assertEqual(sf.find_sdk({"PATH": ""}), cask)

    def test_the_folder_above_an_adb_on_the_path_is_the_last_resort(self):
        sdk = self.sdk(self.root / "elsewhere/sdk")
        adb = touch(sdk / "platform-tools/adb"); adb.chmod(0o755)
        self.assertEqual(sf.find_sdk({"PATH": f"/nonexistent:{sdk / 'platform-tools'}"}), sdk)
        stray = touch(self.root / "bin/adb"); stray.chmod(0o755)   # an adb that is not inside a platform-tools folder says nothing
        self.assertEqual(sf.find_sdk({"PATH": str(self.root / "bin")}), self.home / "Library/Android/sdk")

    def test_nothing_found_falls_back_to_android_home_then_the_android_studio_default(self):
        self.assertEqual(sf.find_sdk({"PATH": "", "ANDROID_HOME": "/custom"}), Path("/custom"))
        self.assertEqual(sf.find_sdk({"PATH": ""}), self.home / "Library/Android/sdk")

    def image(self, sdk, api, tag="google_apis", abi="arm64-v8a", installed=True):
        d = sdk / "system-images" / f"android-{api}" / tag / abi; d.mkdir(parents=True, exist_ok=True)
        if installed: (d / "package.xml").write_text("<x/>")

    def test_any_installed_api_33_plus_arm64_image_is_used_newest_first(self):
        sdk = self.sdk(self.root / "sdk")
        self.assertIsNone(sf.find_image(sdk))
        self.image(sdk, 32); self.image(sdk, 36, abi="x86_64"); self.image(sdk, 34, installed=False)   # too old, wrong CPU, not installed
        self.assertIsNone(sf.find_image(sdk))
        self.image(sdk, 34)
        self.assertEqual(sf.find_image(sdk), "system-images;android-34;google_apis;arm64-v8a")
        self.image(sdk, 35, tag="google_apis_playstore")
        self.assertEqual(sf.find_image(sdk), "system-images;android-35;google_apis_playstore;arm64-v8a")
        self.image(sdk, 35)                                                                             # same API: google_apis first
        self.assertEqual(sf.find_image(sdk), "system-images;android-35;google_apis;arm64-v8a")
        self.image(sdk, "36.1")
        self.assertEqual(sf.find_image(sdk), "system-images;android-36.1;google_apis;arm64-v8a")

    def test_cmdline_tool_prefers_latest_then_other_versions_then_path_then_homebrew(self):
        sdk = self.sdk(self.root / "sdk")
        self.assertIsNone(sf.cmdline_tool("sdkmanager", sdk))
        brew = touch(self.brew / "bin/sdkmanager"); self.assertEqual(sf.cmdline_tool("sdkmanager", sdk), brew)
        pathdir = self.root / "pathbin"; on_path = touch(pathdir / "sdkmanager")
        with mock.patch.dict(os.environ, {"PATH": str(pathdir)}): self.assertEqual(sf.cmdline_tool("sdkmanager", sdk), on_path)
        versioned = touch(sdk / "cmdline-tools/12.0/bin/sdkmanager"); self.assertEqual(sf.cmdline_tool("sdkmanager", sdk), versioned)
        latest = touch(sdk / "cmdline-tools/latest/bin/sdkmanager"); self.assertEqual(sf.cmdline_tool("sdkmanager", sdk), latest)

    def commands(self, sdk, packages, java=None):
        with mock.patch.object(sf, "java_env", return_value={"JAVA_HOME": java} if java else {}):
            return sf.sdkmanager_commands(packages, sdk)

    def test_commands_use_the_sdkmanager_inside_the_sdk(self):
        sdk = self.sdk(self.root / "sdk"); tool = touch(sdk / "cmdline-tools/latest/bin/sdkmanager")
        self.assertEqual(self.commands(sdk, ["platform-tools", "emulator"]), [f"{tool} platform-tools emulator"])
        self.assertEqual(self.commands(sdk, ["system-images;android-36;google_apis;arm64-v8a"]), [f"{tool} 'system-images;android-36;google_apis;arm64-v8a'"])

    def test_commands_install_homebrews_command_line_tools_first_when_there_is_no_sdkmanager(self):
        sdk = self.home / "Library/Android/sdk"        # does not exist
        cmds = self.commands(sdk, ["platform-tools", "emulator"])
        tool = self.brew / "share/android-commandlinetools/cmdline-tools/latest/bin/sdkmanager"
        self.assertEqual(cmds, ["brew install --cask android-commandlinetools", f"yes | {tool} --licenses", f"{tool} platform-tools emulator"])

    def test_commands_name_the_sdk_root_when_the_sdkmanager_lives_elsewhere_and_set_java_home_for_a_keg_only_java(self):
        sdk = self.sdk(self.root / "sdk"); tool = touch(self.brew / "bin/sdkmanager")
        self.assertEqual(self.commands(sdk, ["emulator"], java="/opt/jdk home"), [f"JAVA_HOME='/opt/jdk home' {tool} --sdk_root={sdk} emulator"])

    def test_adb_comes_from_the_sdk_when_it_is_not_on_the_path(self):
        sdk = self.sdk(self.root / "sdk")
        with mock.patch.object(sf, "SDK", sdk):
            self.assertEqual(sf.adb_cmd(), "adb"); self.assertEqual(sf.Emu(5554).serial, "emulator-5554")
            adb = touch(sdk / "platform-tools/adb"); self.assertEqual(sf.adb_cmd(), str(adb))
            with mock.patch.object(sf, "java_env", return_value={}):
                env = sf.android_env()
            self.assertEqual(env["ANDROID_HOME"], str(sdk)); self.assertTrue(env["PATH"].startswith(f"{sdk}/platform-tools:"))

    def create_emulator(self, cfg, sdk):
        """Run android_pool as far as the avdmanager call; return (the -k image, the Fail text)."""
        seen = []
        def fake_sh(cmd, **kw): seen.append(cmd); return subprocess.CompletedProcess(cmd, 1, "", "image missing")
        with mock.patch.object(sf, "SDK", sdk), mock.patch.object(sf, "sh", fake_sh), mock.patch.object(sf, "java_env", return_value={}):
            with self.assertRaises(sf.Fail) as e: sf.android_pool(1, cfg, [])
        return seen[0][seen[0].index("-k") + 1], str(e.exception)

    def test_the_emulator_is_created_from_the_config_image_else_an_installed_one_else_the_default_with_the_install_command(self):
        sdk = self.sdk(self.root / "sdk"); touch(sdk / "cmdline-tools/latest/bin/avdmanager"); sdkmanager = touch(sdk / "cmdline-tools/latest/bin/sdkmanager")
        want = "system-images;android-34;google_apis_playstore;arm64-v8a"
        self.assertEqual(self.create_emulator({"system_image": want}, sdk)[0], want)
        self.image(sdk, 35)
        self.assertEqual(self.create_emulator({"system_image": want}, sdk)[0], want)                  # the config wins even over a newer installed one
        self.assertEqual(self.create_emulator({}, sdk)[0], "system-images;android-35;google_apis;arm64-v8a")
        import shutil; shutil.rmtree(sdk / "system-images")
        image, msg = self.create_emulator({}, sdk)
        self.assertEqual(image, sf.DEFAULT_IMAGE)
        self.assertIn("couldn't create the emulator", msg)
        self.assertIn(f"Install the image with: {sdkmanager} '{sf.DEFAULT_IMAGE}'", msg)

    def test_a_missing_avdmanager_says_how_to_install_it_instead_of_crashing(self):
        sdk = self.sdk(self.root / "sdk"); touch(sdk / "cmdline-tools/latest/bin/sdkmanager")
        with mock.patch.object(sf, "SDK", sdk), mock.patch.object(sf, "java_env", return_value={}), self.assertRaises(sf.Fail) as e:
            sf.android_pool(1, {}, [])
        self.assertIn("avdmanager not found under", str(e.exception)); self.assertIn("cmdline-tools;latest", str(e.exception))


class DoctorAndroid(Tree):
    def doctor(self, sdk):
        out = io.StringIO()
        with mock.patch.object(sf, "SDK", sdk), mock.patch.object(sf, "java_env", return_value={}), mock.patch.object(sf, "find_java", return_value=(True, None)), \
             mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "latest_release", return_value=None), \
             mock.patch.object(sf, "sh", return_value=subprocess.CompletedProcess([], 0, "Ready\n", "")), contextlib.redirect_stdout(out):
            code = sf.cmd_doctor()
        return code, out.getvalue()

    def full_sdk(self, api=36):
        sdk = self.root / "sdk"
        for f in ("platform-tools/adb", "emulator/emulator", "cmdline-tools/latest/bin/avdmanager", "cmdline-tools/latest/bin/sdkmanager", "build-tools/36.0.0/aapt2"):
            touch(sdk / f)
        d = sdk / f"system-images/android-{api}/google_apis_playstore/arm64-v8a"; d.mkdir(parents=True); (d / "package.xml").write_text("<x/>")
        return sdk

    def test_a_complete_sdk_with_any_api_33_plus_image_is_ready_and_prints_no_install_commands(self):
        sdk = self.full_sdk(api=35)
        code, out = self.doctor(sdk)
        self.assertNotRegex(out, r"MISSING .*\(Android\)"); self.assertIn(f"Android SDK: {sdk}", out)
        self.assertRegex(out, r"ok   system image android-35 google_apis_playstore")
        self.assertNotIn("to install what is missing", out); self.assertNotIn("MISSING emulator", out)

    def test_missing_pieces_come_with_one_exact_sdkmanager_command(self):
        sdk = self.full_sdk(); import shutil
        shutil.rmtree(sdk / "emulator"); shutil.rmtree(sdk / "platform-tools"); shutil.rmtree(sdk / "system-images"); shutil.rmtree(sdk / "build-tools")
        code, out = self.doctor(sdk)
        for name in ("MISSING adb", "MISSING emulator", "MISSING aapt2", "MISSING system image (API 33+)"): self.assertIn(name, out)
        tool = sdk / "cmdline-tools/latest/bin/sdkmanager"
        self.assertIn(f"  {tool} platform-tools emulator 'build-tools;36.0.0' 'system-images;android-36;google_apis;arm64-v8a'\n", out)
        self.assertIn("large download", out)

    def test_an_existing_shotfleet_emulator_needs_no_image(self):
        sdk = self.full_sdk(); import shutil; shutil.rmtree(sdk / "system-images")
        (self.home / ".android/avd/shotfleet_android.avd").mkdir(parents=True)
        code, out = self.doctor(sdk)
        self.assertNotRegex(out, r"MISSING .*\(Android\)"); self.assertNotIn("to install what is missing", out)

    def test_with_no_android_sdk_at_all_doctor_prints_the_homebrew_route_and_every_package(self):
        sdk = self.home / "Library/Android/sdk"
        code, out = self.doctor(sdk)
        tool = self.brew / "share/android-commandlinetools/cmdline-tools/latest/bin/sdkmanager"
        self.assertIn("  brew install --cask android-commandlinetools\n", out)
        self.assertIn(f"  yes | {tool} --licenses\n", out)
        self.assertIn(f"  {tool} platform-tools emulator 'build-tools;36.0.0' 'system-images;android-36;google_apis;arm64-v8a'\n", out)
        self.assertIn("nothing found there; set ANDROID_HOME", out)

    def test_only_avdmanager_missing_with_an_sdkmanager_asks_for_the_command_line_tools_package(self):
        sdk = self.full_sdk(); (sdk / "cmdline-tools/latest/bin/avdmanager").unlink()
        code, out = self.doctor(sdk)
        self.assertIn("MISSING avdmanager", out)
        self.assertIn(f"  {sdk / 'cmdline-tools/latest/bin/sdkmanager'} 'cmdline-tools;latest'\n", out)


if __name__ == "__main__":
    unittest.main()
