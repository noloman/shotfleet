"""Tests for shotfleet's logic. No simulators, emulators or Maestro needed.

Run: python3 -m unittest discover -s tests
"""
import contextlib, io, json, os, subprocess, sys, tempfile, time, tomllib, unittest
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

    def test_launch_app_options_are_kept_and_merged(self):
        flow = ("appId: x\n---\n- launchApp:\n    permissions:\n      all: allow\n    arguments:\n      demo: \"1\"\n"
                "- tapOn: Next\n")
        out = sf.localize_flow(flow, "de", Path("/o"))
        self.assertEqual(out.count("- launchApp"), 1)
        for line in ("    clearState: true", "    permissions:", "      all: allow", '      AppleLanguages: "(de)"', '      demo: "1"'):
            self.assertIn(line + "\n", out)
        self.assertEqual(out.count("    arguments:"), 1)
        no_clear = sf.localize_flow("appId: x\n---\n- launchApp:\n    clearState: false\n", "de", Path("/o"))
        self.assertNotIn("clearState: true", no_clear)

    def test_inline_launch_app_options_are_rejected_clearly(self):
        with self.assertRaisesRegex(ValueError, "as a block"):
            sf.localize_flow("appId: x\n---\n- launchApp: { clearState: true }\n", "de", Path("/o"))

    def test_system_dialog_buttons_keep_their_english_text(self):  # iOS draws them in the device language
        out, missing, _ = sf.translate_flow("appId: x\n---\n- tapOn: Allow\n- tapOn: \"Don't Allow\"\n",
                                            {"a": "Allow"}, {"a": "Erlauben"})
        self.assertIn("'(Allow|Erlauben)'", out); self.assertIn('"Don\'t Allow"', out); self.assertEqual(missing, [])

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
                ("[other]\nx = 1\n", "needs an [ios] or an [android] section"),
                ("[ios]\n", "missing: app"),
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
            got = sf.load_strings(app)
            self.assertEqual(got["de"], {
                "next": "Weiter", "title": "Titel", "Feature_Feature.bundle/Localizable:next": "Nächste",
                "Watch/W.app/Localizable:start": "Training starten"})
            self.assertEqual(got["en"]["Watch/W.app/Localizable:start"], "start")  # no en table: keys are the text

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


class BaseAndFallback(unittest.TestCase):
    STRINGS = {"en-GB": {"n": "Next", "c": "Colour"}, "pt": {"n": "Próximo", "c": "Cor"}, "pt-BR": {"c": "Cor!"},
               "zh-Hant": {"n": "下一步"}, "zh-Hant-HK": {}}

    def test_regional_locales_fall_back_to_their_language(self):
        self.assertEqual(sf.with_fallback(self.STRINGS, "pt-BR"), {"n": "Próximo", "c": "Cor!"})
        self.assertEqual(sf.with_fallback(self.STRINGS, "zh-Hant-HK"), {"n": "下一步"})

    def test_flow_translates_through_the_fallback(self):
        out, missing, _ = sf.translate_flow("appId: x\n---\n- tapOn: Next\n", self.STRINGS["en-GB"],
                                            sf.with_fallback(self.STRINGS, "pt-BR"))
        self.assertIn("'Próximo'", out); self.assertEqual(missing, [])

    def test_base_language_found_or_explained(self):
        self.assertEqual(sf.resolve_base(self.STRINGS, "en"), "en-GB")  # app ships only British English
        self.assertEqual(sf.resolve_base({"de": {}, "en": {}}, "de"), "de")
        with self.assertRaises(sf.Fail) as e: sf.resolve_base({"de": {}}, "en")
        self.assertIn("base_locale", str(e.exception))


class RealAppDefects(unittest.TestCase):
    def test_string_catalog_keyed_by_english_text(self):  # Keysi: no en table in the build
        with tempfile.TemporaryDirectory() as d:
            for lp, rows in {"de": '"Next" = "Weiter"; "Delete key" = "Schlüssel löschen";', "ja": '"Next" = "次へ";'}.items():
                (Path(d) / f"{lp}.lproj").mkdir(); (Path(d) / f"{lp}.lproj/Localizable.strings").write_text(rows)
            got = sf.load_strings(Path(d))
        self.assertEqual(got["en"], {"Next": "Next", "Delete key": "Delete key"})
        out, missing, _ = sf.translate_flow("appId: x\n---\n- tapOn: Next\n", got["en"], got["de"])
        self.assertIn("'Weiter'", out); self.assertEqual(missing, [])

    def test_multi_line_android_strings(self):
        dump = ('Package name=x id=7f\n  type string id=10 entryCount=1\n    resource 0x7f120272 string/share\n'
                '      () "%1$s\n      Next renewal: %2$s"\n      (de) "%1$s\n      Nächste Verlängerung: %2$s"\n'
                '    resource 0x7f120273 string/ok\n      () "OK"\n')
        with mock.patch.object(sf, "aapt2", return_value="aapt2"), \
             mock.patch.object(sf, "sh", return_value=subprocess.CompletedProcess([], 0, dump, "")):
            got = sf.load_strings_apk("x.apk")
        self.assertEqual(got["de"]["share"], "%1$s\nNächste Verlängerung: %2$s")
        self.assertEqual(got["en"], {"share": "%1$s\nNext renewal: %2$s", "ok": "OK"})

    def test_yaml_quoted_selectors(self):
        base, de = {"w": "What's new", "s": 'Say "hi"'}, {"w": "Neuigkeiten", "s": "Sag „hallo“"}
        out, missing, _ = sf.translate_flow("appId: x\n---\n- tapOn: 'What''s new'\n- tapOn: \"Say \\\"hi\\\"\"\n", base, de)
        self.assertEqual(missing, []); self.assertIn("'Neuigkeiten'", out)

    def test_non_language_store_folders_are_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            for f in ("de-DE", "ipad_only", "default", "zh-Hans"):
                (Path(d) / f).mkdir(); (Path(d) / f / "1.png").write_bytes(b"p")
            self.assertEqual(sorted(sf.find_screenshots(d)), ["de-DE", "zh-Hans"])


