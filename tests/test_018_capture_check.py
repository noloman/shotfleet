"""0.1.8 capture and check fixes (ten items from the WOD, wger and 0.1.7 device runs). Fakes and fixtures only: no simulator, emulator,
Maestro or text recognition.

Run: python3 -m unittest tests.test_018_capture_check
"""
import contextlib, io, json, plistlib, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf
from tests.test_shotfleet import png_c, shots_with_texts

EN = {"nav_bench": "Benchmarks", "nav_train": "Train"}
DE = {"nav_bench": "Referenzwerte", "nav_train": "Training"}


def quiet(fn, *a, **k):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        return fn(*a, **k), out.getvalue()


class ScrollUntilVisibleStringForm(unittest.TestCase):  # item 1
    def tr(self, flow):
        return sf.translate_flow("appId: x\n---\n" + flow, EN, DE)

    def test_the_plain_string_form_of_element_is_translated(self):
        out, missing, _ = self.tr('- scrollUntilVisible:\n    element: "Benchmarks"\n')
        self.assertIn("element: 'Referenzwerte'", out); self.assertEqual(missing, [])

    def test_the_one_line_map_forms_are_translated(self):
        self.assertIn("{ element: 'Referenzwerte' }", self.tr('- scrollUntilVisible: { element: "Benchmarks" }\n')[0])
        out, missing, _ = self.tr('- scrollUntilVisible: { element: { text: "Benchmarks" }, direction: DOWN }\n')
        self.assertIn("text: 'Referenzwerte'", out); self.assertEqual(missing, [])  # the nested form still goes through `text`, once

    def test_the_object_form_and_other_keys_are_unchanged(self):
        out, _, _ = self.tr('- scrollUntilVisible:\n    element:\n      text: "Benchmarks"\n    direction: DOWN\n')
        self.assertIn("text: 'Referenzwerte'", out); self.assertIn("direction: DOWN", out)

    def test_an_untranslatable_element_is_reported_not_swallowed(self):
        self.assertEqual(self.tr('- scrollUntilVisible:\n    element: "Nowhere"\n')[1], ["Nowhere"])


