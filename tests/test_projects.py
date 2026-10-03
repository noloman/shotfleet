"""`shotfleet init` in the source folder of a Flutter, React Native, Expo, MAUI or Capacitor app: it recognises the
project, finds the build where that framework puts it, and writes the `strings` line itself. Synthetic folders only:
these tests start no toolchain and need no Mac."""
import contextlib, io, json, os, plistlib, sys, tempfile, tomllib, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf


def tree(files):
    d = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        f = d / rel; f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(text if isinstance(text, bytes) else text.encode())
    return d

def sim_app(root, rel, bundle="com.example.app", flutter_debug=False):
    """A simulator .app that passes the same checks as a real one."""
    app = root / rel; app.mkdir(parents=True)
    if flutter_debug: (app / "flutter_assets").mkdir(); (app / "flutter_assets/kernel_blob.bin").write_bytes(b"\0")
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "App", "CFBundleIdentifier": bundle,
                                                      "DTPlatformName": "iphonesimulator"}))
    (app / "App").write_bytes(b"\0")
    return app

ARB = {f"lib/l10n/app_{lp}.arb": json.dumps({"@@locale": lp, "next": lp}) for lp in ("en", "de", "ja")}
FLUTTER = {"pubspec.yaml": "name: demo\ndependencies:\n  flutter:\n    sdk: flutter\nflutter:\n  generate: true\n", **ARB}
RN_JSON = {f"src/locales/{lp}/translation.json": json.dumps({"next": lp}) for lp in ("en", "de")}


class Detect(unittest.TestCase):
    def test_flutter_with_the_default_arb_folder(self):
        p = sf.detect_project(tree(FLUTTER))
        self.assertEqual((p.name, p.strings), ("Flutter", "lib/l10n/*.arb"))
        self.assertIn("flutter build ios --simulator", p.build_ios)

    def test_flutter_arb_dir_from_l10n_yaml(self):
        d = tree({**FLUTTER, "l10n.yaml": "arb-dir: assets/translations # where they live\ntemplate-arb-file: app_en.arb\n",
                  **{f"assets/translations/app_{lp}.arb": json.dumps({"@@locale": lp, "a": "b"}) for lp in ("en", "fr")}})
        self.assertEqual(sf.detect_project(d).strings, "assets/translations/*.arb")

    def test_flutter_without_l10n_yaml_takes_the_folder_with_the_most_arb_files(self):
        d = tree({"pubspec.yaml": "flutter:\n", **{f"res/app_{lp}.arb": "{}" for lp in ("en", "de", "fr")},
                  "other/app_en.arb": "{}", "build/x/app_en.arb": "{}"})
        self.assertEqual(sf.detect_project(d).strings, "res/*.arb")

    def test_flutter_easy_localization_json(self):
        d = tree({"pubspec.yaml": "flutter:\n", "assets/translations/en.json": "{}", "assets/translations/de.json": "{}"})
        self.assertEqual(sf.detect_project(d).strings, "assets/translations/*.json")

    def test_react_native_wants_release_builds_and_finds_i18next_files(self):
        p = sf.detect_project(tree({"package.json": json.dumps({"dependencies": {"react-native": "0.76"}}), **RN_JSON}))
        self.assertEqual((p.name, p.strings, p.configs), ("React Native", "src/locales/*/translation.json", ("Release",)))
        self.assertIn("run-ios --mode Release", p.build_ios)
        self.assertIn("assembleRelease", p.build_android)

    def test_expo_is_told_apart_and_uses_expos_commands(self):
        p = sf.detect_project(tree({"package.json": json.dumps({"dependencies": {"expo": "~52", "react-native": "0.76"}}), **RN_JSON}))
        self.assertEqual(p.name, "Expo")
        self.assertIn("npx expo run:ios --configuration Release", p.build_ios)

    def test_lingui_po_files_are_preferred_when_present(self):
        d = tree({"package.json": json.dumps({"dependencies": {"react-native": "1"}}),
                  "src/locale/locales/en/messages.po": "", "src/locale/locales/de/messages.po": "", **RN_JSON})
        self.assertEqual(sf.detect_project(d).strings, "src/locale/locales/*/messages.po")

    def test_maui_resx_and_capacitor_and_kotlin_multiplatform(self):
        maui = tree({"App.csproj": "<Project><PropertyGroup><UseMaui>true</UseMaui></PropertyGroup></Project>",
                     "Resources/Strings/AppResources.resx": "<root/>", "Resources/Strings/AppResources.de.resx": "<root/>"})
        p = sf.detect_project(maui)
        self.assertEqual((p.name, p.strings), (".NET MAUI", "Resources/Strings/*.resx"))
        self.assertIn("EmbedAssembliesIntoApk=true", p.build_android)
        cap = tree({"package.json": json.dumps({"dependencies": {"@capacitor/core": "6"}}), "src/assets/i18n/en.json": "{}",
                    "src/assets/i18n/de.json": "{}"})
        self.assertEqual((sf.detect_project(cap).name, sf.detect_project(cap).strings), ("Capacitor", "src/assets/i18n/*.json"))
        kmp = tree({"settings.gradle.kts": "include(\":composeApp\")", "composeApp/build.gradle.kts": 'plugins { kotlin("multiplatform") }'})
        self.assertEqual(sf.detect_project(kmp).name, "Kotlin Multiplatform")

    def test_native_and_unrelated_folders_are_not_projects(self):
        self.assertIsNone(sf.detect_project(tree({"MyApp.xcodeproj/project.pbxproj": "", "app/build.gradle": "apply plugin: 'com.android.application'"})))
        self.assertIsNone(sf.detect_project(tree({"package.json": json.dumps({"dependencies": {"react": "18"}})})))
        self.assertIsNone(sf.detect_project(tree({})))

    def test_a_broken_package_json_is_not_a_crash(self):
        self.assertIsNone(sf.detect_project(tree({"package.json": "{not json"})))


