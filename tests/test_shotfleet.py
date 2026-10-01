"""Tests for shotfleet's logic. No simulators, emulators or Maestro needed.

Run: python3 -m unittest discover -s tests
"""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

EN = {"next": "Next", "common_next": "Next", "advanced": "Advanced", "start": "Start Training",
      "goals": "3+ years of training", "settings": "Settings"}
DE = {"next": "Weiter", "common_next": "Nächste", "advanced": "Fortgeschritten", "start": "Training starten",
      "goals": "3+ Jahre Training", "settings": "Einstellungen"}
TR = {"next": "İleri", "common_next": "İleri", "advanced": "İleri", "start": "Antrenmana başla",
      "goals": "3+ yıl antrenman", "settings": "Ayarlar"}


class TranslateFlow(unittest.TestCase):
    def test_single_translation_is_quoted_literal(self):
        out, missing, _ = sf.translate_flow('appId: x\n---\n- tapOn: "Start Training"\n', EN, DE)
        self.assertIn("- tapOn: 'Training starten'", out)
        self.assertEqual(missing, [])

    def test_label_with_two_keys_matches_either_translation(self):
        out, _, _ = sf.translate_flow('- tapOn: "Next"\n', EN, DE)
        self.assertIn("- tapOn: '(Nächste|Weiter)'", out)

    def test_regex_metacharacters_are_escaped_even_in_english(self):
        out, _, _ = sf.translate_flow('- assertVisible: "3+ years of training"\n', EN, EN)
        self.assertIn(r"'3\+ years of training'", out)

    def test_unknown_selector_is_reported_and_left_alone(self):
        out, missing, _ = sf.translate_flow('- tapOn: "Benchmark WODs"\n', EN, DE)
        self.assertIn('- tapOn: "Benchmark WODs"', out)
        self.assertEqual(missing, ["Benchmark WODs"])

    def test_map_form_text_is_translated_and_id_selectors_pass_through(self):
        flow = '- tapOn:\n    text: "Settings"\n    optional: true\n- tapOn:\n    id: "settings_button"\n'
        out, missing, _ = sf.translate_flow(flow, EN, DE)
        self.assertIn("    text: 'Einstellungen'", out)
        self.assertIn('    id: "settings_button"', out)
        self.assertEqual(missing, [])

    def test_untranslated_key_falls_back_to_english(self):
        out, _, _ = sf.translate_flow('- tapOn: "Settings"\n', EN, {})
        self.assertIn('- tapOn: "Settings"', out)

    def test_turkish_next_advanced_collision_is_warned(self):
        _, _, clash = sf.translate_flow('- tapOn: "Next"\n', EN, TR)
        self.assertTrue(any("'Next' -> 'İleri' also means 'Advanced'" in c for c in clash), clash)

    def test_no_collision_warning_when_words_differ(self):
        _, _, clash = sf.translate_flow('- tapOn: "Next"\n', EN, DE)
        self.assertEqual(clash, [])

    def test_several_targets_match_any_of_their_translations(self):
        out, _, _ = sf.translate_flow('- tapOn: "Start Training"\n', EN, [DE, TR])
        self.assertIn("- tapOn: '(Antrenmana başla|Training starten)'", out)


class LocalizeFlow(unittest.TestCase):
    FLOW = 'appId: x\nname: "Old name"\n---\n- tapOn: "Next"\n- launchApp\n- takeScreenshot: 01_home\n'

    def test_language_travels_as_launch_arguments_with_fresh_state_first(self):
        out = sf.localize_flow(self.FLOW, "de", Path("/out/raw/de"))
        head, body = out.split("\n---\n")
        self.assertIn("name: de", head)
        self.assertNotIn("Old name", head)
        first = body.split("\n- ")[0]
        self.assertIn("clearState: true", first)
        self.assertIn('AppleLanguages: "(de)"', first)
        self.assertIn('AppleLocale: "de_DE"', first)

    def test_later_launch_app_keeps_state_but_gets_language(self):
        body = sf.localize_flow(self.FLOW, "ja", Path("/o")).split("\n---\n")[1]
        launches = body.split("- launchApp:")
        self.assertEqual(len(launches), 3)  # injected first launch + the flow's own
        self.assertNotIn("clearState", launches[2])
        self.assertIn('AppleLanguages: "(ja)"', launches[2])

    def test_screenshots_go_to_the_locale_folder(self):
        out = sf.localize_flow(self.FLOW, "de", Path("/out/raw/de"))
        self.assertIn("- takeScreenshot: '/out/raw/de/01_home'", out)

    def test_launch_app_with_options_is_rejected_clearly(self):
        with self.assertRaisesRegex(ValueError, "launchApp with options"):
            sf.localize_flow("appId: x\n---\n- launchApp:\n    clearState: true\n", "de", Path("/o"))

    def test_flow_without_header_is_rejected_clearly(self):
        with self.assertRaisesRegex(ValueError, "appId"):
            sf.localize_flow("- tapOn: x\n", "de", Path("/o"))


