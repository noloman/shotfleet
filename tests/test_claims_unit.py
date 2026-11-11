"""Unit-layer proofs for claims in tests/claims.json (2026-10-03): every language reaches both platform runs (C044), the hook environment and exit codes (C068), a translated caption over an English UI (C100), and
the framework matrix of `init` (C121).

Fake tools only: no simulator, emulator, Maestro, network, Xcode or Gradle. Everything runs on Linux and on a Mac; to run it as if on an
Apple-silicon Mac: python3 tools/pretend-mac.py test_claims_unit

Run: python3 -m unittest tests.test_claims_unit
"""
import contextlib, io, json, os, plistlib, re, shutil, subprocess, sys, tempfile, time, tomllib, unittest, urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf
sf.USE_DEVICE_LOCK = False  # fake runs touch no device; two test suites at once must not refuse each other

ROOT = Path(__file__).resolve().parent.parent
WORDS = {"en": "Next", "de": "Weiter", "ja": "次へ", "fr": "Suivant"}  # the app ships these four languages


def fake_sh(cmd, **kw):
    """Every host command is a no-op here, except the two that read an Info.plist (plist_value and plist_to_json go through sh and the bundle id must be real)."""
    if cmd and Path(str(cmd[0])).name in ("PlistBuddy", "plutil"): return subprocess.run(cmd, capture_output=True, text=True)
    return subprocess.CompletedProcess(cmd, 0, "", "")