class FindTheBuild(unittest.TestCase):
    def find(self, d, project):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            return sf.find_builds(d, derived=Path(d) / "no-derived-data", project=project), out.getvalue()

    def test_flutter_ios_build_in_the_flutter_build_folder(self):
        d = tree(FLUTTER); app = sim_app(d, "build/ios/iphonesimulator/Runner.app")
        builds, out = self.find(d, sf.detect_project(d))
        self.assertEqual(builds, [str(app.resolve())])
        self.assertIn("Runner.app", out)

    def test_flutter_apk_in_the_flutter_apk_folder(self):
        d = tree({**FLUTTER, "build/app/outputs/flutter-apk/app-debug.apk": b"PK"})
        builds, _ = self.find(d, sf.detect_project(d))
        self.assertEqual([Path(b).name for b in builds], ["app-debug.apk"])

    def test_react_native_prefers_the_release_apk_two_folders_down(self):
        d = tree({"package.json": json.dumps({"dependencies": {"react-native": "1"}}), **RN_JSON,
                  "android/app/build/outputs/apk/debug/app-debug.apk": b"PK", "android/app/build/outputs/apk/release/app-release.apk": b"PK"})
        builds, _ = self.find(d, sf.detect_project(d))
        self.assertEqual([Path(b).name for b in builds], ["app-release.apk"])

    def test_react_native_with_only_a_debug_apk_still_finds_it(self):
        d = tree({"package.json": json.dumps({"dependencies": {"react-native": "1"}}), "android/app/build/outputs/apk/debug/app-debug.apk": b"PK"})
        builds, _ = self.find(d, sf.detect_project(d))
        self.assertEqual([Path(b).name for b in builds], ["app-debug.apk"])

    def test_nothing_built_names_the_frameworks_own_commands(self):
        d = tree(FLUTTER)
        with self.assertRaises(sf.Fail) as e: self.find(d, sf.detect_project(d))
        self.assertIn("flutter build ios --simulator --debug", str(e.exception))
        self.assertIn("flutter build apk --debug", str(e.exception))
        self.assertNotIn("gradlew", str(e.exception))

    def test_a_device_build_in_the_flutter_folder_is_ignored(self):
        d = tree(FLUTTER); app = sim_app(d, "build/ios/iphoneos/Runner.app")
        plist = plistlib.loads((app / "Info.plist").read_bytes()); plist["DTPlatformName"] = "iphoneos"
        (app / "Info.plist").write_bytes(plistlib.dumps(plist))
        with self.assertRaises(sf.Fail): self.find(d, sf.detect_project(d))

    def test_capacitor_project_inside_ios_app_is_found_by_the_xcode_scan(self):
        d = tree({"package.json": json.dumps({"dependencies": {"@capacitor/core": "6"}}), "ios/App/App.xcodeproj/project.pbxproj": ""})
        self.assertEqual([p.name for p in sf.xcode_projects(d)], ["App.xcodeproj"])