class AndroidFlow(unittest.TestCase):
    def test_adds_launch_strips_clear_state_and_moves_screenshots(self):
        flow = "appId: x\n---\n- tapOn:\n    text: 'Weiter'\n    clearState: true\n- takeScreenshot: 01_home\n"
        out = sf.android_flow(flow, "r1_f0", Path("/out/tmp/r1/f0"))
        head, body = out.split("\n---\n")
        self.assertIn("name: r1_f0", head)
        self.assertTrue(body.startswith("- launchApp"))
        self.assertNotIn("clearState", body)
        self.assertIn("- takeScreenshot: '/out/tmp/r1/f0/01_home'", body)

    def test_keeps_an_existing_first_launch(self):
        out = sf.android_flow("appId: x\n---\n- launchApp\n- tapOn: 'a'\n", "f", Path("/o"))
        self.assertEqual(out.count("- launchApp"), 1)


class Locales(unittest.TestCase):
    def test_android_qualifiers(self):
        cases = {"de": "de", "pt-rBR": "pt-BR", "b+zh+Hans": "zh-Hans", "b+sr+Latn": "sr-Latn",
                 "night": None, "de-v31": None, "land": None, "xhdpi": None}
        for q, want in cases.items():
            self.assertEqual(sf.android_locale(q), want, q)

    def test_shipped_locales_drop_library_only_translations(self):
        strings = {"en": {str(i): "x" for i in range(100)}, "de": {str(i): "y" for i in range(98)},
                   "zu": {str(i): "z" for i in range(11)}}
        self.assertEqual(sf.shipped_locales(strings), ["de", "en"])

    def test_english_only_app_with_library_translations_ships_only_english(self):
        # 240 app strings, 150 library strings translated into 80 locales (like Now in Android)
        lib = {f"lib_{i}": "x" for i in range(150)}
        strings = {"en": {**{f"app_{i}": "y" for i in range(240)}, **lib}}
        strings.update({f"l{n}": dict(lib) for n in range(80)})
        self.assertEqual(sf.shipped_locales(strings), ["en"])

    def test_app_translated_everywhere_keeps_all_its_languages(self):
        keys = {f"k{i}": "x" for i in range(50)}
        strings = {"en": dict(keys), **{f"l{n}": dict(keys) for n in range(30)}}
        self.assertEqual(len(sf.shipped_locales(strings)), 31)

    def test_every_store_listing_code_maps_to_itself(self):
        for store in (sf.APP_STORE, sf.PLAY):
            self.assertEqual([c for c in store if sf.store_code(c, store) != c], [])

    def test_app_locales_map_to_the_right_listing(self):
        apple = {"en": "en-US", "de": "de-DE", "de-AT": "de-DE", "nb": "no", "nn": "no", "iw": "he", "in": "id",
                 "pt": "pt-BR", "pt-PT": "pt-PT", "zh": "zh-Hans", "zh-CN": "zh-Hans", "zh-HK": "zh-Hant",
                 "zh-Hant-HK": "zh-Hant", "zh-Hant": "zh-Hant", "es-419": "es-MX", "es-MX": "es-MX", "es": "es-ES",
                 "ar": "ar-SA", "ur": "ur-PK", "sl": "sl-SI", "ta": "ta-IN", "en_GB": "en-GB", "German": "de-DE",
                 "fil": None, "sr": None, "eo": None}
        play = {"en": "en-US", "en-IN": "en-IN", "iw": "iw-IL", "he": "iw-IL", "nb": "no-NO", "in": "id", "tl": "fil",
                "zh-Hans": "zh-CN", "zh-Hant": "zh-TW", "zh-HK": "zh-HK", "es-MX": "es-419", "es-US": "es-US",
                "pt": "pt-BR", "sr-Latn": "sr", "hy": "hy-AM", "fa": "fa", "ms": "ms", "eo": None}
        for store, cases in ((sf.APP_STORE, apple), (sf.PLAY, play)):
            for app, want in cases.items():
                self.assertEqual(sf.store_code(app, store), want, app)