class PluralsAndFormats(unittest.TestCase):
    EN = {"r": "Round %1$d of %2$d", "h": "Hello, %@", "d#one": "%d day since your last PR",
          "d#other": "%d days since your last PR"}
    PL = {"r": "Runda %1$d z %2$d", "h": "Cześć, %@", "d#one": "%d dzień od PR", "d#few": "%d dni od PR",
          "d#many": "%d dni od PR", "d#other": "%d dnia od PR"}

    def test_selectors_with_numbers_translate_into_every_plural_form(self):
        flow = "appId: x\n---\n- tapOn: Round 2 of 12\n- assertVisible: 3 days since your last PR\n- tapOn: Hello, Anna\n"
        out, missing, _ = sf.translate_flow(flow, self.EN, self.PL)
        self.assertIn("'Runda 2 z 12'", out)
        self.assertIn("'(3 dni od PR|3 dnia od PR|3 dzień od PR)'", out)
        self.assertIn("'Cześć, Anna'", out)
        self.assertEqual(missing, [])

    def test_positional_arguments_keep_their_meaning(self):
        self.assertEqual(sf.fill_format("%2$d من %1$d", {"a1": "2", "a2": "12"}), "12 من 2")
        self.assertIsNone(sf.fill_format("%1$d / %3$d", {"a1": "2"}))

    def test_lines_with_numbers_count_for_the_right_language(self):
        t = sf.string_tables({"en": self.EN, "pl": self.PL})
        self.assertEqual(sf.judge_screen("pl", {"chars": 40, "text": "Runda 2 z 12\nCześć, Anna\n3 dni od PR"}, t), ("pl", None))
        got, problem = sf.judge_screen("pl", {"chars": 40, "text": "Round 2 of 12\nHello, Anna\n3 days since your last PR"}, t)
        self.assertEqual(got, "en"); self.assertIsNotNone(problem)

    def test_bare_placeholders_are_not_evidence(self):  # "%d" or "%@ %@" would match any line
        t = sf.string_tables({"en": {"n": "%d", "x": "%@ %@"}})
        self.assertIsNone(t["en"].formats)

    def test_stringsdict_forms(self):
        d = {"items": {"NSStringLocalizedFormatKey": "%#@n@ in %#@lists@",
                       "n": {"NSStringFormatSpecTypeKey": "NSStringPluralRuleType", "NSStringFormatValueTypeKey": "d",
                             "one": "%d item", "other": "%d items"},
                       "lists": {"NSStringFormatSpecTypeKey": "NSStringPluralRuleType", "one": "%d list", "other": "%d lists"}},
             "title": {"NSStringDeviceSpecificRuleType": {"iphone": "Tap here", "ipad": "Click here"}}}
        got = sf.stringsdict_forms(d)
        self.assertEqual(got["items#n.one"], "%d item in %d lists")
        self.assertEqual(got["items#lists.one"], "%d items in %d list")
        self.assertEqual(got["title#ipad"], "Click here")

    def test_android_plurals(self):
        dump = ('Package name=x id=7f\n  type plurals id=0e entryCount=1\n    resource 0x7f0e0001 plurals/days\n'
                '      () (plurals) size=2\n        one="%1$d day"\n        other="%1$d days"\n'
                '      (pl) (plurals) size=3\n        one="%1$d dzień"\n        few="%1$d dni"\n        other="%1$d dnia"\n')
        with mock.patch.object(sf, "aapt2", return_value="aapt2"), \
             mock.patch.object(sf, "sh", return_value=subprocess.CompletedProcess([], 0, dump, "")):
            got = sf.load_strings_apk("x.apk")
        self.assertEqual(got["pl"], {"days#one": "%1$d dzień", "days#few": "%1$d dni", "days#other": "%1$d dnia"})


class Evidence(unittest.TestCase):
    def test_one_borrowed_word_on_a_sparse_screen_is_not_wrong_language(self):  # French watch: "Round 1/12"
        t = sf.string_tables({"en": {"r": "Round %1$d/%2$d", "p": "Pause"}, "fr": {"r": "Tour %1$d/%2$d", "p": "Pause"}})
        self.assertEqual(sf.judge_screen("fr", {"chars": 40, "text": "TRAVAIL\nRound 1/12\nPause\nTerminer"}, t), ("fr", None))

    def test_one_word_still_separates_regional_variants_on_a_full_screen(self):
        common = {f"k{i}": f"Shared label {i}" for i in range(6)}
        t = sf.string_tables({"en": {**common, "c": "Color"}, "en-GB": {**common, "c": "Colour"}})
        text = "\n".join([*common.values(), "Color"])
        self.assertIsNotNone(sf.judge_screen("en-GB", {"chars": 90, "text": text}, t)[1])