class WaitForAStillScreen(unittest.TestCase):  # item 2
    FLOW = "appId: x\n---\n- launchApp\n- tapOn: 'a'\n- takeScreenshot: 01_home\n- takeScreenshot:\n    path: 02_more\n"

    def test_ios_waits_for_a_still_screen_before_each_screenshot_with_a_cap(self):
        body = sf.localize_flow(self.FLOW, "de", Path("/o"), settle_ms=1000).split("\n---\n")[1].splitlines()
        for shot in ("- takeScreenshot: '/o/01_home'", "- takeScreenshot:"):
            i = body.index(shot)
            self.assertEqual(body[i - 2:i], ["- waitForAnimationToEnd:", "    timeout: 1000"])
        self.assertEqual(sum(l == "- waitForAnimationToEnd:" for l in body), 2)

    def test_android_does_the_same_and_the_hierarchy_marker_still_follows_its_screenshot(self):
        body = sf.android_flow(self.FLOW, "f", Path("/o"), hierarchy=True, settle_ms=700).split("\n---\n")[1].splitlines()
        i = body.index("- takeScreenshot: '/o/01_home'")
        self.assertEqual(body[i - 2:i], ["- waitForAnimationToEnd:", "    timeout: 700"])
        self.assertTrue(body[i + 1].startswith("- assertTrue:"))

    def test_it_can_be_switched_off_and_old_callers_see_no_change(self):
        for text in (sf.localize_flow(self.FLOW, "de", Path("/o")), sf.localize_flow(self.FLOW, "de", Path("/o"), settle_ms=0),
                     sf.android_flow(self.FLOW, "f", Path("/o"))):
            self.assertNotIn("timeout: 1000", text)
        self.assertEqual(sum(l.startswith("- waitForAnimationToEnd") for l in sf.localize_flow(self.FLOW, "de", Path("/o")).splitlines()), 0)

    def test_the_default_is_a_one_second_cap_and_the_setting_is_checked(self):
        self.assertEqual(sf.SETTLE_MS, 1000)  # the worst case is about one second per screenshot
        sf.check_section({"settle_ms": 0}, "ios", "c.toml"); sf.check_section({"settle_ms": 2500}, "android", "c.toml")
        for bad in (-1, 10001, "1000", True):
            with self.assertRaises(sf.Fail, msg=repr(bad)): sf.check_section({"settle_ms": bad}, "ios", "c.toml")

    def test_a_run_writes_it_into_the_flows_and_the_config_value_wins(self):
        for cfg_value, want in ((None, "timeout: 1000"), (0, None), (400, "timeout: 400")):
            with self.subTest(settle_ms=cfg_value):
                flow = self.ios_flow({} if cfg_value is None else {"settle_ms": cfg_value})
                self.assertEqual(want in flow if want else "waitForAnimationToEnd" in flow, bool(want))

    def ios_flow(self, extra):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); (d / "My.app").mkdir(); (d / "flow.yaml").write_text("appId: x\n---\n- launchApp\n- takeScreenshot: 01_home\n")
            cfg = {"app": "My.app", "bundle_id": "com.x", "flow": "flow.yaml", "runtime": "r", "device_type": "iphone", "out": "out", "_inputs": {}, **extra}
            stop = type("Stop", (Exception,), {})
            with mock.patch.object(sf, "load_strings", return_value={"en": EN, "de": DE}), mock.patch.object(sf, "framework_hint"), \
                 mock.patch.object(sf, "make_pool", side_effect=stop), mock.patch.object(sf, "fit_parallel", lambda n: n), \
                 mock.patch.object(sf, "capacity_warn"), mock.patch.object(sf, "device_type_id", lambda t: t):
                with self.assertRaises(stop): quiet(sf.ios_run_inner, cfg, lambda p: d / p, None, None)
            return (d / "out/.work/flows/de.yaml").read_text()


class LocaleCodesPerPlatform(unittest.TestCase):  # item 3
    def test_chinese_by_script_maps_both_ways(self):
        self.assertEqual(sf.match_locales(["zh-Hans"], {"en": {}, "zh-CN": {}})[0], ["zh-CN"])
        self.assertEqual(sf.match_locales(["zh-CN"], {"en": {}, "zh-Hans": {}})[0], ["zh-Hans"])
        self.assertEqual(sf.match_locales(["zh-Hant", "zh-HK"], {"zh-TW": {}, "zh-HK": {}})[0], ["zh-TW", "zh-HK"])

    def test_a_code_the_app_ships_is_never_touched(self):
        self.assertEqual(sf.match_locales(["pt", "pt-BR"], {"pt": {}, "pt-BR": {}, "pt-PT": {}}), (["pt", "pt-BR"], []))

    def test_pt_and_pt_br_map_only_when_the_app_has_no_other_pt(self):
        self.assertEqual(sf.match_locales(["pt"], {"pt-BR": {}, "de": {}})[0], ["pt-BR"])
        self.assertEqual(sf.match_locales(["pt-BR"], {"pt": {}})[0], ["pt"])
        self.assertEqual(sf.match_locales(["PT-br"], {"pt-BR": {}})[0], ["pt-BR"])  # only the case was off

    def test_two_possible_answers_are_not_guessed_the_exact_codes_are_named(self):
        codes, notes = sf.match_locales(["pt"], {"pt-BR": {}, "pt-PT": {}})
        self.assertEqual(codes, ["pt"])  # left alone: run then skips it with the usual message
        self.assertEqual(len(notes), 1); self.assertIn("pt-BR, pt-PT", notes[0]); self.assertIn('locales = ["pt-BR"]', notes[0])

    def test_other_regions_and_scripts_are_never_crossed(self):
        for asked, have in (("de-AT", {"de-DE": {}}), ("de-DE", {"de": {}, "en": {}}), ("pt-PT", {"pt-BR": {}}), ("zh-Hant", {"zh-CN": {}}), ("zh-Hans", {"zh-TW": {}}), ("ja", {"de": {}})):
            with self.subTest(asked=asked): self.assertEqual(sf.match_locales([asked], have), ([asked], []))

    def test_duplicates_after_mapping_collapse(self):
        self.assertEqual(sf.match_locales(["zh-Hans", "zh-CN"], {"zh-CN": {}})[0], ["zh-CN"])

    def test_a_run_says_what_it_did_and_captures_the_code_the_app_ships(self):
        out = self.android_run(["zh-Hans"], {"en": EN, "zh-CN": DE})
        self.assertIn("zh-Hans is zh-CN in this app", out); self.assertNotIn("skip zh-Hans", out)
        out = self.android_run(["pt"], {"en": EN, "pt-BR": DE, "pt-PT": DE})
        self.assertIn("pt could mean pt-BR, pt-PT", out); self.assertIn("skip pt: app has no pt strings", out)

    def android_run(self, locales, strings):
        """What android_run_inner prints before it would start an emulator (the fit_parallel call is where the fake stops it)."""
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); (d / "flow.yaml").write_text("appId: x\n---\n- launchApp\n- tapOn: 'Train'\n")
            cfg = {"apk": "a.apk", "package": "com.x", "flow": "flow.yaml", "locales": locales}
            stop = type("Stop", (Exception,), {})
            out = io.StringIO()
            with mock.patch.object(sf, "framework_hint"), mock.patch.object(sf, "read_maestro_version", lambda: "2.11.0"), \
                 mock.patch.object(sf, "load_strings_apk", return_value=strings), mock.patch.object(sf, "fit_parallel", side_effect=stop), \
                 contextlib.redirect_stdout(out), self.assertRaises((stop, sf.Fail)):
                sf.android_run_inner(cfg, lambda p: d / p, d / "out", None, None)
            return out.getvalue()