class LoadStrings(unittest.TestCase):
    def test_reads_every_table_and_skips_base(self):
        with tempfile.TemporaryDirectory() as d:
            for lp, rows in {"en": '"a" = "Next";', "de": '"a" = "Weiter";', "Base": '"a" = "Next";'}.items():
                (Path(d) / f"{lp}.lproj").mkdir()
                (Path(d) / f"{lp}.lproj" / "Localizable.strings").write_text(rows)
            (Path(d) / "de.lproj" / "InfoPlist.strings").write_text('"CFBundleName" = "App";')
            got = sf.load_strings(Path(d))
        self.assertEqual(sorted(got), ["de", "en"])
        self.assertEqual(got["de"], {"a": "Weiter", "CFBundleName": "App"})

    def test_parses_aapt2_dump(self):
        dump = """Package name=com.example id=7f
  type string id=10 entryCount=3
    resource 0x7f100001 string/next
      () "Next"
      (de) "Weiter"
      (pt-rBR) "Pr\\u00f3ximo"
      (night) "ignored"
    resource 0x7f100002 string/quote
      () "Say \\"hi\\""
      (b+zh+Hans) "下一步"
  type plurals id=11 entryCount=1
    resource 0x7f110001 plurals/items
      () <plural>
"""
        fake = subprocess.CompletedProcess([], 0, dump, "")
        with mock.patch.object(sf, "sh", return_value=fake), mock.patch.object(sf, "aapt2", return_value="aapt2"):
            got = sf.load_strings_apk("app.apk")
        self.assertEqual(got["en"], {"next": "Next", "quote": 'Say "hi"'})
        self.assertEqual(got["de"], {"next": "Weiter"})
        self.assertIn("pt-BR", got)
        self.assertEqual(got["zh-Hans"], {"quote": "下一步"})
        self.assertNotIn("night", got)


class MaestroOutput(unittest.TestCase):
    def test_flow_to_device_map_from_shard_log(self):
        log = ("09:01 [ INFO] runShardSuite: [shard 1] Selected device emulator-5702 using port 7109 with execution plan "
               "ExecutionPlan(flowsToRun=[/o/flows/r1/r1_f1.yaml, /o/flows/r1/r1_f3.yaml], sequence=x)\n"
               "09:01 [ INFO] runShardSuite: [shard 2] Selected device emulator-5704 using port 7006 with execution plan "
               "ExecutionPlan(flowsToRun=[/o/flows/r1/r1_f0.yaml], sequence=x)\n")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a" / "b").mkdir(parents=True)
            (Path(d) / "a" / "b" / "maestro.log").write_text(log)
            got = sf.flow_devices(d)
        self.assertEqual(got, {"r1_f1": "emulator-5702", "r1_f3": "emulator-5702", "r1_f0": "emulator-5704"})

    def test_junit_results(self):
        xml = """<testsuites><testsuite>
          <testcase name="de" time="61.2"/>
          <testcase name="tr" time="80"><failure message="Assertion is false: X is visible"/></testcase>
        </testsuite></testsuites>"""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "j.xml"; p.write_text(xml)
            got = sf.junit_results(p)
            self.assertEqual(sf.junit_results(Path(d) / "missing.xml"), {})
        self.assertEqual(got["de"], {"ok": True, "seconds": 61, "error": None})
        self.assertFalse(got["tr"]["ok"])
        self.assertIn("Assertion is false", got["tr"]["error"])