class SourceFiles(unittest.TestCase):
    def files(self, files):
        d = Path(tempfile.mkdtemp())
        for rel, body in files.items():
            (d / rel).parent.mkdir(parents=True, exist_ok=True); (d / rel).write_text(body)
        return d

    def test_language_from_file_and_folder_names(self):
        cases = {"lib/l10n/app_de.arb": "de", "lib/l10n/app_pt_BR.arb": "pt-BR", "locales/de/translation.json": "de",
                 "i18n/ja.json": "ja", "Resources/AppResources.fr.resx": "fr", "po/zh_Hant.po": "zh-Hant",
                 "res/values-b+sr+Latn/strings.xml": "sr-Latn", "res/values/strings.xml": "base",
                 "messages_pt_BR.properties": "pt-BR", "Resources/AppResources.resx": None}
        for path, want in cases.items():
            self.assertEqual(sf.locale_from_path(path), want, path)

    def test_flutter_arb_with_icu_plurals(self):
        d = self.files({"l10n/app_en.arb": '{"@@locale": "en", "next": "Next", "@next": {}, '
                        '"items": "{count, plural, =0{No items} one{1 item} other{{count} items}}"}',
                        "l10n/app_de.arb": '{"@@locale": "de", "next": "Weiter", '
                        '"items": "{count, plural, =0{Keine Elemente} one{1 Element} other{{count} Elemente}}"}'})
        got = sf.load_strings_files([str(d / "l10n/*.arb")])
        self.assertEqual(got["de"], {"next": "Weiter", "items#=0": "Keine Elemente", "items#one": "1 Element",
                                     "items#other": "{count} Elemente"})
        out, missing, _ = sf.translate_flow("appId: x\n---\n- tapOn: Next\n- assertVisible: 5 items\n", got["en"], got["de"])
        self.assertIn("'Weiter'", out); self.assertIn("5 Elemente", out); self.assertEqual(missing, [])

    def test_i18next_json(self):
        d = self.files({"locales/en/translation.json": '{"nav": {"next": "Next"}, "hello": "Hello, {{name}}", "day_one": "{{count}} day", "day_other": "{{count}} days"}',
                        "locales/de/translation.json": '{"nav": {"next": "Weiter"}, "hello": "Hallo, {{name}}", "day_one": "{{count}} Tag", "day_other": "{{count}} Tage"}'})
        got = sf.load_strings_files([str(d / "locales/*/translation.json")])
        self.assertEqual(got["de"]["nav.next"], "Weiter")
        self.assertEqual(got["de"]["day#other"], "{{count}} Tage")
        out, _, _ = sf.translate_flow("appId: x\n---\n- assertVisible: Hello, Anna\n- assertVisible: 3 days\n", got["en"], got["de"])
        self.assertIn("'Hallo, Anna'", out); self.assertIn("3 Tage", out)

    def test_xliff_resx_po_properties_csv_xcstrings(self):
        d = self.files({
            "x/de.xliff": '<xliff version="1.2"><file source-language="en" target-language="de"><body>'
                          '<trans-unit id="next"><source>Next</source><target>Weiter</target></trans-unit></body></file></xliff>',
            "r/App.resx": '<root><data name="Next"><value>Next</value></data></root>',
            "r/App.ja.resx": '<root><data name="Next"><value>次へ</value></data></root>',
            "p/fr.po": 'msgid ""\nmsgstr "Language: fr\\n"\n\nmsgid "Next"\nmsgstr "Suivant"\n',
            "j/messages_it.properties": "next=Avanti\n# comment\n",
            "u/table.csv": "Key,English(en),Spanish(es)\nnext,Next,Siguiente\n",
            "c/Localizable.xcstrings": json.dumps({"sourceLanguage": "en", "strings": {"Next": {"localizations": {
                "ko": {"stringUnit": {"state": "translated", "value": "다음"}}}},
                "%lld items": {"localizations": {"ko": {"variations": {"plural": {"other": {"stringUnit": {"value": "%lld개 항목"}}}}}}}}})})
        got = sf.load_strings_files([str(d / "**/*.*")])
        self.assertEqual(got["de"]["next"], "Weiter"); self.assertEqual(got["en"]["next"], "Next")
        self.assertEqual(got["ja"]["Next"], "次へ")
        self.assertEqual(got["fr"]["Next"], "Suivant")
        self.assertEqual(got["it"]["next"], "Avanti")
        self.assertEqual(got["es"]["next"], "Siguiente")
        self.assertEqual(got["ko"]["Next"], "다음"); self.assertEqual(got["ko"]["%lld items#other"], "%lld개 항목")

    def test_details_each_format_gets_right(self):
        d = self.files({
            "l10n/intl_messages.arb": '{"@@locale": "de", "n": "{n, plural, one{# Element} other{# Elemente}}"}',
            "res/values/strings.xml": '<resources><string name="a">"  Weiter  "</string><string name="b">Sag "hallo"</string></resources>',
            "c/Localizable.xcstrings": json.dumps({"sourceLanguage": "en", "strings": {"Next": {"localizations": {
                "ko": {"stringUnit": {"value": "다음"}}}}}})})
        arb = sf.load_strings_files([str(d / "l10n/*.arb")])
        self.assertEqual(arb["de"]["n#other"], "{n} Elemente")  # @@locale wins over the file name; # is the number
        xml = sf.load_strings_files([str(d / "res/values/strings.xml")])
        self.assertEqual(xml["en"], {"a": "  Weiter  ", "b": 'Sag "hallo"'})
        cat = sf.load_strings_files([str(d / "c/*.xcstrings")])
        self.assertEqual(cat["en"], {"Next": "Next"})  # the source text is the key

    def test_unknown_format_and_no_match_explain_themselves(self):
        d = self.files({"a.yml": "x: 1"})
        with self.assertRaises(sf.Fail): sf.load_strings_files([str(d / "*.yml")])
        with self.assertRaises(sf.Fail): sf.load_strings_files([str(d / "*.arb")])

    def test_android_escapes(self):
        self.assertEqual(sf.unescape_android(r"\ud83d\udcf1 verf\u00fcgbar \"x\" it\'s"), '📱 verfügbar "x" it\'s')