class DriverNotReady(unittest.TestCase):  # item 4
    LOG = "Will split 1 flows across 1 shards\n\niOS driver not ready in time, consider increasing timeout by configuring MAESTRO_DRIVER_STARTUP_TIMEOUT env variable\n"

    def test_the_drivers_words_and_the_runs_are_both_device_failures(self):
        self.assertTrue(sf.is_infra_error("iOS driver not ready in time, consider increasing timeout"))
        err = sf.no_result(self.write(self.LOG))
        self.assertTrue(sf.is_infra_error(err)); self.assertIn("did not start in time", err)
        self.assertEqual(sf.retry_choice({"en": {"ok": False, "error": err}}), (["en"], []))  # one retry, not "the flow failed"

    def test_other_logs_keep_the_old_error(self):
        self.assertEqual(sf.no_result(self.write("something else\n")), "no result (see maestro log)")
        self.assertEqual(sf.no_result(Path("/no/such/log")), "no result (see maestro log)")
        self.assertTrue(sf.is_infra_error("no result (see maestro log)"))

    def write(self, text):
        f = Path(tempfile.mkdtemp()) / "maestro1.log"; f.write_text(text); return f


class ReplacedSimulatorKeepsItsName(unittest.TestCase):  # item 5
    def test_a_hung_pool_simulator_is_replaced_under_the_same_name(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict("os.environ", {"SHOTFLEET_HOME": d}):
            old = "OLD-UDID"
            (Path(d) / "hung-simulators").mkdir(); (Path(d) / "hung-simulators" / old).write_text("x")
            listed = {"devices": {"rt": [{"name": "shotfleet-1", "udid": old, "isAvailable": True, "deviceTypeIdentifier": "dt"}]}}
            calls = []
            def simctl(*args, timeout=0):
                calls.append(args)
                return subprocess.CompletedProcess([], 0, json.dumps(listed) if args[0] == "list" else "NEW-UDID\n", "")
            ok = subprocess.CompletedProcess([], 0, "", "")
            with mock.patch.object(sf, "simctl_sh", simctl), mock.patch.object(sf, "sh", return_value=ok), mock.patch.object(sf.Sim, "run"), \
                 mock.patch.object(sf, "run_setup"), mock.patch.object(sf, "OUR_SIMS", set()), contextlib.redirect_stdout(io.StringIO()) as out:
                pool = sf.make_pool(1, "dt", "rt")
            self.assertEqual([(s.name, s.udid) for s in pool], [("shotfleet-1", "NEW-UDID")])  # same name, new id
            self.assertIn(("create", "shotfleet-1", "dt", "rt"), calls)
            self.assertIn("same name", out.getvalue())
            self.assertFalse((Path(d) / "hung-simulators" / old).exists())


def flutter_app(root, with_framework=True):
    app = Path(root) / "Runner.app"; app.mkdir()
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.x", "UIDeviceFamily": [1]}))
    if with_framework:
        fa = app / "Frameworks/App.framework/flutter_assets"; fa.mkdir(parents=True); (fa / "AssetManifest.bin").write_bytes(b"x")
    return app


def fake_read(ocr, png, timeout=120):
    """The text recognition stand-in: what the screenshot's .texts.json holds, as if it had been read from the pixels."""
    text = "\n".join(json.loads(Path(png).with_suffix(".texts.json").read_text()))
    return {"text": text, "chars": len(text), "lang": None, "langs": {}, "ocr": "external"}


def check_fakes(readable=("en", "de")):
    return [mock.patch.object(sf, "read_text", fake_read), mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "warm_up_ocr", return_value=True),
            mock.patch.object(sf, "readable_languages", return_value=set(readable)), mock.patch.object(sf, "tesseract_languages", return_value=frozenset()),
            mock.patch.object(sf, "tesseract_script", return_value={}), mock.patch.object(sf, "store_rules", return_value=([], [])),
            mock.patch.object(sf.shutil, "which", return_value=None)]