class JudgeScreen(unittest.TestCase):
    TABLES = sf.string_tables({k: {v: v for v in vals} for k, vals in {"de": {"Weiter", "Einstellungen", "Training starten"},
              "en": {"Next", "Settings", "Start Training"},
              "ja": {"次へ", "設定"}}.items()})

    def test_screen_in_the_right_language_passes(self):
        self.assertEqual(sf.judge_screen("de", {"chars": 40, "text": "9:41\nEinstellungen\nWeiter"}, self.TABLES), ("de", None))

    def test_screen_showing_another_locales_strings_fails(self):
        got, problem = sf.judge_screen("de", {"chars": 40, "text": "Settings\nNext\nStart Training"}, self.TABLES)
        self.assertEqual(got, "en")
        self.assertIn("shows en strings", problem)

    def test_shared_words_count_for_the_expected_locale(self):
        tables = sf.string_tables({"de": {"a": "Training", "b": "Log"}, "en": {"a": "Training", "b": "Log"}})
        self.assertEqual(sf.judge_screen("de", {"chars": 10, "text": "Training\nLog"}, tables), ("de", None))

    def test_blank_screen_fails(self):
        self.assertIn("no text", sf.judge_screen("de", {"chars": 0, "text": ""}, self.TABLES)[1])

    def test_falls_back_to_language_detection_when_no_string_matches(self):
        ok = sf.judge_screen("ja", {"chars": 30, "text": "ようこそ", "lang": "ja"}, self.TABLES)
        bad = sf.judge_screen("ja", {"chars": 30, "text": "Welcome", "lang": "en", "langs": {"en": 0.9}}, self.TABLES)
        self.assertEqual(ok, ("ja", None))
        self.assertIn("expected 'ja'", bad[1])


class Export(unittest.TestCase):
    def _out(self, d, platform, problems):
        out = Path(d) / "out"
        for lp in ("de", "ja", "tr"):
            (out / "raw" / lp).mkdir(parents=True)
            (out / "raw" / lp / "01_home.png").write_bytes(b"png-" + lp.encode())
        (out / "run.json").write_text(json.dumps({"platform": platform}))
        (out / "check.json").write_text(json.dumps({"problems": problems}))
        return out

    def test_ios_export_skips_failed_locales_and_replaces_old_sets(self):
        with tempfile.TemporaryDirectory() as d:
            out = self._out(d, "ios", ["tr/01_home.png: shows en strings (3 lines) more than tr (0)"])
            fl = Path(d) / "fastlane"
            (fl / "screenshots" / "de-DE").mkdir(parents=True)
            (fl / "screenshots" / "de-DE" / "old.png").write_bytes(b"old")
            code = sf.cmd_export(out, fl)
            self.assertEqual(code, 1)  # something was skipped
            self.assertEqual(sorted(p.name for p in (fl / "screenshots").iterdir()), ["de-DE", "ja"])
            self.assertEqual([p.name for p in (fl / "screenshots" / "de-DE").iterdir()], ["01_home.png"])

    def test_android_export_uses_play_folders(self):
        with tempfile.TemporaryDirectory() as d:
            out = self._out(d, "android", [])
            fl = Path(d) / "fastlane"
            self.assertEqual(sf.cmd_export(out, fl), 0)
            self.assertTrue((fl / "metadata/android/ja-JP/images/phoneScreenshots/01_home.png").exists())
            self.assertTrue((fl / "metadata/android/tr-TR/images/phoneScreenshots/01_home.png").exists())

    def test_identical_images_skip_both_locales(self):
        with tempfile.TemporaryDirectory() as d:
            out = self._out(d, "ios", ["identical image in 2 languages: de/01_home.png, ja/01_home.png"])
            fl = Path(d) / "fastlane"
            sf.cmd_export(out, fl)
            self.assertEqual(sorted(p.name for p in (fl / "screenshots").iterdir()), ["tr"])

    def test_existing_spellings_and_same_language_listings_are_kept_up_to_date(self):
        with tempfile.TemporaryDirectory() as d:
            out = self._out(d, "android", [])
            for lp in ("nb", "es"):
                (out / "raw" / lp).mkdir(); (out / "raw" / lp / "01_home.png").write_bytes(lp.encode())
            fl = Path(d) / "fastlane"; root = fl / "metadata/android"
            for folder in ("nb-NO", "es-419", "zh-TW"):
                (root / folder / "images/phoneScreenshots").mkdir(parents=True)
                (root / folder / "images/phoneScreenshots/old.png").write_bytes(b"old")
            sf.cmd_export(out, fl)
            shot = lambda f: [p.read_bytes() for p in (root / f / "images/phoneScreenshots").iterdir()]
            self.assertEqual(shot("nb-NO"), [b"nb"])  # your spelling, not a second no-NO folder
            self.assertFalse((root / "no-NO").exists())
            self.assertEqual(shot("es-419"), [b"es"])  # same language, no more specific translation
            self.assertEqual(shot("zh-TW"), [b"old"])  # language the app doesn't have: left alone

    def test_languages_without_a_store_listing_are_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            out = self._out(d, "ios", [])
            (out / "raw" / "eo").mkdir(); (out / "raw" / "eo" / "01_home.png").write_bytes(b"eo")
            fl = Path(d) / "fastlane"
            sf.cmd_export(out, fl)
            self.assertEqual(sorted(p.name for p in (fl / "screenshots").iterdir()), ["de-DE", "ja", "tr"])