def png_c(w, h, color_type=2):  # PNG header with a color type: 2 = RGB, 6 = RGBA
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, color_type]) + b"\0" * 8 + b"IDAT"


class StoreRules(unittest.TestCase):
    def images(self, spec):
        d = Path(tempfile.mkdtemp()); out = {}
        for label, files in spec.items():
            (d / label).mkdir()
            for name, data in files.items():
                (d / label / name).write_bytes(data); out.setdefault(label, []).append(d / label / name)
        return out

    def test_app_store_sizes_alpha_counts_and_required_class(self):
        imgs = self.images({"de-DE": {f"{i}.png": png_c(1320, 2868) for i in range(11)},
                            "ja": {"a.png": png_c(1179, 2556), "b.png": png_c(1320, 2868, 6), "c.png": png_c(1000, 2000)},
                            "fr-FR": {"w.png": png_c(416, 496), "l.png": png_c(2868, 1320)}})
        problems, _ = sf.store_rules(imgs, android=False)
        text = "\n".join(problems)
        self.assertIn("de-DE: 11 iPhone 6.9\" screenshots", text)
        self.assertIn("ja/b.png: has transparency", text)
        self.assertIn("ja/c.png: 1000x2000 isn't an App Store screenshot size", text)
        self.assertNotIn("fr-FR", text)  # watch size and landscape 6.9" are fine
        ja_only_63 = self.images({"ja": {"a.png": png_c(1179, 2556)}})
        self.assertIn('need a 6.9" or 6.5" set', sf.store_rules(ja_only_63, android=False)[0][0])
        self.assertIn('13" iPad', sf.store_rules(self.images({"de": {"a.png": png_c(1320, 2868)}}), android=False, ipad=True)[0][0])

    def test_google_play_limits_and_notes(self):
        imgs = self.images({"de-DE": {f"{i}.png": png_c(1080, 2400) for i in range(9)},
                            "ja-JP": {f"{i}.png": png_c(1080, 1920) for i in range(4)},
                            "ko-KR": {"a.png": png_c(200, 400), "b.jpg": b"\xff\xd8\xff\xc0\x00\x11\x08\x07\x80\x04\x38" + b"\0" * 12}})
        problems, notes = sf.store_rules(imgs, android=True)
        self.assertIn("de-DE: 9 phone screenshots; Google Play takes at most 8", problems)
        self.assertTrue(any("ko-KR/a.png: 200x400 is outside" in p for p in problems))
        self.assertEqual(len([n for n in notes if "longer than 2:1" in n]), 1)  # grouped, not per file
        self.assertTrue(any("de-DE, ko-KR" in n and "recommendations" in n for n in notes))  # ja-JP qualifies

    def test_image_info_reads_jpeg_size(self):
        d = Path(tempfile.mkdtemp()) / "a.jpg"
        d.write_bytes(b"\xff\xd8\xff\xe0\x00\x04ab\xff\xc0\x00\x11\x08\x07\x80\x04\x38" + b"\0" * 12)
        self.assertEqual(sf.image_info(d), ((1080, 1920), False))


class ExternalOcr(unittest.TestCase):
    def test_scripts_macos_cant_read_go_to_the_ocr_command(self):
        el = {"a": "Επόμενο", "b": "Ρυθμίσεις", "c": "Έναρξη προπόνησης"}
        en = {"a": "Next", "b": "Settings", "c": "Start Training"}
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for lp, words in (("el", el), ("en", en)):
                (d / lp).mkdir()
                (d / lp / "1.png").write_bytes(png_c(1320, 2868)); (d / lp / "1.png.txt").write_text("\n".join(words.values()))
            (d / "el" / "2.png").write_bytes(png_c(1320, 2868)); (d / "el" / "2.png.txt").write_text("\n".join(en.values()))
            with contextlib.redirect_stdout(io.StringIO()):
                code = sf.cmd_check(d, strings={"en": en, "el": el}, report_dir=d / "rep", ocr_command="cat {image}.txt")
            report = json.loads((d / "rep/check.json").read_text())
        langs = {r["file"]: r["lang"] for r in report["screenshots"]}
        self.assertEqual(langs["el/1.png"], "el")  # read and verified, not "couldn't read"
        self.assertTrue(any(p.startswith("el/2.png: shows en") for p in report["problems"]), report["problems"])
        self.assertEqual(code, 1)

    def test_tesseract_language_names(self):
        self.assertEqual(sf.TESSERACT["he"], "heb"); self.assertEqual(sf.TESSERACT["el"], "ell")