class FleetCase(unittest.TestCase):
    """A project with an iOS app and an Android app (four languages each), a licence file location of its own, and stand-ins for every
    tool `run` starts: simulators, emulators and Maestro. `self.ios` and `self.android` record the languages each device set was run with."""
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.d, True)
        self.ios, self.android, self.device_types = {}, {}, []
        app = self.d / "My.app"
        for lp, word in WORDS.items():
            (app / f"{lp}.lproj").mkdir(parents=True); (app / f"{lp}.lproj/Localizable.strings").write_text(f'"next" = "{word}";\n')
        (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.example.my", "CFBundleLocalizations": list(WORDS),
                                                         "DTPlatformName": "iphonesimulator"}))
        for lp, word in WORDS.items():
            (self.d / "locales" / lp).mkdir(parents=True); (self.d / "locales" / lp / "translation.json").write_text(json.dumps({"next": word}, ensure_ascii=False))
        (self.d / "a.apk").write_bytes(b"x")
        (self.d / "flow.yaml").write_text("- launchApp\n- tapOn: Next\n- takeScreenshot: 01\n")
        for p in (mock.patch.object(sf.sys, "frozen", True, create=True), mock.patch.object(sf, "NO_HOOKS", False),
                  mock.patch.object(sf, "maestro_cmd", return_value="/usr/bin/maestro"), mock.patch.object(sf, "read_maestro_version", return_value="2.0.10"),
                  mock.patch.object(sf, "java_env", return_value={}), mock.patch.object(sf, "fit_parallel", side_effect=lambda n: n),
                  mock.patch.object(sf, "kill_stale_drivers"), mock.patch.object(sf, "shutdown_sims"), mock.patch.object(sf, "OUR_SIMS", set()),
                  mock.patch.object(sf, "latest_ios_runtime", return_value="com.apple.CoreSimulator.SimRuntime.iOS-27-0"),
                  mock.patch.object(sf, "make_pool", side_effect=self.fake_make_pool), mock.patch.object(sf, "android_pool", side_effect=self.fake_android_pool),
                  mock.patch.object(sf, "run_guarded", side_effect=self.fake_maestro), mock.patch.object(sf, "cmd_check", return_value=0),
                  mock.patch.object(sf, "aapt2", return_value="aapt2"), mock.patch.object(sf, "sh", side_effect=fake_sh)):
            p.start(); self.addCleanup(p.stop)

    # --- stand-ins -------------------------------------------------------------------------------------------------
    def fake_make_pool(self, n, device_type, runtime, prefix="shotfleet", simctl=()):
        self.device_types.append(device_type)
        class Sim:
            udid = "U1"
            def run(self, *a, check=True): return ""
        return [Sim()]

    def fake_android_pool(self, n, cfg, pool):
        test, device = self, cfg.get("device", "phone")
        class Emu:
            def __init__(self, i): self.serial = f"emulator-{5702 + 2 * i}"
            def adb(self, *a, check=True, timeout=180):
                if a[:3] == ("shell", "cmd", "locale"): test.android.setdefault(device, []).append(a[-1])  # set-app-locales ... --locales <lp>
                return ""
        pool.extend(Emu(i) for i in range(n))

    def fake_maestro(self, cmd, env=None, timeout=None, cwd=None, **watchdog):  # progress= and stall_s= (the stall watchdog)
        flows, junit = Path(cmd[cmd.index("test") + 1]), Path(cmd[cmd.index("--output") + 1])
        yamls = sorted(flows.glob("*.yaml")); cases = ""
        if flows.parent.name == "flows" and "attempt" in flows.name:  # iOS: one flow per language, screenshots named <lp>/01 relative to Maestro's working directory (cwd)
            out, lps = flows.parent.parent.parent, [f.stem for f in yamls]
            self.ios.setdefault(self.device_types[-1], []).extend(lps)
            for lp in lps: (Path(cwd) / lp).mkdir(parents=True, exist_ok=True); (Path(cwd) / lp / "01.png").write_bytes(b"x"); cases += f'<testcase name="{lp}" time="1"/>'
        else:  # Android: r<N>_f<j>.yaml per emulator; the log says which emulator ran which
            out, dbg = flows.parent.parent.parent, Path(cmd[cmd.index("--debug-output") + 1]); dbg.mkdir(parents=True, exist_ok=True)
            devs, log = cmd[cmd.index("--device") + 1].split(","), ""
            for j, f in enumerate(yamls):
                log += f"Selected device {devs[j]} using port 7001 with execution plan ExecutionPlan(flowsToRun=[{f}], sequence=x)\n"
                shots = Path(cwd) / f.stem; shots.mkdir(parents=True); (shots / "01.png").write_bytes(b"x")  # `<flow name>/01` relative to cwd
                cases += f'<testcase name="{f.stem}" time="1"/>'
            (dbg / "maestro.log").write_text(log)
        junit.write_text(f"<testsuites><testsuite>{cases}</testsuite></testsuites>")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    # --- helpers ---------------------------------------------------------------------------------------------------
    def config(self, ios="", android="", extra=""):
        text = ("[ios]\napp = \"My.app\"\n" + ios if ios is not None else "") + ("\n[android]\napk = \"a.apk\"\npackage = \"p.q\"\n"
                                                                                 "strings = \"locales/*/translation.json\"\n" + android if android is not None else "")
        (self.d / "shotfleet.toml").write_text(text + extra)
        return str(self.d / "shotfleet.toml")

    def main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch.object(sf.urllib.request, "urlopen", side_effect=AssertionError("the network was used")):
            code = sf.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class TierReachesBothPlatformRuns(FleetCase):
    """C044: a licence runs every language on both platforms, iPad and tablet sets included, and exports; without one `run` is capped
    and `export` is refused. The cap is applied inside ios_run and android_run, so the stand-ins here sit below them (at the
    simulator pool, the emulator pool and Maestro), not above."""
    def shipped(self):
        return sf.shipped_locales({lp: {"next": w} for lp, w in WORDS.items()})

    def test_a_run_gives_every_language_to_ios_and_to_android(self):
        every = self.shipped()
        self.assertEqual(len(every), 4)  # the fixture ships four languages: capping at 2 would be visible
        code, out, err = self.main("run", self.config())
        self.assertEqual(code, 0, err)
        self.assertEqual([sorted(v) for v in self.ios.values()], [every])
        self.assertEqual({k: sorted(v) for k, v in self.android.items()}, {"phone": every})

    def test_ipad_and_tablet_sets_get_every_language_too(self):
        every = self.shipped()
        ipad = "com.apple.CoreSimulator.SimDeviceType.iPad-Pro-13-inch-M5-12GB"
        iphone = "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"
        cfg = self.config(ios=f'device_types = ["{iphone}", "{ipad}"]\n', android='devices = ["phone", "tablet", "tablet-7"]\n')
        want = every
        self.main("run", cfg)
        self.assertEqual({k: sorted(v) for k, v in self.ios.items()}, {iphone: sorted(want), ipad: sorted(want)})
        self.assertEqual({k: sorted(v) for k, v in self.android.items()}, {d: sorted(want) for d in ("phone", "tablet", "tablet-7")})

    def test_the_export_is_the_real_fastlane_copy(self):
        out = self.d / "out"; (out / "raw/de").mkdir(parents=True); (out / "raw/de/01.png").write_bytes(b"x")
        (out / "check.json").write_text(json.dumps({"problems": []}))
        (out / "run.json").write_text(json.dumps({"platform": "ios", "locales": {"de": {"ok": True}}}))
        code, text, err = self.main("export", str(out), "--fastlane", str(self.d / "fl"))
        self.assertEqual(code, 0, err)
        self.assertTrue((self.d / "fl/screenshots/de-DE/01.png").is_file(), text)