class InitInAFlutterFolder(unittest.TestCase):
    def run_init(self, d, dest="."):
        out, old = io.StringIO(), os.getcwd()
        os.chdir(d)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out): sf.cmd_init([], dest)
        finally: os.chdir(old)
        return out.getvalue()

    def test_init_with_no_arguments_writes_the_strings_line_and_counts_the_languages(self):
        d = tree(FLUTTER); sim_app(d, "build/ios/iphonesimulator/Runner.app", "com.example.demo", flutter_debug=True)
        out = self.run_init(d)
        cfg = tomllib.loads((d / "shotfleet.toml").read_text())
        self.assertEqual(cfg["ios"]["strings"], "lib/l10n/*.arb")
        self.assertTrue(cfg["ios"]["app"].endswith("Runner.app"))
        self.assertIn("Flutter project: translations from lib/l10n/*.arb (3 languages)", out)
        self.assertIn("com.example.demo: 3 languages", out)
        self.assertIn("DEBUG banner", out)
        self.assertNotIn("hint: Flutter keeps its translations", out)  # the line is already in the config

    def test_the_config_can_live_in_another_folder(self):
        d = tree(FLUTTER); sim_app(d, "build/ios/iphonesimulator/Runner.app")
        self.run_init(d, "shots")
        cfg = tomllib.loads((d / "shots/shotfleet.toml").read_text())
        self.assertEqual(cfg["ios"]["strings"], "../lib/l10n/*.arb")

    def test_a_flutter_folder_without_translation_files_says_what_to_add(self):
        d = tree({"pubspec.yaml": "flutter:\n"}); sim_app(d, "build/ios/iphonesimulator/Runner.app")
        out = self.run_init(d)
        self.assertIn("Flutter project: no translation files found", out)
        self.assertNotIn("strings", (d / "shotfleet.toml").read_text())

    def test_the_generated_strings_path_actually_loads(self):
        d = tree(FLUTTER)
        old = os.getcwd(); os.chdir(d)
        try: strings = sf.load_strings_files(["lib/l10n/*.arb"])
        finally: os.chdir(old)
        self.assertEqual(sorted(strings), ["de", "en", "ja"])


if __name__ == "__main__":
    unittest.main()