class Mcp(unittest.TestCase):
    def test_protocol_handshake_tools_and_errors(self):
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "check", "arguments": {"folder": "/no/such"}}},
                {"jsonrpc": "2.0", "id": 4, "method": "nope"}]
        r = subprocess.run([sys.executable, str(Path(sf.__file__)), "mcp"], input="\n".join(map(json.dumps, msgs)) + "\n",
                           capture_output=True, text=True, timeout=60)
        out = {m["id"]: m for m in map(json.loads, r.stdout.splitlines())}
        self.assertEqual(sorted(out), [1, 2, 3, 4])  # nothing for the notification, nothing else on stdout
        self.assertEqual(out[1]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual({t["name"] for t in out[2]["result"]["tools"]}, {"check", "doctor", "run"})
        self.assertTrue(out[3]["result"]["isError"]); self.assertIn("no folder", out[3]["result"]["content"][0]["text"])
        self.assertEqual(out[4]["error"]["code"], -32601)


class Licence(unittest.TestCase):
    """Against a fake Lemon Squeezy licence API on localhost."""
    def setUp(self):
        import http.server, threading, urllib.parse
        self.calls, test = [], self
        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = dict(urllib.parse.parse_qsl(self.rfile.read(int(self.headers["Content-Length"])).decode()))
                test.calls.append((self.path.rsplit("/", 1)[-1], body))
                good = body.get("license_key") == "GOOD"
                reply = {"activate": {"activated": good, "instance": {"id": "inst1"}, "error": None if good else "license_key not found"},
                         "validate": {"valid": good, "error": None if good else "expired"},
                         "deactivate": {"deactivated": True}}[self.path.rsplit("/", 1)[-1]]
                self.send_response(200 if good or "deactivate" in self.path else 400); self.end_headers()
                self.wfile.write(json.dumps(reply).encode())
            def log_message(self, *a): pass
        self.server = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.dir = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(sf, "LICENCE_API", f"http://127.0.0.1:{self.server.server_port}/v1/licenses"),
                        mock.patch.object(sf, "LICENCE_FILE", self.dir / "licence.json"),
                        mock.patch.object(sf.sys, "frozen", True, create=True)]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in self.patches: p.stop()
        self.server.shutdown()

    def quiet(self, f, *a):
        with contextlib.redirect_stdout(io.StringIO()): return f(*a)

    def test_released_build_needs_a_licence_for_run(self):
        with self.assertRaisesRegex(sf.Fail, "shotfleet activate"): sf.require_licence()
        with self.assertRaisesRegex(sf.Fail, "didn't activate"): self.quiet(sf.cmd_activate, "BAD")
        self.quiet(sf.cmd_activate, "GOOD")
        sf.require_licence()  # fresh: no network call
        self.assertEqual([c[0] for c in self.calls], ["activate", "activate"])

    def test_weekly_recheck_and_offline_grace(self):
        self.quiet(sf.cmd_activate, "GOOD")
        lic = json.loads(sf.LICENCE_FILE.read_text())
        sf.LICENCE_FILE.write_text(json.dumps({**lic, "checked": time.time() - 8 * 86400}))
        sf.require_licence(); self.assertEqual(self.calls[-1][0], "validate")
        with mock.patch.object(sf, "LICENCE_API", "http://127.0.0.1:9/nope"):  # unreachable
            sf.LICENCE_FILE.write_text(json.dumps({**lic, "checked": time.time() - 10 * 86400}))
            sf.require_licence()  # within 30 days offline
            sf.LICENCE_FILE.write_text(json.dumps({**lic, "checked": time.time() - 31 * 86400}))
            with self.assertRaisesRegex(sf.Fail, "30 days"): sf.require_licence()

    def test_revoked_licence_and_ci_key(self):
        sf.LICENCE_FILE.write_text(json.dumps({"key": "REVOKED", "instance": "x", "checked": 0}))
        with self.assertRaisesRegex(sf.Fail, "no longer valid"): sf.require_licence()
        sf.LICENCE_FILE.unlink()
        with mock.patch.dict(os.environ, {"SHOTFLEET_KEY": "GOOD"}): sf.require_licence()
        with mock.patch.dict(os.environ, {"SHOTFLEET_KEY": "BAD"}):
            with self.assertRaisesRegex(sf.Fail, "SHOTFLEET_KEY"): sf.require_licence()

    def test_source_checkout_never_asks(self):
        with mock.patch.object(sf.sys, "frozen", False): sf.require_licence()


class GumroadLicence(unittest.TestCase):
    """Against a fake Gumroad /v2/licenses/verify (shape from antiwork/gumroad licenses_controller.rb)."""
    GOOD, REFUNDED = "ABCDEF12-34567890-ABCDEF12-34567890", "11111111-22222222-33333333-44444444"

    def setUp(self):
        import http.server, threading, urllib.parse
        self.uses, self.calls, test = {self.GOOD: 0, self.REFUNDED: 0}, [], self
        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                b = dict(urllib.parse.parse_qsl(self.rfile.read(int(self.headers["Content-Length"])).decode()))
                test.calls.append(b)
                key = b.get("license_key")
                if key not in test.uses or b.get("product_id") != "prod1":
                    self.send_response(404); self.end_headers()
                    self.wfile.write(b'{"success":false,"message":"That license does not exist for the provided product."}'); return
                if b.get("increment_uses_count") != "false": test.uses[key] += 1
                body = {"success": True, "uses": test.uses[key], "purchase": {"refunded": key == test.REFUNDED, "chargebacked": False}}
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps(body).encode())
            def log_message(self, *a): pass
        self.server = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        d = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(sf, "GUMROAD_API", f"http://127.0.0.1:{self.server.server_port}/v2/licenses"),
                        mock.patch.object(sf, "GUMROAD_PRODUCT_ID", "prod1"),
                        mock.patch.object(sf, "LICENCE_FILE", d / "licence.json"),
                        mock.patch.object(sf.sys, "frozen", True, create=True)]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in self.patches: p.stop()
        self.server.shutdown()

    def activate(self, key):
        with contextlib.redirect_stdout(io.StringIO()): return sf.cmd_activate(key)

    def test_key_formats(self):
        self.assertTrue(sf.is_gumroad_key(self.GOOD))
        self.assertFalse(sf.is_gumroad_key("38b1460a-5104-4067-a91d-77b872934d51"))  # Lemon Squeezy UUID

    def test_three_macs_then_refused(self):
        for _ in range(3): self.activate(self.GOOD)
        with self.assertRaisesRegex(sf.Fail, "3 Macs"): self.activate(self.GOOD)

    def test_refunded_and_unknown_keys_are_refused(self):
        with self.assertRaisesRegex(sf.Fail, "refunded"): self.activate(self.REFUNDED)
        with self.assertRaisesRegex(sf.Fail, "does not exist"): self.activate("99999999-99999999-99999999-99999999")

    def test_weekly_recheck_doesnt_use_an_activation(self):
        self.activate(self.GOOD)
        lic = json.loads(sf.LICENCE_FILE.read_text())
        sf.LICENCE_FILE.write_text(json.dumps({**lic, "checked": 0}))
        sf.require_licence()
        self.assertEqual(self.uses[self.GOOD], 1)
        self.assertEqual(self.calls[-1]["increment_uses_count"], "false")
        with mock.patch.dict(os.environ, {"SHOTFLEET_KEY": self.GOOD}): sf.require_licence()
        self.assertEqual(self.uses[self.GOOD], 1)