# ---------------------------------------------------------------------------------------------------------------------
# C068: hooks
# ---------------------------------------------------------------------------------------------------------------------
README = (ROOT / "docs/guide.md").read_text()


def documented_variables():
    """{event: set of SHOTFLEET_ names} read from the README paragraph that lists them."""
    m = re.search(r"Variables on every event:(.*?)`--no-hooks` skips", README, re.S)
    assert m, "the README paragraph that lists the hook variables moved: update this reader"
    first, run_hooks, after_run, export_hooks = [c.strip() for c in " ".join(m.group(1).split()).split(";")]
    names = lambda text: {"SHOTFLEET_" + n.removeprefix("SHOTFLEET_").lstrip("_") for n in re.findall(r"`(_?[A-Z][A-Z_]+)`", text)}
    base = names(first)
    export_main, _, export_after = export_hooks.partition("(and")
    table = {ev: set(base) for ev in sf.HOOK_EVENTS}
    for ev in ("before_run", "after_run"): table[ev] |= names(run_hooks)
    table["after_run"] |= names(after_run)
    for ev in ("before_export", "after_export"): table[ev] |= names(export_main)
    table["after_export"] |= names(export_after)
    return table


class HookEventsAndExitCodes(FleetCase):
    """C068: the four events, the variables each gets (as the README lists them), a failing before_* stops the command with exit 2,
    a failing after_* makes the exit code 1, and --no-hooks skips them all."""
    def setUp(self):
        super().setUp()
        env = {k: v for k, v in os.environ.items() if not k.startswith("SHOTFLEET_")}
        for p in (mock.patch.dict(os.environ, env, clear=True), mock.patch.object(sf.sys, "frozen", False), mock.patch.object(sf, "capture_platform", return_value=0)):
            p.start(); self.addCleanup(p.stop)
        self.out = self.d / "out"; self.out.mkdir()
        (self.out / "check.json").write_text(json.dumps({"problems": ["a", "b"]}))

    def recorder(self, event): return f"env | grep '^SHOTFLEET_' | sort > {event}.env"

    def hooks(self, **cmds): return "[hooks]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in cmds.items())

    def seen(self, event):
        return {l.split("=", 1)[0]: l.split("=", 1)[1] for l in (self.d / f"{event}.env").read_text().splitlines()}

    def export_inputs(self, cfg):
        (self.out / "run.json").write_text(json.dumps({"config": cfg, "platform": "ios", "locales": {"de": {"ok": True}}}))

    def test_each_event_gets_exactly_the_variables_the_readme_lists(self):
        table = documented_variables()
        self.assertEqual(set(table), set(sf.HOOK_EVENTS))
        self.assertEqual(sorted(table["before_export"]), ["SHOTFLEET_CONFIG", "SHOTFLEET_EVENT", "SHOTFLEET_FASTLANE", "SHOTFLEET_OUT", "SHOTFLEET_PLATFORM", "SHOTFLEET_REPORT", "SHOTFLEET_VERSION"])
        cfg = self.config(ios="", android=None, extra=self.hooks(**{ev: self.recorder(ev) for ev in sf.HOOK_EVENTS}))
        self.assertEqual(self.main("run", cfg, "--locales", "de")[0], 0)
        with mock.patch.object(sf, "cmd_export", return_value=0):
            self.export_inputs(cfg)
            self.assertEqual(self.main("export", str(self.out), "--fastlane", str(self.d / "fl"))[0], 0)
        for ev in sf.HOOK_EVENTS:
            with self.subTest(event=ev):
                self.assertEqual(set(self.seen(ev)), table[ev])
        run, exp = self.seen("after_run"), self.seen("after_export")
        self.assertEqual((run["SHOTFLEET_EVENT"], run["SHOTFLEET_VERSION"], run["SHOTFLEET_PLATFORM"], str(Path(run["SHOTFLEET_CONFIG"]).resolve())),
                         ("after_run", sf.VERSION, "ios", str(Path(cfg).resolve())))  # /var is /private/var on macOS
        self.assertEqual((run["SHOTFLEET_OUT"], run["SHOTFLEET_REPORT"]), (str(self.out.resolve()), str(self.out.resolve() / "check.json")))
        self.assertEqual((run["SHOTFLEET_BUNDLE_ID"], run["SHOTFLEET_LOCALES"], run["SHOTFLEET_EXIT"], run["SHOTFLEET_PROBLEMS"]), ("com.example.my", "de", "0", "2"))
        self.assertEqual((exp["SHOTFLEET_EVENT"], exp["SHOTFLEET_EXIT"], exp["SHOTFLEET_FASTLANE"]), ("after_export", "0", str((self.d / "fl").resolve())))
        self.assertEqual(self.seen("before_run")["SHOTFLEET_LOCALES"], "de")

    def test_locales_is_empty_unless_the_run_is_restricted_and_bundle_id_is_the_android_package(self):
        cfg = self.config(ios=None, android="", extra=self.hooks(before_run=self.recorder("before_run")))
        self.assertEqual(self.main("run", cfg)[0], 0)
        seen = self.seen("before_run")
        self.assertEqual((seen["SHOTFLEET_LOCALES"], seen["SHOTFLEET_BUNDLE_ID"], seen["SHOTFLEET_PLATFORM"]), ("", "p.q", "android"))

    def test_a_failing_before_run_stops_the_command_with_exit_2_and_a_one_line_message(self):
        cfg = self.config(extra=self.hooks(before_run=["exit 5", "touch never"]), android=None)
        with mock.patch.object(sf, "capture_platform") as capture:
            code, _, err = self.main("run", cfg)
        self.assertEqual(code, 2); capture.assert_not_called()
        self.assertEqual(err.strip().splitlines()[-1], "shotfleet: hook before_run failed (exit 5): exit 5")
        self.assertFalse((self.d / "never").exists())  # the commands after the failing one do not run

    def test_a_failing_after_run_makes_the_exit_code_1_even_when_the_run_was_clean(self):
        cfg = self.config(extra=self.hooks(after_run="exit 4"), android=None)
        code, _, err = self.main("run", cfg)
        self.assertEqual(code, 1); self.assertIn("hook after_run failed (exit 4): exit 4", err)

    def test_a_failing_after_run_does_not_hide_a_worse_exit_code_of_the_run(self):
        cfg = self.config(extra=self.hooks(after_run="exit 4"), android=None)
        with mock.patch.object(sf, "capture_platform", return_value=1): self.assertEqual(self.main("run", cfg)[0], 1)

    def test_a_failing_before_export_stops_before_anything_is_copied_and_a_failing_after_export_gives_exit_1(self):
        cfg = self.config(extra=self.hooks(before_export="exit 7"), android=None); self.export_inputs(cfg)
        with mock.patch.object(sf, "cmd_export", return_value=0) as export:
            code, _, err = self.main("export", str(self.out), "--fastlane", str(self.d / "fl"))
            self.assertEqual(code, 2); export.assert_not_called()
            self.assertEqual(err.strip().splitlines()[-1], "shotfleet: hook before_export failed (exit 7): exit 7")
            cfg = self.config(extra=self.hooks(after_export="exit 3"), android=None); self.export_inputs(cfg)
            code, _, err = self.main("export", str(self.out), "--fastlane", str(self.d / "fl"))
            self.assertEqual(code, 1); export.assert_called_once(); self.assertIn("hook after_export failed (exit 3): exit 3", err)

    def test_a_hook_that_hangs_is_stopped_at_hook_timeout_s_and_counts_as_a_failure(self):
        cfg = self.config(extra='[hooks]\nhook_timeout_s = 1\nbefore_run = "exec sleep 30"\n', android=None)
        started = time.time()
        code, _, err = self.main("run", cfg)
        self.assertEqual(code, 2); self.assertIn("hook before_run failed (exit 124)", err); self.assertLess(time.time() - started, 20)

    def test_no_hooks_runs_none_of_the_four_events_whatever_they_would_do(self):
        cfg = self.config(extra=self.hooks(**{ev: "exit 9" for ev in sf.HOOK_EVENTS}), android=None); self.export_inputs(cfg)
        with mock.patch.object(sf, "cmd_export", return_value=0):
            self.assertEqual(self.main("run", cfg, "--no-hooks")[0], 0)
            self.assertEqual(self.main("export", str(self.out), "--fastlane", str(self.d / "fl"), "--no-hooks")[0], 0)

    def test_the_four_events_are_the_ones_the_readme_example_shows(self):
        block = re.search(r"\[hooks\]\n(.*?)```", README, re.S).group(1)
        self.assertEqual(re.findall(r"^(\w+)\s*=", block, re.M)[:4], ["before_run", "after_run", "before_export", "after_export"])
        self.assertEqual(list(sf.HOOK_EVENTS), ["before_run", "after_run", "before_export", "after_export"])


