"""tools/fixture-e2e.sh without devices: its shell syntax, its refusal, its assertion helper on a synthetic output tree
(good, then one planted defect at a time), and the whole script against fake `xcrun`, `shotfleet`, `df` and `memory_pressure`.

Never touches a simulator: the fakes stand in for everything that would.  Run: python3 -m unittest tests.test_fixture_e2e
"""
import contextlib, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile, textwrap, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools/fixture-e2e.sh"
LOCALES = ["de", "ja", "ar", "tr"]
DEVICES = ["iphone-17-pro-max", "ipad-pro-13-inch-m5-12gb"]
SHOTS = ["01_welcome", "02_settings"]
LISTING = {"de": "de-DE", "ja": "ja", "ar": "ar-SA", "tr": "tr"}
PLAY_LISTING = {"de": "de-DE", "ja": "ja-JP", "ar": "ar", "tr": "tr-TR"}
SDK = Path(os.environ.get("ANDROID_HOME") or Path.home() / "Library/Android/sdk")
CAN_BUILD_APK = bool(shutil.which("javac") and shutil.which("keytool") and list(SDK.glob("build-tools/*/apksigner")) and list(SDK.glob("platforms/android-[0-9]*/android.jar")))
TEXTS = {"de": (["Willkommen", "Weiter"], ["Einstellungen", "Fertig"]), "ja": (["ようこそ", "次へ"], ["設定", "完了"]),
         "ar": (["مرحبا", "التالي"], ["الإعدادات", "تم"]), "tr": (["Hoş geldin", "İleri"], ["Ayarlar", "Bitti"]),
         "en": (["Welcome", "Next"], ["Settings", "Done"])}


def png(tag, w=1320, h=2868):
    """A PNG header with the given size and padding that differs per tag (so images differ unless copied)."""
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, 2]) + b"\0" * 8 + b"IDAT" + tag.encode() * 2000


def make_out(out, locales=LOCALES, devices=DEVICES, config="/x/shotfleet.toml", android=False):
    """A finished, clean multi-device run: out/<device>/raw/<locale>/<shot>.png (+ the app's text capture), check.json, run.json.
    android: the one phone set of an Android run."""
    devices = ["phone"] if android else devices
    for dev in devices:
        d = Path(out) / dev
        for lp in locales:
            (d / "raw" / lp).mkdir(parents=True, exist_ok=True)
            for i, shot in enumerate(SHOTS):
                (d / "raw" / lp / f"{shot}.png").write_bytes(png(f"{dev}{lp}{shot}"))
                (d / "raw" / lp / f"{shot}.texts.json").write_text(json.dumps(TEXTS[lp][i], ensure_ascii=False))
        (d / "check.json").write_text(json.dumps({"screenshots": [], "problems": [], "notes": []}))
        (d / "run.json").write_text(json.dumps({"config": config, "app": "/x/FleetFixture.app", **({"platform": "android"} if android else {}),
                                                "locales": {lp: {"ok": True, "screenshots": 2} for lp in locales}}))


def make_fastlane(out, fastlane, android=False):
    """What `export --fastlane` writes: screenshots/<listing>/<device>_<shot>.png (iOS), metadata/android/<listing>/images/phoneScreenshots/ (Android)."""
    for d in sorted(Path(out).iterdir()):
        for lp_dir in sorted((d / "raw").iterdir()):
            dst = Path(fastlane) / "metadata/android" / PLAY_LISTING[lp_dir.name] / "images/phoneScreenshots" if android else Path(fastlane) / "screenshots" / LISTING[lp_dir.name]
            dst.mkdir(parents=True, exist_ok=True)
            for p in lp_dir.glob("*.png"): shutil.copy2(p, dst / f"{d.name}_{p.name}")


GOOD_HOOKS = "before_run locales=de,ja,ar,tr\nafter_run exit=0 problems=0\nbefore_export\nafter_export exit=0\n"