class ReviewFixes(unittest.TestCase):
    def test_map_form_screenshots_are_redirected_on_both_platforms(self):
        flow = "appId: x\n---\n- takeScreenshot:\n    path: 01_home\n- takeScreenshot: 02_log\n"
        ios = sf.localize_flow(flow, "de", Path("/o/raw/de"))
        android = sf.android_flow(flow, "f", Path("/o/tmp/f"))
        for out, d in ((ios, "/o/raw/de"), (android, "/o/tmp/f")):
            self.assertIn(f"    path: '{d}/01_home'", out)
            self.assertIn(f"- takeScreenshot: '{d}/02_log'", out)
        self.assertEqual(sf.count_screenshots(flow), 2)

    def test_driver_cleanup_only_touches_our_simulators(self):
        killed = []
        def fake_sh(cmd, **kw):
            if cmd[0] == "pgrep": return subprocess.CompletedProcess(cmd, 0, "11\n22\n", "")
            if cmd[0] == "ps":
                args = {"11": "xcodebuild test-without-building -xctestrun /t/maestro.xctestrun -destination id=OURS",
                        "22": "xcodebuild test-without-building -xctestrun /t/maestro.xctestrun -destination id=SOMEONE_ELSE"}
                return subprocess.CompletedProcess(cmd, 0, args[cmd[-1]], "")
            if cmd[0] == "kill": killed.append(cmd[-1])
            return subprocess.CompletedProcess(cmd, 0, "", "")
        with mock.patch.object(sf, "sh", side_effect=fake_sh), mock.patch.object(sf, "OUR_SIMS", {"OURS"}):
            sf.kill_stale_drivers()
        self.assertEqual(killed, ["11"])

    def test_no_simulators_of_ours_means_nothing_is_killed(self):
        with mock.patch.object(sf, "sh") as fake, mock.patch.object(sf, "OUR_SIMS", set()):
            sf.kill_stale_drivers()
        fake.assert_not_called()

    def test_missing_aapt2_is_a_friendly_failure(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "SDK", Path(d)):
            with self.assertRaisesRegex(sf.Fail, "aapt2 not found"):
                sf.load_strings_apk("app.apk")
            with self.assertRaisesRegex(sf.Fail, "aapt2 not found"):
                sf.cmd_init(str(Path(d) / "app.apk"), d) if (Path(d) / "app.apk").write_bytes(b"x") else None