# ---------------------------------------------------------------------------------------------------------------------
# C100: a translated caption over an app that is still English
# ---------------------------------------------------------------------------------------------------------------------
FONTS = ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
         "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc")
STORE_STRINGS = {"en": {"a": "Next", "b": "Settings", "c": "Start Training", "d": "Training log"},
                 "ja": {"a": "次へ", "b": "設定", "c": "トレーニング開始", "d": "記録"}}
CAPTION_JA = "トレーニングを簡単に記録"


def golden_screenshot(path, ui, caption, size=(1320, 2868)):
    """A framed store screenshot: a caption band on top, the app's UI lines below. Drawn with PIL when PIL and a Japanese font exist
    (then the pixels really show it); otherwise a PNG of the right size. Returns True when the text was drawn."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont
        font_file = next(f for f in FONTS if Path(f).is_file())
    except (ImportError, StopIteration):
        w, h = size
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + b"\x08\x02\0\0\0" + str(path).encode())
        return False
    img = Image.new("RGB", size, "white"); draw = ImageDraw.Draw(img)
    draw.text((80, 140), caption, fill="black", font=ImageFont.truetype(font_file, 120))
    for i, line in enumerate(ui): draw.text((120, 800 + i * 260), line, fill="black", font=ImageFont.truetype(font_file, 96))
    img.save(path)
    return True


class CaptionOverAnEnglishUi(unittest.TestCase):
    """C100: a Japanese listing whose caption is Japanese but whose app UI is still English is reported, by name. The pictures are
    generated here. The text recognition is real Tesseract where it is installed (Linux) and a fixture of what macOS Vision
    returns for such a picture otherwise: ocr.swift itself (the caption box) only runs on a Mac and is not run here."""
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.d, True)
        for lp, words in STORE_STRINGS.items():
            (self.d / "locales" / lp).mkdir(parents=True); (self.d / "locales" / lp / "translation.json").write_text(json.dumps(words, ensure_ascii=False))
        self.strings = str(self.d / "locales/*/translation.json")

    def check(self, *extra, vision=None):
        """sf.main(["check", ...]) on self.d/shots; `vision` is what the (faked) macOS text recognition answers for every picture."""
        patches = []
        if vision is not None:
            patches = [mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "warm_up_ocr", return_value=True),
                       mock.patch.object(sf, "readable_languages", return_value={"en", "ja"}), mock.patch.object(sf, "read_text", side_effect=lambda *a, **k: vision)]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as stack, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            for p in patches: stack.enter_context(p)
            code = sf.main(["check", str(self.d / "shots"), "--strings", self.strings, "--report", str(self.d / "rep"), *extra])
        return code, json.loads((self.d / "rep/check.json").read_text()), out.getvalue()

    def vision_answer(self, ui, caption, caption_lang):  # the shape ocr.swift prints, see test_ocr_swift_prints_the_keys_the_check_reads
        text = "\n".join([caption, *ui])
        return {"text": text, "chars": len(text), "lang": "en", "langs": {"en": 0.9}, "lines": [], "caption": caption, "caption_lang": caption_lang}

    def test_a_japanese_caption_over_an_english_ui_is_named_with_both_languages(self):
        for name in ("01.png", "02.png"): golden_screenshot(self.d / "shots/ja" / name, STORE_STRINGS["en"].values(), CAPTION_JA)
        code, report, out = self.check(vision=self.vision_answer(list(STORE_STRINGS["en"].values()), CAPTION_JA, "ja"))
        self.assertEqual(code, 1)
        self.assertEqual(report["problems"], [f"ja/{n}: the caption is in ja but the app UI shows en strings (4 lines) more than ja (0)" for n in ("01.png", "02.png")])
        self.assertIn("2 problem(s)", out)

    def test_the_same_framing_with_the_ui_translated_is_clean(self):
        golden_screenshot(self.d / "shots/ja/01.png", STORE_STRINGS["ja"].values(), CAPTION_JA)
        code, report, _ = self.check(vision=self.vision_answer(list(STORE_STRINGS["ja"].values()), CAPTION_JA, "ja"))
        self.assertEqual((code, report["problems"]), (0, []))

    def test_an_english_caption_over_an_english_ui_in_the_japanese_folder_is_the_plain_wrong_language_problem(self):
        golden_screenshot(self.d / "shots/ja/01.png", STORE_STRINGS["en"].values(), "Log your training in seconds")
        code, report, _ = self.check(vision=self.vision_answer(list(STORE_STRINGS["en"].values()), "Log your training in seconds", "en"))
        self.assertEqual(report["problems"], ["ja/01.png: shows en strings (4 lines) more than ja (0)"])  # no 'the caption is in' sentence: the caption is not ja

    @unittest.skipIf(sf.vision_available(), "this reads the picture with Tesseract, which is the path off the Mac")
    @unittest.skipUnless(shutil.which("tesseract") and {"eng", "jpn"} <= set(sf.tesseract_languages()), "needs Tesseract with English and Japanese data")
    def test_the_pixels_of_the_golden_sample_are_enough_off_the_mac(self):
        drawn = golden_screenshot(self.d / "shots/ja/01.png", STORE_STRINGS["en"].values(), CAPTION_JA)
        if not drawn: self.skipTest("PIL or a Japanese font is missing")
        golden_screenshot(self.d / "shots/en/01.png", STORE_STRINGS["en"].values(), "Log your training in seconds")
        code, report, _ = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(len(report["problems"]), 1, report["problems"])
        self.assertRegex(report["problems"][0], r"^ja/01\.png: shows en strings \(\d+ lines\) more than ja \(0\)$")  # Tesseract returns no caption box

    def test_ocr_swift_prints_the_keys_the_check_reads(self):
        swift = (ROOT / "ocr.swift").read_text()
        self.assertIn('"caption": caption, "caption_lang": captionLang', swift)
        source = (ROOT / "shotfleet.py").read_text()
        self.assertIn('ocr.get("caption", "")', source); self.assertIn('ocr.get("caption_lang")', source)

    def test_the_same_check_refuses_a_size_the_app_store_does_not_take(self):  # the other half of the launch email: 'checks screenshot sizes against App Store Connect's rules'
        golden_screenshot(self.d / "shots/screenshots/ja/01.png", STORE_STRINGS["ja"].values(), CAPTION_JA, size=(1000, 2000))  # fastlane deliver's layout: App Store screenshots
        code, report, _ = self.check(vision=self.vision_answer(list(STORE_STRINGS["ja"].values()), CAPTION_JA, "ja"))
        self.assertEqual((code, report["problems"]), (1, ["ja/01.png: 1000x2000 isn't an App Store screenshot size"]))

    def test_the_launch_email_says_this_and_no_more(self):
        email = (ROOT / "marketing/launch-email.md").read_text()
        self.assertIn("store listings with translated captions over an app that was still in English", email)
        self.assertIn("It also checks screenshot sizes against App Store Connect's rules.", email)


# ---------------------------------------------------------------------------------------------------------------------
# C121, C122: `shotfleet init` in a framework's project folder, and with an archive. Fake project folders: no framework toolchain
# was run, so these do not turn the 'the build paths are each framework's documented defaults' caveat into a proof.
# ---------------------------------------------------------------------------------------------------------------------
def write_tree(files):
    d = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        f = d / rel; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(text if isinstance(text, bytes) else text.encode())
    return d


def simulator_app(root, rel, bundle="com.example.app"):
    app = root / rel; app.mkdir(parents=True)
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "App", "CFBundleIdentifier": bundle, "DTPlatformName": "iphonesimulator"}))
    (app / "App").write_bytes(b"\0")
    return app


def resx(**strings): return "<root>" + "".join(f'<data name="{k}"><value>{v}</value></data>' for k, v in strings.items()) + "</root>"
def i18n(*langs): return {f"src/assets/i18n/{lp}.json": json.dumps({"next": lp}) for lp in langs}


# name, project files, where its simulator build lands, its APK, the strings glob init writes, the build commands it prints when nothing is built
FRAMEWORKS = (
    ("Flutter", {"pubspec.yaml": "name: demo\nflutter:\n  generate: true\n", **{f"lib/l10n/app_{lp}.arb": json.dumps({"@@locale": lp, "next": lp}) for lp in ("en", "de", "ja")}},
     "build/ios/iphonesimulator/Runner.app", "build/app/outputs/flutter-apk/app-debug.apk", "lib/l10n/*.arb",
     ("flutter build ios --simulator --debug", "flutter build apk --debug")),
    ("React Native", {"package.json": json.dumps({"dependencies": {"react-native": "0.76"}}), **{f"src/locales/{lp}/translation.json": json.dumps({"next": lp}) for lp in ("en", "de", "ja")}},
     "ios/build/Build/Products/Release-iphonesimulator/App.app", "android/app/build/outputs/apk/release/app-release.apk", "src/locales/*/translation.json",
     ("npx react-native run-ios --mode Release", "(cd android && ./gradlew assembleRelease)")),
    ("Expo", {"package.json": json.dumps({"dependencies": {"expo": "~52", "react-native": "0.76"}}), **{f"src/locales/{lp}/translation.json": json.dumps({"next": lp}) for lp in ("en", "de", "ja")}},
     "ios/build/Build/Products/Release-iphonesimulator/App.app", "android/app/build/outputs/apk/release/app-release.apk", "src/locales/*/translation.json",
     ("npx expo run:ios --configuration Release --no-bundler", "npx expo run:android --variant release --no-bundler")),
    ("Capacitor", {"package.json": json.dumps({"dependencies": {"@capacitor/core": "6"}}), **i18n("en", "de", "ja")},
     "ios/build/Build/Products/Debug-iphonesimulator/App.app", "android/app/build/outputs/apk/debug/app-debug.apk", "src/assets/i18n/*.json",
     ("npx cap sync ios", "npx cap sync android")),
    (".NET MAUI", {"App.csproj": "<Project><PropertyGroup><UseMaui>true</UseMaui></PropertyGroup></Project>", "Resources/Strings/AppResources.resx": resx(next="Next"),
                   "Resources/Strings/AppResources.de.resx": resx(next="Weiter"), "Resources/Strings/AppResources.ja.resx": resx(next="次へ")},
     "bin/Debug/net10.0-ios/iossimulator-arm64/App.app", "bin/Debug/net10.0-android/com.example.app-Signed.apk", "Resources/Strings/*.resx",
     ("dotnet build -f net10.0-ios", "dotnet build -f net10.0-android")),
)


class InitInEveryFramework(unittest.TestCase):
    """C121: init, run in the project folder with no arguments, finds each framework's build, writes the strings line, and with nothing
    built prints that framework's own build commands. Kotlin Multiplatform has no strings line to write (see its test)."""
    def init(self, d, dest="."):
        out, old = io.StringIO(), os.getcwd(); os.chdir(d)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out): sf.cmd_init([], dest)
        finally: os.chdir(old)
        return out.getvalue()

    def test_the_simulator_build_is_found_and_the_strings_line_is_written(self):
        for name, files, app, apk, strings, _ in FRAMEWORKS:
            with self.subTest(framework=name):
                d = write_tree(files); simulator_app(d, app, "com.example.demo")
                text = self.init(d)
                cfg = tomllib.loads((d / "shotfleet.toml").read_text())
                self.assertEqual(cfg["ios"]["app"], app)
                self.assertEqual(cfg["ios"]["strings"], strings)
                self.assertIn(f"{name} project: translations from {strings} (3 languages)", text)
                self.assertIn("com.example.demo: 3 languages (de, en, ja)", text)

    def test_the_apk_is_found_where_the_framework_builds_it(self):
        for name, files, app, apk, strings, _ in FRAMEWORKS:
            with self.subTest(framework=name):
                d = write_tree({**files, apk: b"PK"}); simulator_app(d, app)
                with contextlib.redirect_stdout(io.StringIO()):
                    builds = sf.find_builds(d, derived=d / "no-derived-data", project=sf.detect_project(d))
                self.assertEqual(builds, [str((d / app).resolve()), str((d / apk).resolve())])

    def test_nothing_built_prints_the_frameworks_own_commands_for_both_platforms(self):
        for name, files, _, _, _, commands in FRAMEWORKS:
            with self.subTest(framework=name):
                d = write_tree(files)
                with self.assertRaises(sf.Fail) as e, contextlib.redirect_stdout(io.StringIO()):
                    sf.find_builds(d, derived=d / "no-derived-data", project=sf.detect_project(d))
                for command in commands: self.assertIn(command, str(e.exception))
                self.assertNotIn("xcodebuild -scheme <scheme>", str(e.exception))  # not the generic native advice

    def test_kotlin_multiplatform_is_recognised_and_its_gradle_apk_found_but_it_has_no_strings_line(self):
        d = write_tree({"settings.gradle.kts": 'include(":composeApp")', "composeApp/build.gradle.kts": 'plugins { kotlin("multiplatform") }',
                        "composeApp/build/outputs/apk/debug/composeApp-debug.apk": b"PK"})
        project = sf.detect_project(d)
        self.assertEqual((project.name, project.strings), ("Kotlin Multiplatform", None))  # its strings are compiled resources read from the build
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sf.find_builds(d, derived=d / "no-derived-data", project=project), [str((d / "composeApp/build/outputs/apk/debug/composeApp-debug.apk").resolve())])

    def test_the_readme_names_the_same_frameworks(self):
        para = next(p for p in README.split("\n\n") if p.startswith("**Run `shotfleet init` in the project folder**"))
        for word in ("Flutter", "React Native and Expo", "Capacitor", ".NET MAUI", "Kotlin Multiplatform"): self.assertIn(word, para)