def load_helper(into):
    """The assertion helper, cut out of the script the way the script itself does it."""
    text = SCRIPT.read_text()
    body = re.search(r"^: <<'__PY__'\n(.*?)^__PY__$", text, re.S | re.M).group(1)
    path = Path(into) / "e2e_assert.py"; path.write_text(body)
    spec = importlib.util.spec_from_file_location("e2e_assert", path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def no_ocr(path): raise AssertionError(f"OCR called for {path}: the text capture should have been used")


class Script(unittest.TestCase):
    def test_shell_syntax_is_valid(self):
        r = subprocess.run(["sh", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("set -eu", SCRIPT.read_text())

    def test_refuses_without_the_opt_in_and_says_why(self):
        env = {k: v for k, v in os.environ.items() if k != "SHOTFLEET_E2E"}
        for value in (None, "0", "yes"):
            if value is not None: env["SHOTFLEET_E2E"] = value
            r = subprocess.run(["sh", str(SCRIPT)], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("SHOTFLEET_E2E=1", r.stderr); self.assertIn("simulators", r.stderr)

    def test_help_and_bad_options_need_no_opt_in(self):
        r = subprocess.run(["sh", str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0); self.assertIn("SHOTFLEET_E2E=1", r.stdout)
        for args in (["--nope"], ["--platform-only", "windows"], ["--platform-only"]):
            r = subprocess.run(["sh", str(SCRIPT), *args], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, args)

    def test_script_never_boots_creates_or_builds_with_xcode_itself(self):
        text = SCRIPT.read_text()
        for forbidden in ("simctl boot", "simctl create", "simctl erase", "simctl delete", "xcodebuild", "killall", "pkill"):
            self.assertNotIn(forbidden, text)
        shutdowns = re.findall(r"simctl shutdown.*", text)
        self.assertEqual(len(shutdowns), 1)  # only the safety net, and only for udids the helper's pool-name filter returned


class Helper(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory(); self.addCleanup(self._d.cleanup)
        self.d = Path(self._d.name); self.h = load_helper(self.d)
        self.out, self.fl, self.hooks = self.d / "out", self.d / "fastlane", self.d / "hooks.log"
        make_out(self.out); make_fastlane(self.out, self.fl); self.hooks.write_text(GOOD_HOOKS)

    def run_tree(self, locales=LOCALES):
        return self.h.tree(self.out, self.fl, self.hooks, locales, no_ocr)

    def failed(self, locales=LOCALES):
        return [what for what, ok, _ in self.run_tree(locales) if not ok]

    def test_good_tree_passes_every_assertion(self):
        res = self.run_tree()
        self.assertGreater(len(res), 20)
        self.assertEqual([r for r in res if not r[1]], [])
        with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(self.h.report(res), 0)

    def test_missing_screenshot_fails(self):
        (self.out / DEVICES[1] / "raw/tr/02_settings.png").unlink()
        f = self.failed()
        self.assertTrue(any("ipad" in w and "screenshots in every language" in w for w in f), f)
        self.assertTrue(any("every raw PNG" in w for w in f), f)

    def test_empty_or_truncated_screenshot_fails(self):
        (self.out / DEVICES[0] / "raw/ar/01_welcome.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        self.assertTrue(any("every raw PNG" in w for w in self.failed()))

    def test_screenshot_copied_over_another_language_fails(self):
        for suffix in (".png", ".texts.json"):
            src, dst = (self.out / DEVICES[0] / f"raw/{lp}/01_welcome{suffix}" for lp in ("de", "ja"))
            dst.write_bytes(src.read_bytes())
        self.assertTrue(any("identical image" in w for w in self.failed()))

    def test_wrong_language_text_fails(self):
        (self.out / DEVICES[1] / "raw/de/01_welcome.texts.json").write_text(json.dumps(["Welcome", "Next"]))
        f = self.failed()
        self.assertTrue(any("ipad" in w and "'Weiter'" in w for w in f), f)

    def test_ocr_is_the_fallback_when_the_app_captured_no_text(self):
        for p in self.out.rglob("*.texts.json"): p.unlink()
        calls = []
        res = self.h.tree(self.out, self.fl, self.hooks, LOCALES, lambda p: calls.append(p) or "Willkommen Weiter Fertig")
        self.assertTrue(all(ok for _, ok, _ in res), [r for r in res if not r[1]])
        self.assertEqual(len(calls), 4)  # 2 screens x 2 devices, German only
        res = self.h.tree(self.out, self.fl, self.hooks, LOCALES, lambda p: "Welcome Next Done")
        self.assertTrue(any(not ok and "'Weiter'" in what for what, ok, _ in res))

    def test_missing_hook_log_or_event_fails(self):
        self.hooks.unlink()
        self.assertEqual(sum("hook " in w for w in self.failed()), 4)
        self.hooks.write_text("before_run locales=de\nafter_run exit=0 problems=0\nbefore_export\n")
        self.assertEqual([w for w in self.failed() if "hook" in w], ["hook after_export fired (hooks.log)"])
        self.hooks.write_text(GOOD_HOOKS.replace("problems=0", "problems=3"))
        self.assertEqual([w for w in self.failed() if "hook" in w], ["hook after_run fired (hooks.log)"])

    def test_nonzero_problems_in_the_report_fail(self):
        (self.out / DEVICES[0] / "check.json").write_text(json.dumps({"problems": ["ja/01_welcome.png: shows de"]}))
        f = self.failed()
        self.assertEqual([w for w in f if "problems" in w], [f"{DEVICES[0]}: the report has 0 problems"])
        (self.out / DEVICES[0] / "check.json").unlink()
        self.assertTrue(any("0 problems" in w for w in self.failed()))

    def test_language_that_failed_to_capture_fails(self):
        run = self.out / DEVICES[0] / "run.json"; doc = json.loads(run.read_text()); doc["locales"]["ja"]["ok"] = False
        run.write_text(json.dumps(doc))
        self.assertTrue(any("captured ok" in w for w in self.failed()))

    def test_export_folder_missing_a_language_or_a_device_set_fails(self):
        shutil.rmtree(self.fl / "screenshots/ar-SA")
        self.assertEqual([w for w in self.failed() if w.startswith("export")], ["export: ar-SA has 4 screenshots (one set per device)"])
        (self.fl / "screenshots/de-DE" / f"{DEVICES[1]}_01_welcome.png").unlink()
        self.assertEqual(len([w for w in self.failed() if w.startswith("export")]), 2)

    def test_only_one_device_set_fails(self):
        shutil.rmtree(self.out / DEVICES[1])
        self.assertTrue(any("an iPhone and an iPad" in w for w in self.failed()))

    def test_planted_copy_and_delete_are_what_the_real_check_must_catch(self):
        note = self.h.plant(self.out, "copy")
        self.assertIn("ja/01_welcome.png", note)
        d = Path(sorted(p for p in self.out.iterdir())[0])
        self.assertEqual((d / "raw/ja/01_welcome.png").read_bytes(), (d / "raw/de/01_welcome.png").read_bytes())
        self.assertEqual((d / "raw/ja/01_welcome.texts.json").read_text(), (d / "raw/de/01_welcome.texts.json").read_text())
        self.assertIn("tr/02_settings.png", self.h.plant(self.out, "delete"))
        self.assertFalse((d / "raw/tr/02_settings.png").exists()); self.assertFalse((d / "raw/tr/02_settings.texts.json").exists())

    def test_expect_names_the_locale_and_the_defect(self):
        pat = "shows de|identical image"
        self.assertTrue(self.h.expect("  - ja/01_welcome.png: shows de strings (3 lines) more than ja (0)", "ja", pat)[0])
        self.assertTrue(self.h.expect("  - identical image in 2 languages: de/01_welcome.png, ja/01_welcome.png", "ja", pat)[0])
        self.assertTrue(self.h.expect("  - tr: missing 02_settings.png", "tr", "missing")[0])
        self.assertFalse(self.h.expect("checked 16 screenshots in 4 languages: 0 problem(s)", "ja", pat)[0])
        self.assertFalse(self.h.expect("  - ar/01_welcome.png: shows de strings", "ja", pat)[0])  # names another language
        self.assertFalse(self.h.expect("  - jar/01.png: identical image", "ja", pat)[0])

    def test_only_our_own_booted_pool_simulators_are_listed(self):
        devs = {"devices": {"rt": [{"udid": "A", "name": "shotfleet-iphone-17-pro-max-1", "state": "Booted"},
                                   {"udid": "B", "name": "shotfleet-ipad-pro-13-inch-m5-12gb-2", "state": "Booted"},
                                   {"udid": "C", "name": "shotfleet-iphone-17-pro-max-3", "state": "Shutdown"},
                                   {"udid": "D", "name": "iPhone 17 Pro", "state": "Booted"},
                                   {"udid": "E", "name": "my-shotfleet-iphone-1", "state": "Booted"},
                                   {"udid": "F", "name": "shotfleet-1", "state": "Booted"}]}}
        self.assertEqual(self.h.booted_pool_sims(json.dumps(devs)), ["A", "B"])
        self.assertEqual(self.h.booted_pool_sims(""), [])


class AndroidHelper(unittest.TestCase):
    """The same assertions on the Android layout: one phone set, Play listing folders."""
    def setUp(self):
        self._d = tempfile.TemporaryDirectory(); self.addCleanup(self._d.cleanup)
        self.d = Path(self._d.name); self.h = load_helper(self.d)
        self.out, self.fl, self.hooks = self.d / "out", self.d / "fastlane", self.d / "hooks.log"
        make_out(self.out, android=True); make_fastlane(self.out, self.fl, android=True); self.hooks.write_text(GOOD_HOOKS)

    def failed(self):
        return [w for w, ok, _ in self.h.tree(self.out, self.fl, self.hooks, LOCALES, no_ocr, "android") if not ok]

    def test_good_android_tree_passes(self):
        self.assertEqual(self.failed(), [])

    def test_ios_layout_is_not_an_android_run(self):
        shutil.rmtree(self.out / "phone"); make_out(self.out)
        self.assertTrue(any("a phone set" in w for w in self.failed()))

    def test_export_in_the_ios_folders_or_missing_a_listing_fails(self):
        shutil.rmtree(self.fl / "metadata/android/ja-JP")
        self.assertEqual([w for w in self.failed() if w.startswith("export")], ["export: ja-JP has 2 screenshots (one set per device)"])
        shutil.rmtree(self.fl); make_fastlane(self.out, self.fl)  # the App Store layout
        self.assertEqual(len([w for w in self.failed() if w.startswith("export")]), 4)

    def test_identical_images_and_missing_screenshots_fail(self):
        self.h.plant(self.out, "copy")
        self.assertTrue(any("identical image" in w for w in self.failed()))
        self.h.plant(self.out, "delete")
        self.assertTrue(any("screenshots in every language" in w for w in self.failed()))


FAKE_SF = '''#!/usr/bin/env python3
"""Stands in for shotfleet: same commands and output files, no devices. FAKE_DEFECT picks one thing to get wrong."""
import os, subprocess, sys, tomllib
from pathlib import Path
sys.path.insert(0, %(tests)r)
import test_fixture_e2e as t
defect = os.environ.get("FAKE_DEFECT", "")
cmd, args = sys.argv[1], sys.argv[2:]

def hook(cfg, event, **env):
    hooks = tomllib.loads(Path(cfg).read_text()).get("hooks", {})
    if event in hooks and defect != "no-hooks":
        subprocess.run(["/bin/sh", "-c", hooks[event]], cwd=Path(cfg).parent, env={**os.environ, **env}, check=True)

if cmd == "doctor": print("iOS: ready   Android: ready")
elif cmd == "init":
    app, dest = args[0], Path(args[args.index("--dir") + 1])
    section = '[android]\\napk = "' if app.endswith(".apk") else '[ios]\\napp = "'
    (dest / "shotfleet.toml").write_text(section + app + '"\\n'); (dest / "flow.yaml").write_text("- launchApp\\n")
elif cmd == "run":
    cfg = Path(args[0]).resolve(); out = cfg.parent / "out"
    locales = args[args.index("--locales") + 1]
    hook(cfg, "before_run", SHOTFLEET_LOCALES=locales)
    t.make_out(out, locales.split(","), config=str(cfg), android="android" in tomllib.loads(cfg.read_text()))
    if defect == "bad-german":
        for p in out.glob("*/raw/de/01_welcome.texts.json"): p.write_text('["Welcome", "Next"]')
    hook(cfg, "after_run", SHOTFLEET_EXIT="0", SHOTFLEET_PROBLEMS="0")
elif cmd == "check":
    bad = 0
    for d in sorted(Path(args[0]).iterdir()):
        raw = d / "raw"; seen = {}
        names = {p.name for p in raw.glob("*/*.png")}
        for lp in sorted(raw.iterdir()):
            have = {p.name for p in lp.glob("*.png")}
            if have != names: print(f"  - {lp.name}: missing {', '.join(sorted(names - have))}"); bad = 1
            for p in lp.glob("*.png"): seen.setdefault((p.name, p.read_bytes()), []).append(f"{lp.name}/{p.name}")
        for files in seen.values():
            if len(files) > 1 and defect != "blind-check":  # blind-check: a detector that was removed
                print(f"  - identical image in {len(files)} languages: {', '.join(files)}"); bad = 1
    sys.exit(bad)
elif cmd == "export":
    out, fl = Path(args[0]), Path(args[args.index("--fastlane") + 1])
    import json
    cfg = json.loads(next(out.glob("*/run.json")).read_text())["config"]
    hook(cfg, "before_export", SHOTFLEET_FASTLANE=str(fl))
    t.make_fastlane(out, fl, android=json.loads(next(out.glob("*/run.json")).read_text()).get("platform") == "android")
    hook(cfg, "after_export", SHOTFLEET_EXIT="0")
'''

FAKE_ADB = '''#!/bin/sh
echo "List of devices attached"; [ -n "${FAKE_EMUS:-}" ] && printf '%s\\tdevice\\n' $FAKE_EMUS; exit 0
'''

FAKE_XCRUN = '''#!/bin/sh
case "$1" in
  simctl) if [ -n "${FAKE_BOOTED:-}" ]; then echo "$FAKE_BOOTED"; else echo '{"devices":{}}'; fi ;;
  *) while [ $# -gt 0 ]; do if [ "$1" = -o ]; then shift; echo fake > "$1"; fi; shift; done ;;
esac
'''


@unittest.skipUnless(sys.platform == "darwin", "the script is macOS only")
class WholeScriptWithFakes(unittest.TestCase):
    """The shell flow end to end against fakes that never touch a device (xcrun, shotfleet, df and memory_pressure are fakes)."""

    def setUp(self):
        self._d = tempfile.TemporaryDirectory(); self.addCleanup(self._d.cleanup)
        d = self.d = Path(self._d.name); (d / "bin").mkdir(); (d / "tmp").mkdir()
        shims = {"xcrun": FAKE_XCRUN, "adb": FAKE_ADB, "codesign": "#!/bin/sh\nexit 0\n",
                 "df": "#!/bin/sh\necho 'Filesystem 1024-blocks Used Available Capacity Mounted'\necho \"/dev/x 1 1 ${FAKE_FREE_KB:-99999999} 1% /\"\n",
                 "memory_pressure": "#!/bin/sh\necho \"System-wide memory free percentage: ${FAKE_FREE_PCT:-50}%\"\n",
                 "sysctl": "#!/bin/sh\necho ${FAKE_LEVEL:-1}\n"}
        for name, body in shims.items(): (d / "bin" / name).write_text(body); (d / "bin" / name).chmod(0o755)
        sf = d / "fake-shotfleet"; sf.write_text(FAKE_SF % {"tests": str(ROOT / "tests")}); sf.chmod(0o755)
        self.env = {**os.environ, "PATH": f"{d / 'bin'}:{os.environ['PATH']}", "TMPDIR": str(d / "tmp"), "SHOTFLEET_E2E": "1",
                    "SHOTFLEET_BIN": str(sf), "SHOTFLEET_E2E_ADB": str(d / "bin/adb")}
        for k in ("FAKE_DEFECT", "FAKE_BOOTED", "FAKE_FREE_KB", "FAKE_FREE_PCT", "FAKE_LEVEL", "FAKE_EMUS", "SHOTFLEET_E2E_ANDROID"): self.env.pop(k, None)

    def run_script(self, *args, **env):
        r = subprocess.run(["sh", str(SCRIPT), *args], capture_output=True, text=True, env={**self.env, **env}, timeout=120)
        return r.returncode, r.stdout, r.stderr

    def test_clean_run_passes_and_cleans_up(self):
        code, out, err = self.run_script()
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, r"PASS: all \d+ assertions passed")
        for phase in ("build the fixture app", "shotfleet init", "shotfleet doctor", "shotfleet run", "shotfleet check",
                      "shotfleet export", "planted failures"):
            self.assertIn(f"== {phase}", out)
        self.assertRegex(out, r"total \d+ min \d+ s"); self.assertIn("SKIP android", out); self.assertNotIn("FAIL", out); self.assertNotIn("== android", out)  # iOS only by default
        self.assertRegex(out, r"PASS check-copy exits 1"); self.assertRegex(out, r"PASS check-delete exits 1")
        self.assertEqual(list((self.d / "tmp").iterdir()), [])  # temp work dir removed on success

    def test_keep_flag_and_android_flags(self):
        code, out, err = self.run_script("--keep", "--skip-android", "--platform-only", "ios")
        self.assertEqual(code, 0, out + err)
        kept = list((self.d / "tmp").glob("shotfleet-e2e.*"))
        self.assertEqual(len(kept), 1)
        toml = (kept[0] / "proj/shotfleet.toml").read_text()
        for want in ('device_types = ["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]', "before_run", "after_export", "[ios]"):
            self.assertIn(want, toml)
        self.assertIn("takeScreenshot: 02_settings", (kept[0] / "proj/flow.yaml").read_text())

    @unittest.skipUnless(CAN_BUILD_APK, "the Android fixture builds with the SDK's own tools and a JDK")
    def test_android_flag_adds_the_android_half_after_ios(self):
        code, out, err = self.run_script("--android", "--keep")
        self.assertEqual(code, 0, out + err)
        phases = re.findall(r"^== (.*)$", out, re.M)
        self.assertEqual(phases.index("build the fixture app"), 0)
        self.assertEqual([p for p in phases if p.startswith("android: ")][:2], ["android: build the fixture app", "android: shotfleet init"])
        self.assertNotIn("SKIP android", out)
        for what in ("android-run exits 0", "android-check-copy exits 1", "android-check-delete exits 1", "phone: 2 screenshots in every language",
                     "export: tr-TR has 2 screenshots (one set per device)", "hook after_export fired (hooks.log)"):
            self.assertIn(f"PASS {what}", out)
        kept = next((self.d / "tmp").glob("shotfleet-e2e.*"))
        toml = (kept / "proj-android/shotfleet.toml").read_text()
        for want in ("[android]", 'apk = "', 'devices = ["phone"]', "parallel = 2", "before_run"): self.assertIn(want, toml)
        self.assertTrue((kept / "build-android/FleetFixture.apk").is_file())

    @unittest.skipUnless(CAN_BUILD_APK, "the Android fixture builds with the SDK's own tools and a JDK")
    def test_platform_only_android_skips_ios_and_the_env_var_opts_in(self):
        for args, env in ((["--platform-only", "android"], {}), (["--keep"], {"SHOTFLEET_E2E_ANDROID": "1"})):
            code, out, err = self.run_script(*args, **env)
            self.assertEqual(code, 0, out + err); self.assertIn("== android: shotfleet run", out); self.assertNotIn("SKIP android", out)
            self.assertEqual("== build the fixture app" in out, "--keep" in args)  # the env var adds Android to the iOS default
        code, out, _ = self.run_script("--skip-android", SHOTFLEET_E2E_ANDROID="1")
        self.assertEqual(code, 0); self.assertIn("SKIP android", out)

    @unittest.skipUnless(CAN_BUILD_APK, "the Android fixture builds with the SDK's own tools and a JDK")
    def test_android_check_that_misses_planted_defects_fails_the_script(self):
        code, out, _ = self.run_script("--platform-only", "android", FAKE_DEFECT="blind-check")
        self.assertEqual(code, 1); self.assertIn("FAIL android-check-copy exits 1", out); self.assertNotIn("FAIL check-copy", out)

    def test_android_refuses_while_an_emulator_is_on_shotfleets_ports(self):
        code, out, err = self.run_script("--platform-only", "android", FAKE_EMUS="emulator-5702")
        self.assertEqual(code, 2, (out, err)); self.assertIn("emulator is already running", err); self.assertNotIn("== ", out)

    def test_no_hooks_failed_hook_assertions_and_work_dir_kept(self):
        code, out, err = self.run_script(FAKE_DEFECT="no-hooks")
        self.assertEqual(code, 1, out + err)
        self.assertEqual(len(re.findall(r"^FAIL hook ", out, re.M)), 4)
        self.assertRegex(out, r"FAIL: 4 of \d+ assertions failed"); self.assertIn("work dir kept", out)
        self.assertEqual(len(list((self.d / "tmp").glob("shotfleet-e2e.*"))), 1)

    def test_wrong_german_text_fails_the_script(self):
        code, out, _ = self.run_script(FAKE_DEFECT="bad-german")
        self.assertEqual(code, 1); self.assertIn("FAIL iphone-17-pro-max: de/01_welcome.png shows 'Weiter'", out)

    def test_a_check_that_misses_planted_defects_fails_the_script(self):
        code, out, _ = self.run_script(FAKE_DEFECT="blind-check")
        self.assertEqual(code, 1)
        self.assertIn("FAIL check-copy exits 1", out)  # nothing flagged the copied picture: the guardrail itself failed

    def test_preflight_refuses_low_disk_critical_memory_and_a_booted_pool(self):
        for env, why in (({"FAKE_FREE_KB": "1000000"}, "need 5 GB"), ({"FAKE_LEVEL": "4"}, "memory pressure is critical"),
                         ({"FAKE_FREE_PCT": "4"}, "memory pressure is critical"),
                         ({"FAKE_BOOTED": json.dumps({"devices": {"rt": [{"udid": "U", "name": "shotfleet-iphone-17-pro-max-1", "state": "Booted"}]}})},
                          "already booted")):
            code, out, err = self.run_script(**env)
            self.assertEqual(code, 2, (env, out, err)); self.assertIn(why, err); self.assertNotIn("== ", out)


if __name__ == "__main__":
    unittest.main()


class LinuxRefusals(unittest.TestCase):
    """On Linux the script runs only the Android half, and says so instead of failing in the middle."""
    @unittest.skipIf(sys.platform == "darwin", "the Linux messages")
    def test_ios_on_linux_is_refused_with_the_android_command(self):
        r = subprocess.run(["sh", str(Path(__file__).resolve().parent.parent / "tools/fixture-e2e.sh")], capture_output=True, text=True,
                           env={**os.environ, "SHOTFLEET_E2E": "1"})
        self.assertEqual(r.returncode, 2)
        self.assertIn("only the Android half runs", r.stderr)
        self.assertIn("--platform-only android", r.stderr)