class UnpackBuilds(unittest.TestCase):
    """EAS hands iOS simulator builds over as .tar.gz; init unpacks them and writes the .app into the config."""
    def make_app_tar(self, d, name="MyApp-sim.tar.gz", root="MyApp.app"):
        import tarfile
        src = tree({})
        sim_app(src, root, "com.example.eas")
        path = Path(d) / name
        with tarfile.open(path, "w:gz") as t: t.add(src / root, arcname=root)
        return path

    def test_tar_gz_zip_and_a_nested_folder(self):
        import zipfile
        d = Path(tempfile.mkdtemp())
        app = sf.unpack_build(self.make_app_tar(d), d / "out")
        self.assertEqual((app.name, app.parent.name), ("MyApp.app", "MyApp-sim"))
        z = d / "b.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("build/MyApp.app/Info.plist", plistlib.dumps({"CFBundleExecutable": "A"}))
        self.assertEqual(sf.unpack_build(z, d / "out2").name, "MyApp.app")

    def test_unpacking_twice_replaces_the_old_copy(self):
        d = Path(tempfile.mkdtemp()); arc = self.make_app_tar(d)
        first = sf.unpack_build(arc, d / "out"); (first / "stale").write_text("x")
        again = sf.unpack_build(arc, d / "out")
        self.assertFalse((again / "stale").exists())

    def test_an_archive_with_nothing_installable_or_with_escaping_paths_is_refused(self):
        import tarfile, io as _io
        d = Path(tempfile.mkdtemp())
        empty = d / "e.tar.gz"
        with tarfile.open(empty, "w:gz") as t:
            info = tarfile.TarInfo("readme.txt"); info.size = 2; t.addfile(info, _io.BytesIO(b"hi"))
        with self.assertRaisesRegex(sf.Fail, "holds no .app or .apk"): sf.unpack_build(empty, d / "o")
        evil = d / "evil.tgz"
        with tarfile.open(evil, "w:gz") as t:
            info = tarfile.TarInfo("../outside.txt"); info.size = 2; t.addfile(info, _io.BytesIO(b"hi"))
        with self.assertRaisesRegex(sf.Fail, "outside its folder"): sf.unpack_build(evil, d / "o2")
        self.assertFalse((d / "outside.txt").exists())
        notarchive = d / "bad.tar.gz"; notarchive.write_bytes(b"not a tar")
        with self.assertRaisesRegex(sf.Fail, "can't unpack"): sf.unpack_build(notarchive, d / "o3")

    def test_init_takes_the_archive_directly(self):
        d = Path(tempfile.mkdtemp()); arc = self.make_app_tar(d)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out): sf.cmd_init([str(arc)], d / "cfg")
        cfg = tomllib.loads((d / "cfg/shotfleet.toml").read_text())
        self.assertTrue(cfg["ios"]["app"].endswith("MyApp.app"), cfg)
        self.assertTrue((d / "cfg" / cfg["ios"]["app"]).is_dir())


class BuildHookSuggestion(unittest.TestCase):
    def init_in(self, d, dest="."):
        old = os.getcwd(); os.chdir(d)
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()): sf.cmd_init([], dest)
        finally: os.chdir(old)
        return (Path(d) / dest / "shotfleet.toml").read_text()

    def test_a_flutter_folder_gets_a_commented_before_run_hook_that_is_valid_toml_and_off(self):
        d = tree(FLUTTER); sim_app(d, "build/ios/iphonesimulator/Runner.app")
        text = self.init_in(d)
        self.assertIn('# before_run = "if [ \\"$SHOTFLEET_PLATFORM\\" = ios ]; then flutter build ios --simulator --debug; else flutter build apk --debug; fi"', text)
        self.assertNotIn("hooks", tomllib.loads(text))  # a suggestion only: nothing runs unless the user uncomments it

    def test_uncommented_it_is_accepted_by_the_config_reader(self):
        d = tree(FLUTTER); sim_app(d, "build/ios/iphonesimulator/Runner.app")
        text = self.init_in(d).replace("# [hooks]", "[hooks]").replace("# before_run", "before_run")
        doc = tomllib.loads(text)
        self.assertIn("before_run", doc["hooks"])
        sf.check_tables(doc, "shotfleet.toml")  # the reader accepts it (raises Fail otherwise)

    def test_no_hook_suggestion_for_a_native_app_or_when_the_config_is_elsewhere(self):
        d = tree({"MyApp.xcodeproj/project.pbxproj": ""}); sim_app(d, "build/x/Debug-iphonesimulator/MyApp.app")
        self.assertNotIn("before_run", self.init_in_with_app(d, "build/x/Debug-iphonesimulator/MyApp.app"))
        f = tree(FLUTTER); sim_app(f, "build/ios/iphonesimulator/Runner.app")
        self.assertNotIn("before_run", self.init_in(f, "cfg"))

    def init_in_with_app(self, d, app):
        old = os.getcwd(); os.chdir(d)
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()): sf.cmd_init([app], ".")
        finally: os.chdir(old)
        return (Path(d) / "shotfleet.toml").read_text()