class Config(unittest.TestCase):
    def _cfg(self, d, text):
        p = Path(d) / "shotfleet.toml"; p.write_text(text); return p

    def test_mistakes_are_reported_as_one_line_with_the_fix(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "flow.yaml").write_text("appId: x\n---\n")
            cases = [
                (None, "no config at"),
                ("not = [valid", "isn't valid TOML"),
                ("[ios]\n[android]\n", "exactly one [ios] or [android]"),
                ('[ios]\napp = "x.app"\n', "missing: bundle_id, flow"),
                ('[ios]\napp = "nope.app"\nbundle_id = "a"\nflow = "flow.yaml"\n', "no simulator app at"),
                ('[ios]\napp = "nope.app"\nbundle_id = "a"\nflow = "missing.yaml"\n', "flow file not found"),
                ('[android]\napk = "nope.apk"\npackage = "a"\nflow = "flow.yaml"\n', "no APK at"),
            ]
            for text, msg in cases:
                path = Path(d) / "absent.toml" if text is None else self._cfg(d, text)
                with self.subTest(msg=msg), self.assertRaisesRegex(sf.Fail, msg.replace("[", r"\[").replace("]", r"\]")):
                    sf.load_config(path)

    def test_cli_exits_2_with_a_message_instead_of_a_traceback(self):
        r = subprocess.run([sys.executable, str(Path(sf.__file__)), "run", "/nonexistent/shotfleet.toml"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("shotfleet: no config at", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class CheckAnyFolder(unittest.TestCase):
    def layout(self, paths):
        root = Path(tempfile.mkdtemp())
        for rel in paths:
            (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_bytes(b"png")
        return {k: [p.name for p in v] for k, v in sf.find_screenshots(root).items()}

    def test_finds_fastlane_ios_android_and_plain_folders(self):
        self.assertEqual(self.layout(["screenshots/de-DE/1.png", "screenshots/ja/1.png", "Snapfile"]),
                         {"de-DE": ["1.png"], "ja": ["1.png"]})
        self.assertEqual(self.layout(["metadata/android/pt-BR/images/phoneScreenshots/1.png",
                                      "metadata/android/pt-BR/images/icon.png"]), {"pt-BR": ["1.png"]})
        self.assertEqual(self.layout(["fr/a.png", "fr/b.png"]), {"fr": ["a.png", "b.png"]})
        self.assertEqual(self.layout(["raw/ko/a.png", "index.html"]), {"ko": ["a.png"]})

    def test_store_codes_map_to_app_languages(self):
        app = {"en", "de", "nb", "pt", "pt-PT", "zh-Hans", "in", "iw", "es"}
        cases = {"de-DE": "de", "no": "nb", "no-NO": "nb", "pt-BR": "pt", "pt-PT": "pt-PT", "en-US": "en",
                 "zh-CN": "zh-Hans", "zh-Hans": "zh-Hans", "id": "in", "iw-IL": "iw", "he": "iw", "es-ES": "es",
                 "zh-Hant": None, "zh-TW": None, "fr-FR": None}
        for store, want in cases.items():
            self.assertEqual(sf.app_locale(store, app), want, store)

    def test_script_rescues_cjk_screens_detection_misreads(self):
        ocr = {"chars": 80, "text": "EMOM AMRAP\nTabataタイマー\n9:41\nワーク", "lang": "hr", "langs": {"hr": 0.2}}
        self.assertEqual(sf.judge_screen("ja", ocr, {"en": {"Start"}}), ("ja", None))
        ocr = {"chars": 80, "text": "Timer\nRounds\nWork", "lang": "en", "langs": {"en": 0.9}}
        self.assertIsNotNone(sf.judge_screen("ja", ocr, {"en": {"Start"}})[1])

    def test_one_shared_label_is_not_evidence_of_wrong_language(self):  # "Training starten" is German and Dutch
        tables = sf.string_tables({"de": {"s": "Training starten"}, "nl": {"b": "Begin"}})
        ocr = {"chars": 21, "text": "9:41\nTraining starten", "lang": "nl", "langs": {"nl": 0.6}}
        self.assertEqual(sf.judge_screen("nl", ocr, tables), ("nl", None))
    def test_json_mode_keeps_stdout_machine_readable(self):
        r = subprocess.run([sys.executable, str(Path(sf.__file__)), "check", "/no/such/folder", "--json"],
                           capture_output=True, text=True)
        self.assertEqual((r.returncode, json.loads(r.stdout)), (2, {"exit": 2}))
        self.assertIn("no folder", r.stderr)


class LocalizationFormats(unittest.TestCase):
    def test_compose_multiplatform_resources(self):
        import base64
        b = lambda t: base64.b64encode(t.encode()).decode()
        out = {}
        sf.add_cvr(out, "assets/composeResources/app.generated.resources/values-pt-rBR/strings.commonMain.cvr",
                   f"version:0\nstring|next|{b('Próximo')}\nplurals|items|xyz\n", "en")
        sf.add_cvr(out, "composeResources/app.generated.resources/values/strings.commonMain.cvr", f"string|next|{b('Next')}", "en")
        sf.add_cvr(out, "composeResources/app.generated.resources/values-night/strings.cvr", f"string|x|{b('y')}", "en")
        self.assertEqual(out, {"pt-BR": {"cmp:next": "Próximo"}, "en": {"cmp:next": "Next"}})

    def test_strings_in_bundles_frameworks_and_watch_apps(self):
        with tempfile.TemporaryDirectory() as d:
            app = Path(d) / "My.app"
            for rel, body in [("de.lproj/Localizable.strings", '"next" = "Weiter";'),
                              ("Feature_Feature.bundle/de.lproj/Localizable.strings", '"next" = "Nächste";'),
                              ("Watch/W.app/de.lproj/Localizable.strings", '"start" = "Training starten";'),
                              ("German.lproj/Main.strings", '"title" = "Titel";'),
                              ("Base.lproj/Main.strings", '"title" = "Title";')]:
                (app / rel).parent.mkdir(parents=True, exist_ok=True); (app / rel).write_text(body)
            self.assertEqual(sf.load_strings(app), {"de": {
                "next": "Weiter", "title": "Titel", "Feature_Feature.bundle/Localizable:next": "Nächste",
                "Watch/W.app/Localizable:start": "Training starten"}})

    def test_pseudolocales_and_ui_modes_are_not_languages(self):
        for q in ("en-rXA", "ar-rXB", "en-rXC", "car", "night", "v31", "ldrtl"):
            self.assertIsNone(sf.android_locale(q), q)
        self.assertEqual([sf.android_locale(q) for q in ("b+sr+Latn", "b+es+419", "in", "iw", "fil", "zh-rTW")],
                         ["sr-Latn", "es-419", "in", "iw", "fil", "zh-TW"])


def png(w, h):  # just enough of a PNG for png_size
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big")


class AuditFixes(unittest.TestCase):
    def test_inline_maps_relative_anchors_and_comments_are_translated(self):
        flow = ("appId: x\n---\n- tapOn: { text: \"Next\", optional: true }\n- tapOn:\n    text: Next\n"
                "    below: \"Settings\"\n- tapOn: \"Next\" # the big button\n")
        out, missing, _ = sf.translate_flow(flow, {"n": "Next", "s": "Settings"}, {"n": "Weiter", "s": "Einstellungen"})
        self.assertIn("{ text: 'Weiter', optional: true }", out)
        self.assertIn("below: 'Einstellungen'", out)
        self.assertIn("- tapOn: 'Weiter' # the big button", out)
        self.assertEqual(missing, [])

    def test_shared_script_is_not_proof_of_language(self):  # Russian in the Ukrainian folder
        ocr = {"chars": 60, "text": "Настройки\nДалее\nГотово", "lang": "ru", "langs": {"ru": 0.95}}
        self.assertIsNotNone(sf.judge_screen("uk", ocr, {})[1])

    def test_export_never_wipes_a_listing_with_a_failed_or_empty_capture(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            for lp in ("de", "ja"): (out / "raw" / lp).mkdir(parents=True)
            (out / "raw/de/01.png").write_bytes(png(1320, 2868))
            (out / "run.json").write_text(json.dumps({"platform": "ios", "locales": {"de": {"ok": False}, "ja": {"ok": True}}}))
            (out / "check.json").write_text(json.dumps({"problems": []}))
            fl = Path(d) / "fl"
            for lp in ("de-DE", "ja"): (fl / "screenshots" / lp).mkdir(parents=True); (fl / "screenshots" / lp / "old.png").write_bytes(png(1320, 2868))
            self.assertEqual(sf.cmd_export(out, fl), 1)
            self.assertTrue((fl / "screenshots/de-DE/old.png").exists())
            self.assertTrue((fl / "screenshots/ja/old.png").exists())

    def test_export_replaces_only_the_same_device_size(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"; (out / "raw/de").mkdir(parents=True)
            (out / "raw/de/01.png").write_bytes(png(1320, 2868))
            (out / "run.json").write_text(json.dumps({"platform": "ios", "locales": {"de": {"ok": True}}}))
            (out / "check.json").write_text(json.dumps({"problems": []}))
            dst = Path(d) / "fl/screenshots/de-DE"; dst.mkdir(parents=True)
            (dst / "old_iphone.png").write_bytes(png(1320, 2868)); (dst / "ipad.png").write_bytes(png(2064, 2752))
            sf.cmd_export(out, Path(d) / "fl")
            self.assertEqual(sorted(p.name for p in dst.iterdir()), ["01.png", "ipad.png"])

    def test_export_needs_a_check_first(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d); (out / "run.json").write_text("{}")
            with self.assertRaises(sf.Fail): sf.cmd_export(out, out / "fl")

    def test_partly_translated_apps_keep_their_languages(self):
        en = {f"k{i}": "x" for i in range(100)}
        de = {f"k{i}": "y" for i in range(80)}
        self.assertEqual(sf.shipped_locales({"en": en, "de": de}), ["de", "en"])
        self.assertEqual(sf.shipped_locales({"de": de, "fr": de}), ["de", "fr"])  # no English at all: no crash

    def test_flows_launch_once_and_screenshot_comments_are_ignored(self):
        flow = "appId: x\n---\n# start\n- launchApp\n- takeScreenshot: 01_home # first\n"
        ios = sf.localize_flow(flow, "de", Path("/s"))
        self.assertEqual(ios.count("- launchApp"), 1)
        self.assertIn("/s/01_home'", ios)
        self.assertEqual(sf.android_flow(flow, "f", Path("/s")).count("- launchApp"), 1)

    def test_folders_with_both_platforms_or_jpegs(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "screenshots/de-DE").mkdir(parents=True); (Path(d) / "metadata/android").mkdir(parents=True)
            with self.assertRaises(sf.Fail): sf.find_screenshots(d)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "fr").mkdir(); (Path(d) / "fr/a.jpg").write_bytes(b"j"); (Path(d) / "fr/notes.txt").write_text("")
            self.assertEqual({k: [p.name for p in v] for k, v in sf.find_screenshots(d).items()}, {"fr": ["a.jpg"]})


class FirstRun(unittest.TestCase):
    def cli(self, *args, python=sys.executable):
        return subprocess.run([python, str(Path(sf.__file__)), *args], capture_output=True, text=True)

    def test_old_python_gets_a_sentence_not_a_traceback(self):
        if not Path("/usr/bin/python3").exists(): self.skipTest("no system python")
        r = self.cli("doctor", python="/usr/bin/python3")
        if r.returncode == 2 and "3.11" in r.stderr: return
        self.assertNotIn("Traceback", r.stderr)

    def test_wrong_build_types_say_what_to_pass(self):
        for name, words in (("x.ipa", "simulator .app"), ("x.aab", "assembleDebug"), ("x.zip", "unzip")):
            r = self.cli("init", name, tempfile.mkdtemp())
            self.assertEqual(r.returncode, 2); self.assertIn(words, r.stderr)

    def test_empty_folder_and_empty_locales_are_setup_errors(self):
        r = self.cli("check", tempfile.mkdtemp())
        self.assertEqual(r.returncode, 2); self.assertIn("Expected one of", r.stderr)
        self.assertEqual(self.cli("run", "x.toml", "--locales", "").returncode, 2)

    def test_config_paths_are_short(self):
        d = Path(tempfile.mkdtemp())
        self.assertEqual(sf.config_path(d / "build/App.app", d), "build/App.app")
        self.assertTrue(sf.config_path(Path.home() / "Library/x/App.app", "/tmp/a/b/c/d").startswith("~/Library"))


class TolerantMatching(unittest.TestCase):
    def test_ocr_and_strings_meet_halfway(self):
        same = [("Paramètres", "PARAMETRES"), ("Réglages\u202f:", "Réglages :"), ("الجولة ٢/١٢", "الجولة 2/12"),
                ("\u200fمرحبا", "مرحبا"), ("Beállítások", "Beallitasok"), ("Kő", "Kö"), ("ｆｕｌｌ", "full"),
                ("دور ۳", "دور 3"), ("  two   spaces ", "two spaces")]
        for a, b in same:
            self.assertEqual(sf.norm(a), sf.norm(b), (a, b))
        self.assertNotEqual(sf.norm("Weiter"), sf.norm("Weiterer"))

    def test_upper_case_android_button_still_counts(self):
        tables = sf.string_tables({"de": {"n": "Weiter", "s": "Einstellungen"}, "en": {"n": "Next", "s": "Settings"}})
        self.assertEqual(sf.judge_screen("de", {"chars": 30, "text": "WEITER\nEINSTELLUNGEN"}, tables), ("de", None))


if __name__ == "__main__":
    unittest.main()