class InitUnpacksArchives(unittest.TestCase):
    """C122: an archive given to init is unpacked next to the config and the .app inside it goes into the config. The archives are
    built here in the layout of an EAS simulator build (the .app at the root of a .tar.gz); no real EAS artifact was available."""
    def archives(self, d):
        import tarfile, zipfile
        src = write_tree({}); simulator_app(src, "MyApp.app", "com.example.eas")
        tar, tgz, zipped = d / "build-1.tar.gz", d / "build-2.tgz", d / "build-3.zip"
        with tarfile.open(tar, "w:gz") as t: t.add(src / "MyApp.app", arcname="MyApp.app")
        shutil.copy(tar, tgz)
        with zipfile.ZipFile(zipped, "w") as z:
            for f in sorted((src / "MyApp.app").rglob("*")): z.write(f, f.relative_to(src))
        return tar, tgz, zipped

    def test_each_archive_kind_is_unpacked_under_the_config_folder_and_the_config_points_into_it(self):
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d, True)
        for archive in self.archives(d):
            with self.subTest(archive=archive.name):
                dest = d / f"cfg-{archive.stem}"
                with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(sf.main(["init", str(archive), "--dir", str(dest)]), 0)
                cfg = tomllib.loads((dest / "shotfleet.toml").read_text())
                self.assertEqual(cfg["ios"]["app"], f".shotfleet/builds/{archive.name.removesuffix('.tar.gz').removesuffix('.tgz').removesuffix('.zip')}/MyApp.app")
                self.assertTrue((dest / cfg["ios"]["app"] / "Info.plist").is_file())
                self.assertTrue(archive.is_file())  # the download is left alone
                self.assertIn("com.example.eas", out.getvalue())

    def test_the_unpacked_app_passes_the_config_reader_as_a_simulator_build(self):
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d, True)
        archive = self.archives(d)[0]
        with contextlib.redirect_stdout(io.StringIO()): sf.cmd_init([str(archive)], d / "cfg")
        with mock.patch.object(sf, "maestro_cmd", return_value="/usr/bin/maestro"):
            platform, cfg, _ = sf.load_config(d / "cfg/shotfleet.toml")
        self.assertEqual((platform, cfg["bundle_id"]), ("ios", "com.example.eas"))


if __name__ == "__main__":
    unittest.main()