class KotlinMultiplatformLayouts(unittest.TestCase):
    """kotlinconf-app (JetBrains) keeps the plugin as a version-catalog alias and its modules two folders down."""
    def test_catalog_alias_and_nested_modules(self):
        d = tree({"settings.gradle.kts": 'include(":app:shared")', "build.gradle.kts": "plugins { alias(libs.plugins.kotlinMultiplatform) apply false }",
                  "app/shared/build.gradle.kts": "plugins { alias(libs.plugins.kotlinMultiplatform) }"})
        self.assertEqual(sf.detect_project(d).name, "Kotlin Multiplatform")

    def test_only_the_version_catalog_names_it(self):
        d = tree({"settings.gradle": "", "gradle/libs.versions.toml": '[plugins]\nkotlinMultiplatform = { id = "org.jetbrains.kotlin.multiplatform" }'})
        self.assertEqual(sf.detect_project(d).name, "Kotlin Multiplatform")

    def test_a_plain_android_gradle_project_is_not_multiplatform(self):
        d = tree({"settings.gradle.kts": 'include(":app")', "app/build.gradle.kts": 'plugins { id("com.android.application") }'})
        self.assertIsNone(sf.detect_project(d))


class RealAppLessons(unittest.TestCase):
    """What running wger (Flutter) and kotlinconf-app (Compose) on a Mac taught `init` to say (research/frameworks.md section 15)."""
    def test_flutter_says_how_to_tap_a_row_and_to_wait_for_text(self):
        notes = " ".join(sf.detect_project(tree(FLUTTER)).notes)
        self.assertIn('"Title.*"', notes); self.assertIn("extendedWaitUntil", notes)

    def test_compose_says_to_wait_and_the_xcodebuild_it_prints_names_arm64(self):
        d = tree({"settings.gradle.kts": 'include(":app")', "app/build.gradle.kts": 'plugins { kotlin("multiplatform") }',
                  "iosApp/App.xcodeproj/project.pbxproj": ""})
        project = sf.detect_project(d)
        self.assertIn("extendedWaitUntil", " ".join(project.notes))
        with self.assertRaises(sf.Fail) as e, contextlib.redirect_stdout(io.StringIO()):
            sf.find_builds(d, derived=d / "no-derived-data", project=project)
        self.assertIn("ARCHS=arm64", str(e.exception))  # Xcode 27 asks for x86_64 as well, which the Gradle build lacks

    def test_the_starter_flow_waits_for_text_before_the_first_screenshot(self):
        flow = sf.FLOW_TEMPLATE
        self.assertLess(flow.index("extendedWaitUntil"), flow.index("takeScreenshot: 01_home"))


class BareReactNativeWithTheExpoPackage(unittest.TestCase):
    """Rocket.Chat.ReactNative: a bare React Native app (ios/ and android/ committed) that depends on `expo` for native modules."""
    ROCKET = {"package.json": json.dumps({"dependencies": {"react-native": "0.86.3", "expo": "^57.0.0"}}), "app.json": json.dumps({"name": "RocketChatRN"}),
              "ios/RocketChat.xcodeproj/project.pbxproj": "", "android/build.gradle": "",
              **{f"app/i18n/locales/{lp}.json": json.dumps({"Add": lp}) for lp in ("en", "de", "ar")}}

    def test_it_is_react_native_not_expo_and_its_translations_are_found(self):
        p = sf.detect_project(tree(self.ROCKET))
        self.assertEqual((p.name, p.strings), ("React Native", "app/i18n/locales/*.json"))
        self.assertIn("react-native run-ios", p.build_ios); self.assertNotIn("expo", p.build_android)

    def test_an_expo_app_is_still_expo(self):
        for extra in ({"app.config.ts": ""}, {"app.json": json.dumps({"expo": {"name": "x"}})}):
            files = {"package.json": json.dumps({"dependencies": {"react-native": "0.81", "expo": "~54"}}), **extra}
            self.assertEqual(sf.detect_project(tree(files)).name, "Expo", extra)
        files = {"package.json": json.dumps({"main": "expo-router/entry", "dependencies": {"react-native": "0.81", "expo": "~54"}})}
        self.assertEqual(sf.detect_project(tree(files)).name, "Expo")