class ScreenText(unittest.TestCase):
    def test_flows_pause_after_each_screenshot(self):
        flow = "appId: x\n---\n- takeScreenshot: a\n- tapOn: Next\n- takeScreenshot:\n    path: b\n- tapOn: Done\n"
        out = sf.localize_flow(flow, "de", Path("/s"))
        self.assertEqual(out.count("__shotfleet_reading_screen__"), 2)
        self.assertLess(out.index("/s/a'"), out.index("__shotfleet_reading_screen__"))
        self.assertLess(out.index("path: '/s/b'"), out.rindex("__shotfleet_reading_screen__"))
        self.assertLess(out.rindex("__shotfleet_reading_screen__"), out.index("- tapOn: Done"))

    def test_check_prefers_the_apps_own_text(self):
        with tempfile.TemporaryDirectory() as d:
            png = Path(d) / "el" / "1.png"; png.parent.mkdir(); png.write_bytes(png_c(1320, 2868))
            png.with_suffix(".texts.json").write_text(json.dumps(["Επόμενο", "Ρυθμίσεις\nσυσκευής"]))
            r = sf.screen_text(png)
        self.assertEqual(r["text"], "Επόμενο\nΡυθμίσεις συσκευής")  # one element per line
        t = sf.string_tables({"el": {"a": "Επόμενο", "b": "Ρυθμίσεις\nσυσκευής"}, "en": {"a": "Next", "b": "Device settings"}})
        self.assertEqual(sf.judge_screen("el", r, t), ("el", None))  # Greek verified: no OCR involved
        self.assertIsNone(sf.screen_text(Path(d) / "missing.png"))


class MultiDevice(unittest.TestCase):
    def make(self, d, devices, families):
        app = Path(d) / "My.app"; app.mkdir()
        subprocess.run(["/usr/libexec/PlistBuddy", "-c", "Add :UIDeviceFamily array", "-c",
                        *[x for f in families for x in ("-c", f"Add :UIDeviceFamily: integer {f}")][1:], str(app / "Info.plist")],
                       capture_output=True)
        out = Path(d) / "out"
        for name, size in devices.items():
            raw = out / name / "raw" / "de"; raw.mkdir(parents=True)
            (raw / "01_home.png").write_bytes(png_c(*size))
            (out / name / "run.json").write_text(json.dumps({"app": str(app), "locales": {"de": {"ok": True}}}))
            (out / name / "check.json").write_text(json.dumps({"problems": []}))
        return out

    def test_export_keeps_both_sizes_and_ipad_rule_spans_devices(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.make(d, {"iphone-17-pro-max": (1320, 2868), "ipad-pro-13-inch-m5-12gb": (2064, 2752)}, [1, 2])
            with contextlib.redirect_stdout(io.StringIO()):
                sf.cmd_export(out, Path(d) / "fl")
                self.assertEqual(sf.ipad_set_missing(out), 0)
            self.assertEqual(sorted(p.name for p in (Path(d) / "fl/screenshots/de-DE").iterdir()),
                             ["ipad-pro-13-inch-m5-12gb_01_home.png", "iphone-17-pro-max_01_home.png"])
        with tempfile.TemporaryDirectory() as d:
            out = self.make(d, {"iphone-17-pro-max": (1320, 2868)}, [1, 2])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sf.ipad_set_missing(out), 1)  # iPad app, iPhone set only