class FlutterBuildInCheck(unittest.TestCase):  # item 6
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.app = flutter_app(self.d)
        shots_with_texts(self.d, {"en": {"01_home": ["Benchmarks"]}, "de": {"01_home": ["Referenzwerte"]}})
        l10n = self.d / "l10n"; l10n.mkdir()
        for lp, t in (("en", EN), ("de", DE)): (l10n / f"app_{lp}.arb").write_text(json.dumps({"@@locale": lp, **t}))
        self.arb = str(l10n / "*.arb")

    def run_check(self, **kw):
        with contextlib.ExitStack() as st:
            for f in check_fakes(): st.enter_context(f)
            return quiet(sf.cmd_check, self.d / "shots", report_dir=self.d / "rep", **kw)

    def test_the_message_names_the_option_to_pass(self):
        with self.assertRaises(sf.Fail) as e: self.run_check(app=self.app)
        self.assertIn("This is a Flutter build: pass --strings 'lib/l10n/*.arb'", str(e.exception))
        self.assertIn("contains no translations shotfleet can read", str(e.exception))

    def test_an_ordinary_app_keeps_the_old_message(self):
        other = self.d / "other"; other.mkdir()
        plain = flutter_app(other, with_framework=False)
        with self.assertRaises(sf.Fail) as e: self.run_check(app=plain)
        self.assertIn("no .lproj strings, String Catalogs or resources", str(e.exception)); self.assertNotIn("Flutter", str(e.exception))

    def test_strings_together_with_app_are_used_not_ignored(self):
        code, out = self.run_check(app=self.app, strings_files=[self.arb])
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads((self.d / "rep/check.json").read_text())["problems"], [])