class StuckOcrFallback(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.bin = self.d / "bin"; self.bin.mkdir()
        self.log = self.d / "calls.txt"
        (self.bin / "tesseract").write_text(f'#!/bin/sh\necho "$@" >> {self.log}\ncat "$1.txt"\n')
        (self.bin / "tesseract").chmod(0o755)
        for lp, words in (("de", ["Weiter", "Einstellungen", "Training starten"]), ("ja", ["Next", "Settings", "Start Training"])):
            png = self.d / "shots" / lp / "1.png"; png.parent.mkdir(parents=True)
            png.write_bytes(png_c(1320, 2868)); Path(f"{png}.txt").write_text("\n".join(words))
        self.strings = {"en": {"a": "Next", "b": "Settings", "c": "Start Training"},
                        "de": {"a": "Weiter", "b": "Einstellungen", "c": "Training starten"},
                        "ja": {"a": "次へ", "b": "設定", "c": "トレーニング開始"}}

    def check(self):
        with mock.patch.object(sf, "warm_up_ocr", return_value=False), \
             mock.patch.object(sf, "read_text", side_effect=AssertionError("macOS OCR must not be called")), \
             mock.patch.dict(os.environ, {"PATH": f"{self.bin}:{os.environ['PATH']}"}), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            code = sf.cmd_check(self.d / "shots", strings=self.strings, report_dir=self.d / "rep")
        return code, out.getvalue(), json.loads((self.d / "rep/check.json").read_text())

    def test_stuck_macos_ocr_falls_back_to_tesseract(self):
        code, out, report = self.check()
        self.assertIn("using Tesseract instead", out)
        self.assertIn("-l eng+deu", self.log.read_text()); self.assertIn("-l eng+jpn", self.log.read_text())
        self.assertTrue(any(p.startswith("ja/1.png: shows en") for p in report["problems"]))  # still catches English
        self.assertFalse(any(p.startswith("de/") for p in report["problems"]))

    def test_without_tesseract_it_says_how_to_fix(self):
        (self.bin / "tesseract").unlink()
        with mock.patch.object(sf.shutil, "which", return_value=None):
            with self.assertRaisesRegex(sf.Fail, "brew install tesseract"):
                self.check()


class SimpleConfig(unittest.TestCase):
    """One small config for both platforms: only the build is required; ids come from it."""
    def build(self, d):
        app = Path(d) / "My.app"; app.mkdir()
        (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "com.example.my", "DTPlatformName": "iphonesimulator"}))
        (Path(d) / "flow.yaml").write_text("- launchApp\n")
        return app

    def test_bare_steps_and_one_flow_for_both_platforms(self):
        steps = "- launchApp\n- takeScreenshot: 01\n"
        self.assertEqual(sf.with_app_id(steps, "com.x"), "appId: com.x\n---\n" + steps)
        full = "appId: ios.id\nname: Shots\n---\n" + steps
        self.assertEqual(sf.with_app_id(full, "android.pkg"), "appId: android.pkg\nname: Shots\n---\n" + steps)
        self.assertEqual(sf.with_app_id("---\n- launchApp\n", "com.x"), "appId: com.x\n---\n- launchApp\n")
        out = sf.localize_flow(sf.with_app_id(steps, "com.x"), "de", Path("/shots"))
        self.assertTrue(out.startswith("appId: com.x\nname: de\n---\n"))

    def test_only_the_build_is_required_and_ids_come_from_it(self):
        with tempfile.TemporaryDirectory() as d:
            self.build(d)
            (Path(d) / "shotfleet.toml").write_text('[ios]\napp = "My.app"\n')
            with mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"):
                platform, cfg, _ = sf.load_config(Path(d) / "shotfleet.toml")
                self.assertEqual((platform, cfg["bundle_id"], cfg["flow"], cfg["out"]), ("ios", "com.example.my", "flow.yaml", "out"))
                (Path(d) / "shotfleet.toml").write_text('[ios]\napp = "My.app"\n[android]\napk = "a.apk"\n')
                self.assertEqual(sf.platforms_in(Path(d) / "shotfleet.toml"), ["ios", "android"])
                self.assertEqual(sf.load_config(Path(d) / "shotfleet.toml", "ios")[1]["out"], "out-ios")  # two platforms, two folders
                (Path(d) / "shotfleet.toml").write_text('[ios]\napp = "My.app"\nbundle_id = "wrong"\n')
                with self.assertRaisesRegex(sf.Fail, "bundle_id is wrong but My.app is com.example.my"):
                    sf.load_config(Path(d) / "shotfleet.toml")

    def test_unknown_keys_and_wrong_types_are_one_line_errors(self):
        with tempfile.TemporaryDirectory() as d:
            self.build(d)
            for body, msg in (('ipd = true\n', "unknown setting 'ipd'"), ('device_type = 3\n', "device_type .* should be a string"),
                              ('parallel = "four"\n', "parallel .* should be a whole number"), ('parallel = true\n', "parallel .* should be a whole number"),
                              ('locales = "de"\n', "locales .* should be a list")):
                (Path(d) / "shotfleet.toml").write_text('[ios]\napp = "My.app"\n' + body)
                with self.subTest(body=body), self.assertRaisesRegex(sf.Fail, msg):
                    sf.load_config(Path(d) / "shotfleet.toml")

    def test_run_goes_through_every_platform_in_the_file(self):
        seen = []
        with mock.patch.object(sf, "platforms_in", return_value=["ios", "android"]), \
             mock.patch.object(sf, "run_platform", side_effect=lambda c, o, p, plat: seen.append(plat) or (1 if plat == "android" else 0)):
            self.assertEqual(sf.cmd_run("x.toml"), 1)
            self.assertEqual(sf.cmd_run("x.toml", platform="ios"), 0)
        self.assertEqual(seen, ["ios", "android", "ios"])

    def test_init_takes_several_builds_into_one_small_config(self):
        with tempfile.TemporaryDirectory() as d:
            ios = self.build(d)
            with mock.patch.object(sf, "load_strings", return_value={"en": {"a": "A"}, "de": {"a": "B"}}):
                sf.cmd_init([str(ios)], d)
            toml = (Path(d) / "shotfleet.toml").read_text()
            self.assertEqual(tomllib.loads(toml)["ios"], {"app": "My.app"}); self.assertNotIn("bundle_id", toml)
            self.assertNotIn("appId:", (Path(d) / "flow.yaml").read_text().split("No appId needed")[0].replace("# ", ""))

    def test_init_refuses_two_builds_of_one_platform_and_creates_nothing(self):
        d = Path(tempfile.mkdtemp()) / "new"
        with self.assertRaisesRegex(sf.Fail, "two .app builds"): sf.cmd_init(["a.app", "b.app"], d)
        self.assertFalse(d.exists())


class JavaForMaestro(unittest.TestCase):
    def test_finds_a_keg_only_jdk_and_sets_its_home_for_maestro(self):
        sf.java_env.cache_clear()
        home = "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
        majors = {home + "/bin/java": 21}
        with mock.patch.dict(os.environ, {"PATH": "/usr/bin", "JAVA_HOME": ""}), \
             mock.patch.object(sf.shutil, "which", return_value=None), \
             mock.patch.object(sf, "java_major", side_effect=lambda j: majors.get(str(j), 0)), \
             mock.patch.object(sf.Path, "exists", return_value=False), mock.patch.object(sf.glob, "glob", return_value=[]):
            self.assertEqual(sf.find_java(), (True, home))
            sf.java_env.cache_clear()
            self.assertEqual(sf.java_env()["JAVA_HOME"], home); self.assertTrue(sf.java_env()["PATH"].startswith(home + "/bin:"))
        sf.java_env.cache_clear()

    def test_a_working_system_java_needs_nothing_set(self):
        sf.java_env.cache_clear()
        with mock.patch.dict(os.environ, {"JAVA_HOME": ""}), mock.patch.object(sf.shutil, "which", return_value="/usr/bin/java"), \
             mock.patch.object(sf, "java_major", return_value=17):
            self.assertEqual(sf.find_java(), (True, None)); self.assertEqual(sf.java_env(), {})
        sf.java_env.cache_clear()

    def test_no_java_is_reported(self):
        sf.java_env.cache_clear()
        with mock.patch.dict(os.environ, {"JAVA_HOME": ""}), mock.patch.object(sf.shutil, "which", return_value=None), \
             mock.patch.object(sf, "java_major", return_value=0), mock.patch.object(sf.Path, "exists", return_value=False), \
             mock.patch.object(sf.glob, "glob", return_value=[]):
            self.assertEqual(sf.find_java(), (False, None))
        sf.java_env.cache_clear()


class PolarLicence(unittest.TestCase):
    """Polar licence keys and the free tier (the other stores' tests are in the class above)."""
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp()); self.calls = []
        self.patches = [mock.patch.object(sf, "LICENCE_FILE", self.dir / "licence.json"),
                        mock.patch.object(sf.sys, "frozen", True, create=True), mock.patch.object(sf, "LOCALE_CAP", None),
                        mock.patch.object(sf, "polar_post", side_effect=self.fake)]
        for p in self.patches: p.start(); self.addCleanup(p.stop)

    def fake(self, action, **f):
        self.calls.append((action, f))
        if f["key"] == "SHOTFLEET-BAD": return 404, {"detail": "Resource not found"}
        return 200, {"id": "act-1"} if action == "activate" else {"status": "granted"}

    def test_polar_keys_are_told_apart_by_their_prefix(self):
        self.assertTrue(sf.is_polar_key(" shotfleet-1C285B2D-6CE6 ")); self.assertFalse(sf.is_polar_key("ABCDEF12-ABCDEF12-ABCDEF12-ABCDEF12"))

    def test_activate_validate_and_deactivate(self):
        self.assertEqual(sf.cmd_activate("SHOTFLEET-GOOD"), 0)
        self.assertEqual(json.loads(sf.LICENCE_FILE.read_text())["activation"], "act-1")
        sf.require_licence(); self.assertEqual([c[0] for c in self.calls], ["activate"])  # fresh: no network
        lic = json.loads(sf.LICENCE_FILE.read_text()); sf.LICENCE_FILE.write_text(json.dumps({**lic, "checked": time.time() - 8 * 86400}))
        sf.require_licence(); self.assertEqual(self.calls[-1], ("validate", {"key": "SHOTFLEET-GOOD", "activation_id": "act-1"}))
        sf.cmd_deactivate(); self.assertEqual(self.calls[-1][0], "deactivate"); self.assertFalse(sf.LICENCE_FILE.exists())

    def test_bad_key_is_refused_with_polars_reason(self):
        with self.assertRaisesRegex(sf.Fail, "didn't activate: Resource not found"): sf.cmd_activate("SHOTFLEET-BAD")

    def test_ci_key_validates_without_taking_an_activation(self):
        with mock.patch.dict(os.environ, {"SHOTFLEET_KEY": "SHOTFLEET-GOOD"}): sf.require_licence()
        self.assertEqual([c[0] for c in self.calls], ["validate"]); self.assertFalse(sf.LICENCE_FILE.exists())
        with mock.patch.dict(os.environ, {"SHOTFLEET_KEY": "SHOTFLEET-BAD"}), self.assertRaises(sf.NoLicence): sf.require_licence()

    def test_run_without_a_licence_is_the_free_tier_export_is_not(self):
        with mock.patch.object(sf, "cmd_run", return_value=0):
            self.assertEqual(sf.main(["run", "x.toml"]), 0); self.assertEqual(sf.LOCALE_CAP, 2)
        with mock.patch.object(sf, "LOCALE_CAP", None): self.assertEqual(sf.main(["export", "x", "--fastlane", "y"]), 2)
        with mock.patch.object(sf, "LOCALE_CAP", 2):
            self.assertEqual(sf.cap_locales(["de", "ja", "fr"]), ["de", "ja"]); self.assertEqual(sf.cap_locales(["de"]), ["de"])
        sf.LOCALE_CAP = None  # (main() set it above; the setUp patch restores it afterwards)
        self.assertEqual(sf.cap_locales(["de", "ja", "fr"]), ["de", "ja", "fr"])


if __name__ == "__main__":
    unittest.main()