class FlutterApkInCheck(FlutterBuildInCheck):  # item 6, Android: the APK of a Flutter app holds only the libraries' strings (wger: fr, hr, uk "not translated", 0 screenshots checked)
    def setUp(self):
        super().setUp()
        self.apk = self.d / "app-debug.apk"
        import zipfile
        with zipfile.ZipFile(self.apk, "w") as z: z.writestr("assets/flutter_assets/AssetManifest.bin", b"x"); z.writestr("resources.arsc", b"x")
        self.lib = {"en": {"ok": "OK"}, "de": {"ok": "OK"}, "fr": {"ok": "OK"}}  # what load_strings_apk finds in a Flutter APK

    def run_check(self, **kw):
        with mock.patch.object(sf, "load_strings_apk", return_value=self.lib): return super().run_check(**kw)

    def test_the_message_names_the_option_to_pass(self):
        with self.assertRaises(sf.Fail) as e: self.run_check(app=self.apk)
        self.assertIn("This is a Flutter build: pass --strings 'lib/l10n/*.arb'", str(e.exception))

    def test_strings_together_with_the_apk_are_used(self):
        code, out = self.run_check(app=self.apk, strings_files=[self.arb])
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads((self.d / "rep/check.json").read_text())["problems"], [])


REAL_STORE_RULES = sf.store_rules


class ParentOfSeveralDevices(unittest.TestCase):  # item 7
    STRINGS = {"en": {"a": "Next", "b": "Settings"}, "de": {"a": "Weiter", "b": "Einstellungen"}}

    def make(self, devices, families=(1, 2), multi=None):
        d = Path(tempfile.mkdtemp())
        app = d / "My.app"; app.mkdir()
        (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.x", "UIDeviceFamily": list(families)}))
        out = d / "out"
        for name, size in devices.items():
            raw = out / name / "raw" / "de"; raw.mkdir(parents=True)
            (raw / "01_home.png").write_bytes(png_c(*size)); (raw / "01_home.texts.json").write_text(json.dumps(["Weiter", "Einstellungen"]))
            run = {"app": str(app), "platform": "ios", "locales": {"de": {"ok": True}}, **({} if multi is None else {"multi_device": multi})}
            (out / name / "run.json").write_text(json.dumps(run))
        return out

    def check(self, target):
        """check_any with the real App Store size rules and fake text readers."""
        with contextlib.ExitStack() as st:
            for f in check_fakes(): st.enter_context(f)
            st.enter_context(mock.patch.object(sf, "store_rules", REAL_STORE_RULES))
            st.enter_context(mock.patch.object(sf, "load_strings", return_value=self.STRINGS))
            return quiet(sf.check_any, target)

    def test_missing_ipad_is_a_problem_in_the_summary_and_the_exit_code_agrees(self):
        out = self.make({"iphone-17-pro-max": (1320, 2868)})
        code, text = self.check(out)
        self.assertEqual(code, 1, text)
        self.assertNotIn("0 problem(s)", text)
        self.assertIn('the app runs on iPad, so the App Store requires 13" iPad screenshots', text)
        problems = json.loads((out / "iphone-17-pro-max/check.json").read_text())["problems"]
        self.assertTrue(any('requires 13" iPad' in p for p in problems), problems)
        iPad_column = json.loads((out / "iphone-17-pro-max/check.json").read_text())["coverage"]["locales"]["de"]['iPad 13"']["status"]
        self.assertEqual(iPad_column, "missing")  # not "-" (optional)

    def test_an_ipad_set_somewhere_in_the_run_is_fine_and_the_iphone_folder_does_not_need_one(self):
        out = self.make({"iphone-17-pro-max": (1320, 2868), "ipad-pro-13-inch-m5-12gb": (2064, 2752)})
        code, text = self.check(out)
        self.assertEqual(code, 0, text)
        cov = json.loads((out / "iphone-17-pro-max/check.json").read_text())["coverage"]["locales"]["de"]['iPad 13"']["status"]
        self.assertEqual(cov, "optional")

    def test_one_device_of_a_multi_device_run_leaves_the_ipad_set_to_the_whole_run_but_a_single_run_does_not(self):
        multi = self.make({"iphone-17-pro-max": (1320, 2868)}, multi=True)
        self.assertEqual(self.check(multi / "iphone-17-pro-max")[0], 0)
        single = self.make({"iphone-17-pro-max": (1320, 2868)}, multi=False)
        code, text = self.check(single / "iphone-17-pro-max")
        self.assertEqual(code, 1, text); self.assertIn('requires 13" iPad screenshots', text)  # a one-device run has to cover the iPad too

    def test_run_json_of_a_multi_device_run_says_so(self):
        self.assertIn('report["multi_device"] = bool(cfg.get("multi_device"))', (ROOT / "shotfleet.py").read_text())


class ExpectByStringKey(unittest.TestCase):  # item 8
    STRINGS = {"en": {"nav_bench": "Benchmarks", "nav_train": "Train", "t_round": "Round %d"},
               "de": {"nav_bench": "Referenzwerte", "nav_train": "Training", "t_round": "Runde %d"}}

    def check(self, expect, spec, strings=STRINGS):
        d = tempfile.mkdtemp(); shots_with_texts(d, spec)
        with contextlib.ExitStack() as st:
            for f in check_fakes(): st.enter_context(f)
            st.enter_context(mock.patch.object(sf, "store_rules", return_value=([], [])))
            code, _ = quiet(sf.cmd_check, Path(d) / "shots", strings=strings, report_dir=Path(d) / "rep", expect=expect)
        return code, json.loads((Path(d) / "rep/check.json").read_text())

    GOOD = {"en": {"02_benchmarks": ["Benchmarks", "Train"]}, "de": {"02_benchmarks": ["Referenzwerte", "Training"]}}
    WRONG_SCREEN = {"en": {"02_benchmarks": ["Benchmarks", "Train"]}, "de": {"02_benchmarks": ["Training", "Letzte Woche"]}}  # Train instead of Benchmarks

    def test_the_right_screen_passes_in_every_language(self):
        code, report = self.check({"02_benchmarks": {"key": "nav_bench"}}, self.GOOD)
        self.assertEqual((code, report["problems"]), (0, []))

    def test_the_wrong_screen_in_one_language_is_a_problem_naming_the_text(self):
        code, report = self.check({"02_benchmarks": {"key": "nav_bench"}}, self.WRONG_SCREEN)
        self.assertEqual(code, 1)
        self.assertEqual(report["problems"], ['de/02_benchmarks.png: expected "Referenzwerte" on screen'])

    def test_a_list_of_keys_and_a_per_language_table_work_next_to_all_any_not(self):
        expect = {"02_benchmarks": {"key": ["nav_bench"], "not": ["Fehler"], "de": {"key": "nav_train"}}}
        self.assertEqual(self.check(expect, self.GOOD)[1]["problems"], [])

    def test_a_wrong_key_or_no_strings_is_said_plainly(self):
        problems = self.check({"02_benchmarks": {"key": "nav_bnech"}}, self.GOOD)[1]["problems"]
        self.assertIn('en/02_benchmarks.png: key "nav_bnech": the app has no string with that key', problems)
        problems = self.check({"02_benchmarks": {"key": "nav_bench"}}, {"en": {"02_benchmarks": ["Benchmarks"]}}, strings=None)[1]["problems"]
        self.assertTrue(any("needs the app's strings: pass --app or --strings" in p for p in problems), problems)
        problems = self.check({"02_benchmarks": {"key": "t_round"}}, self.GOOD)[1]["problems"]
        self.assertTrue(all("has a placeholder" in p for p in problems) and problems, problems)

    def test_it_is_off_unless_the_config_asks_for_it(self):
        self.assertEqual(self.check(None, self.WRONG_SCREEN)[1]["problems"], [])
        self.assertEqual(self.check({}, self.WRONG_SCREEN)[0], 0)

    def test_the_config_accepts_key_and_refuses_nonsense_with_the_fix(self):
        sf.check_expect({"s": {"key": "title"}}, "c.toml"); sf.check_expect({"s": {"key": ["a", "b"], "de": {"key": "c"}}}, "c.toml")
        for bad in ({"key": 3}, {"key": []}, {"key": ""}):
            with self.assertRaises(sf.Fail, msg=repr(bad)) as e: sf.check_expect({"s": bad}, "c.toml")
            self.assertIn('key = "benchmarks_title"', str(e.exception))
        with self.assertRaises(sf.Fail) as e: sf.check_expect({"s": {"keys": ["a"]}}, "c.toml")
        self.assertIn("did you mean 'key'", str(e.exception))

    def test_a_config_file_with_key_is_read_by_check_content(self):
        cfg = Path(tempfile.mkdtemp()) / "shotfleet.toml"
        cfg.write_text('[ios]\napp = "a.app"\n[expect.02_benchmarks]\nkey = "nav_bench"\n')
        self.assertEqual(sf.read_expect(cfg), {"02_benchmarks": {"key": "nav_bench"}})


class DoctorSaysWhichRuntimeRunUses(unittest.TestCase):  # item 9
    def doctor(self, names, config_text=None):
        d = Path(tempfile.mkdtemp())
        cfg = d / "shotfleet.toml"
        if config_text: cfg.write_text(config_text)
        out = io.StringIO()
        ok = lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, "Ready\n" if "--warmup" in cmd else '{"runtimes": []}', "")
        with mock.patch.object(sf, "SDK", d / "sdk"), mock.patch.object(sf, "BREW", d / "brew"), mock.patch.object(sf.Path, "home", return_value=d / "home"), \
                mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "SYSTEM_SDKS", ()), \
                mock.patch.object(sf.shutil, "which", lambda c, **k: f"/usr/bin/{c}" if c in ("xcrun", "swiftc") else None), \
                mock.patch.object(sf, "find_java", return_value=(True, None)), mock.patch.object(sf, "java_env", return_value={}), \
                mock.patch.object(sf, "sh", ok), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "latest_release", lambda: None), \
                mock.patch.object(sf, "ios_runtimes", lambda: names), mock.patch.object(sf, "maestro_cmd", lambda: "/m"), \
                mock.patch.object(sf, "read_maestro_version", return_value="2.11.0"), contextlib.redirect_stdout(out):
            sf.cmd_doctor(config=str(cfg))
        return out.getvalue()

    def test_with_26_4_and_27_0_it_says_26_4_and_why(self):
        for names in (["iOS 26.4", "iOS 27.0"], ["iOS 27.0", "iOS 26.4"]):
            out = self.doctor(names)
            self.assertRegex(out, r"ok\s+iOS Simulator runtime iOS 26\.4"); self.assertNotRegex(out, r"ok\s+iOS Simulator runtime iOS 27\.0")
            self.assertIn("`run` will be using iOS 26.4", out); self.assertIn("iOS 27.0 is installed", out); self.assertIn("freeze at boot", out)
            self.assertIn('runtime = "com.apple.CoreSimulator.SimRuntime.iOS-27-0"', out)  # how to use it anyway

    def test_nothing_extra_when_there_is_nothing_to_explain(self):
        out = self.doctor(["iOS 26.4"])
        self.assertRegex(out, r"ok\s+iOS Simulator runtime iOS 26\.4"); self.assertNotIn("`run` will be", out)

    def test_a_runtime_in_the_config_is_what_run_uses(self):
        out = self.doctor(["iOS 26.4", "iOS 27.0"], '[ios]\napp = "a.app"\nruntime = "com.apple.CoreSimulator.SimRuntime.iOS-27-0"\n')
        self.assertRegex(out, r"ok\s+iOS Simulator runtime iOS 27\.0"); self.assertIn("sets runtime", out)


class AndroidWithoutAHierarchy(unittest.TestCase):  # item 10
    def test_the_note_says_ocr_why_and_what_to_do(self):
        note = sf.no_hierarchy_note("2.0.10")
        for word in ("Maestro 2.0.10", "2.7.0", "(OCR)", "Maestro 2.11.0", "get.maestro.mobile.dev"): self.assertIn(word, note)
        self.assertIn("(version unreadable)", sf.no_hierarchy_note(None))

    def test_the_run_prints_it_at_the_start_and_again_with_the_result(self):
        src = (ROOT / "shotfleet.py").read_text()
        self.assertEqual(src.count('if not hier: print("note: " + no_hierarchy_note(version))'), 2)


if __name__ == "__main__":
    unittest.main()
