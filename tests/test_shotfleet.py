"""Tests for shotfleet's logic. No simulators, emulators or Maestro needed.

Run: python3 -m unittest discover -s tests
"""
import ast, contextlib, io, json, os, re, subprocess, sys, tempfile, threading, time, tomllib, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

needs_mac = unittest.skipUnless(sys.platform == "darwin", "needs macOS tools (PlistBuddy, swiftc, xcrun, BSD sed)")

# These tests describe the Mac and Apple-silicon behaviour (Vision, Homebrew, arm64 images); the same code on Linux is in
# test_portable.py. The patches last for this module only.
_MAC = [mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "SYSTEM_SDKS", ()),
        mock.patch.object(sf, "ABI", "arm64-v8a"), mock.patch.object(sf, "DEFAULT_IMAGE", "system-images;android-36;google_apis;arm64-v8a")]
def setUpModule():
    for p in _MAC: p.start()
def tearDownModule():
    for p in reversed(_MAC): p.stop()
MAC_READS = {"en", "de", "nl", "fr", "es", "it", "pt", "ru", "uk", "pl", "tr", "ja", "ko", "zh", "ar", "th", "hi"}  # a subset of what macOS reads

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

    def test_wildcard_around_a_known_label_is_kept_and_the_label_translated(self):
        # a Flutter row is one accessibility label "Title\nDetail"; `Start Training.*` and `.*Settings` are how a flow matches it
        out, missing, _ = sf.translate_flow('- tapOn: "Start Training.*"\n- tapOn: ".*Settings"\n- tapOn: "Nope.*"\n', EN, DE)
        self.assertIn("- tapOn: 'Training starten.*'", out)
        self.assertIn("- tapOn: '.*Einstellungen'", out)
        self.assertIn('- tapOn: "Nope.*"', out)
        self.assertEqual(missing, ["Nope"])

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

    def test_inline_launch_app_options_are_expanded_and_merged(self):
        flow = 'appId: x\n---\n- launchApp: { permissions: { all: allow }, arguments: { demo: "1" }, stopApp: false }  # one line\n'
        out = sf.localize_flow(flow, "de", Path("/o"))
        self.assertEqual(out.count("- launchApp"), 1)
        for line in ("    clearState: true", "    permissions:", "      all: allow", '      demo: "1"', '      AppleLanguages: "(de)"', "    stopApp: false"):
            self.assertIn(line + "\n", out)
        self.assertEqual(out.count("    arguments:"), 1)
        self.assertNotIn("{", out.split("\n---\n")[1])

    def test_launch_app_with_just_an_app_id_and_inline_arguments_in_a_block(self):
        out = sf.localize_flow("appId: x\n---\n- launchApp: com.example.app\n", "de", Path("/o"))
        self.assertIn("    appId: com.example.app\n", out)
        out = sf.localize_flow("appId: x\n---\n- launchApp:\n    arguments: { a: b, c: 'd e' }\n", "de", Path("/o"))
        self.assertIn("      a: b\n      c: 'd e'\n", out); self.assertIn('AppleLanguages: "(de)"', out)

    def test_inline_lists_and_broken_inline_options(self):
        self.assertEqual(sf.flow_mapping_lines("{ a: [x, y], b: {} }"), ["    a:", "      - x", "      - y", "    b: {}"])
        for bad in ("{ a: 1", "{ a 1 }", "{ a: 'open }", "{ a: 1 } trailing"):
            with self.assertRaises(ValueError, msg=bad): sf.flow_mapping_lines(bad)
        with self.assertRaisesRegex(ValueError, "as a block"):
            sf.localize_flow("appId: x\n---\n- launchApp:\n    arguments: nope\n", "de", Path("/o"))

    def test_system_dialog_buttons_keep_their_english_text(self):  # iOS draws them in the device language
        out, missing, _ = sf.translate_flow("appId: x\n---\n- tapOn: Allow\n- tapOn: \"Don't Allow\"\n",
                                            {"a": "Allow"}, {"a": "Erlauben"})
        self.assertIn("'(Allow|Erlauben)'", out); self.assertIn("'Don\u2019t Allow'", out); self.assertEqual(missing, [])  # curly, as iOS spells it

    def test_not_now_after_a_login_form_is_a_system_button_too(self):  # iOS's "Save Password?" sheet, seen in the Expo app
        out, missing, _ = sf.translate_flow("- tapOn: \"Not Now\"\n", {"a": "Settings"}, {"a": "Einstellungen"})
        self.assertEqual((missing, out), ([], '- tapOn: "Not Now"\n'))

    def test_flow_without_header_is_rejected_clearly(self):
        with self.assertRaisesRegex(ValueError, "appId"):
            sf.localize_flow("- tapOn: x\n", "de", Path("/o"))


class AndroidFlow(unittest.TestCase):
    def test_inline_launch_app_options_lose_clear_state_but_keep_the_rest(self):
        out = sf.android_flow("appId: x\n---\n- launchApp: { clearState: true, permissions: { all: allow } }\n- takeScreenshot: a\n",
                              "r1", Path("/o"))
        body = out.split("\n---\n")[1]
        self.assertNotIn("clearState", body)
        self.assertIn("- launchApp:\n    permissions:\n      all: allow\n", body)

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

    @mock.patch.object(sf, "readable_languages", lambda: MAC_READS)
    def test_blank_screen_fails(self):
        self.assertIn("no text", sf.judge_screen("de", {"chars": 0, "text": ""}, self.TABLES)[1])

    @mock.patch.object(sf, "readable_languages", lambda: MAC_READS)
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

    def test_map_form_path_after_other_keys_is_redirected(self):
        flow = "appId: x\n---\n- takeScreenshot:\n    cropOn: \"Card\"\n    path: 01_home\n- runFlow:\n    file: x.yaml\n    path: keep\n"
        out = sf.localize_flow(flow, "de", Path("/o/raw/de"))
        self.assertIn("    path: '/o/raw/de/01_home'", out)
        self.assertIn("    path: keep", out)  # not a screenshot's path

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
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "SDK", Path(d)), mock.patch.object(sf.shutil, "which", lambda *a, **k: None):
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
                ("[hooks]\n", "needs an [ios] or an [android] section"),
                ("[hook]\n", "unknown table [hook]; did you mean [hooks]"),
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

    @mock.patch.object(sf, "readable_languages", lambda: MAC_READS)
    def test_script_rescues_cjk_screens_detection_misreads(self):
        ocr = {"chars": 80, "text": "EMOM AMRAP\nTabataタイマー\n9:41\nワーク", "lang": "hr", "langs": {"hr": 0.2}}
        self.assertEqual(sf.judge_screen("ja", ocr, {"en": {"Start"}}), ("ja", None))
        ocr = {"chars": 80, "text": "Timer\nRounds\nWork", "lang": "en", "langs": {"en": 0.9}}
        self.assertIsNotNone(sf.judge_screen("ja", ocr, {"en": {"Start"}})[1])

    @mock.patch.object(sf, "readable_languages", lambda: MAC_READS)
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

    @mock.patch.object(sf, "readable_languages", lambda: MAC_READS)
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
        for name, words in (("x.ipa", "simulator .app"), ("x.aab", "assembleDebug"), ("x.zip", "no such file")):
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
    @needs_mac
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
                meta = {"product_id": "other" if body.get("license_key") == "OTHERPRODUCT" else "p1"}
                good = good or body.get("license_key") == "OTHERPRODUCT"
                reply = {"activate": {"activated": good, "instance": {"id": "inst1"}, "meta": meta, "error": None if good else "license_key not found"},
                         "validate": {"valid": good, "meta": meta, "error": None if good else "expired"},
                         "deactivate": {"deactivated": True}}[self.path.rsplit("/", 1)[-1]]
                self.send_response(200 if good or "deactivate" in self.path else 400); self.end_headers()
                self.wfile.write(json.dumps(reply).encode())
            def log_message(self, *a): pass
        self.server = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.dir = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(sf, "LICENCE_API", f"http://127.0.0.1:{self.server.server_port}/v1/licenses"),
                        mock.patch.object(sf, "LICENCE_FILE", self.dir / "licence.json"),
                        mock.patch.object(sf, "LS_PRODUCT_ID", "p1"),
                        mock.patch.object(sf.sys, "frozen", True, create=True)]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in self.patches: p.stop()
        self.server.shutdown()

    def test_a_key_from_another_lemon_squeezy_product_unlocks_nothing(self):
        with self.assertRaisesRegex(sf.Fail, "not a shotfleet licence"): self.quiet(sf.cmd_activate, "OTHERPRODUCT")
        self.assertFalse(sf.LICENCE_FILE.exists())
        with mock.patch.dict(os.environ, {"SHOTFLEET_KEY": "OTHERPRODUCT"}), self.assertRaisesRegex(sf.Fail, "SHOTFLEET_KEY"): sf.require_licence()
        with mock.patch.object(sf, "LS_PRODUCT_ID", ""), self.assertRaisesRegex(sf.Fail, "not a shotfleet licence"): self.quiet(sf.cmd_activate, "GOOD")  # none configured: nothing passes

    def test_a_licence_file_with_a_future_or_non_numeric_date_is_refused(self):
        for checked in (time.time() + 10 * 86400, 9999999999, "2099-01-01", None, True):
            with self.subTest(checked=checked):
                sf.LICENCE_FILE.write_text(json.dumps({"key": "GOOD", "instance": "x", "checked": checked}))
                with self.assertRaisesRegex(sf.Fail, "future|unreadable"): sf.require_licence()
        self.assertEqual(self.calls, [])  # refused locally, no network

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
    """Against a fake Gumroad /v2/licenses/verify (shape from Gumroad's licence-key help article and antiwork/gumroad licenses_controller.rb)."""
    GOOD, REFUNDED = "ABCDEF12-34567890-ABCDEF12-34567890", "11111111-22222222-33333333-44444444"

    def setUp(self):
        import http.server, threading, urllib.parse
        self.uses, self.calls, self.flags, self.status, test = {self.GOOD: 0, self.REFUNDED: 0}, [], {self.REFUNDED: {"refunded": True}}, 200, self
        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                b = dict(urllib.parse.parse_qsl(self.rfile.read(int(self.headers["Content-Length"])).decode()))
                test.calls.append(b)
                key = b.get("license_key")
                if test.status >= 500:
                    self.send_response(test.status); self.end_headers(); self.wfile.write(b'{"success":false,"message":"boom"}'); return
                if key not in test.uses or b.get("product_id") != "prod1":
                    self.send_response(404); self.end_headers()
                    self.wfile.write(b'{"success":false,"message":"That license does not exist for the provided product."}'); return
                if b.get("increment_uses_count") != "false": test.uses[key] += 1
                purchase = {"refunded": False, "chargebacked": False, "disputed": False, "dispute_won": False, **test.flags.get(key, {})}
                self.send_response(200); self.end_headers(); self.wfile.write(json.dumps({"success": True, "uses": test.uses[key], "purchase": purchase}).encode())
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

    def stale(self):  # make the weekly re-check due
        sf.LICENCE_FILE.write_text(json.dumps({**json.loads(sf.LICENCE_FILE.read_text()), "checked": time.time() - 8 * 86400}))

    def test_key_formats_do_not_collide(self):
        self.assertTrue(sf.is_gumroad_key(self.GOOD))
        self.assertFalse(sf.is_gumroad_key("38b1460a-5104-4067-a91d-77b872934d51"))  # Lemon Squeezy UUID
        self.assertFalse(sf.is_gumroad_key("SHOTFLEET-1C285B2D-6CE6"))  # Polar
        self.assertFalse(sf.is_polar_key(self.GOOD))

    def test_three_activations_then_refused_and_the_refusal_costs_nothing(self):
        for _ in range(3): self.activate(self.GOOD); sf.LICENCE_FILE.unlink()  # three different Macs
        with self.assertRaisesRegex(sf.Fail, "all 3 activations"): self.activate(self.GOOD)
        with self.assertRaisesRegex(sf.Fail, "hello@shotfleet.com"): self.activate(self.GOOD)
        self.assertEqual(self.uses[self.GOOD], 3)  # a refused attempt never burns a use
        self.assertFalse(sf.LICENCE_FILE.exists())

    def test_activating_again_on_the_same_mac_does_not_use_another(self):
        for _ in range(5): self.activate(self.GOOD)
        self.assertEqual(self.uses[self.GOOD], 1)

    def test_deactivate_cant_give_the_activation_back_and_says_so(self):
        self.activate(self.GOOD)
        with contextlib.redirect_stdout(io.StringIO()) as out: sf.cmd_deactivate()
        self.assertFalse(sf.LICENCE_FILE.exists()); self.assertIn("can't give the activation back", out.getvalue())
        self.assertEqual(len(self.calls), 2)  # activate's look and count; deactivate made no request

    def test_refunded_and_unknown_keys_are_refused_without_using_an_activation(self):
        with self.assertRaisesRegex(sf.Fail, "refunded"): self.activate(self.REFUNDED)
        with self.assertRaisesRegex(sf.Fail, "does not exist"): self.activate("99999999-99999999-99999999-99999999")
        self.assertEqual(self.uses[self.REFUNDED], 0)
        with self.assertRaisesRegex(sf.Fail, "Gumroad receipt"): self.activate(self.REFUNDED)

    def test_refunded_chargebacked_and_disputed_keys_stop_working_at_the_next_check(self):
        for flags, why in (({"refunded": True}, "refunded"), ({"chargebacked": True}, "charged back"), ({"disputed": True}, "disputed")):
            with self.subTest(flags=flags):
                self.flags[self.GOOD] = {}; self.activate(self.GOOD); self.stale()
                sf.require_licence()  # still fine
                self.flags[self.GOOD] = flags; self.stale()
                with self.assertRaisesRegex(sf.NoLicence, why): sf.require_licence()
                with mock.patch.dict(os.environ, {"SHOTFLEET_KEY": self.GOOD}), self.assertRaisesRegex(sf.NoLicence, why): sf.require_licence()
                sf.LICENCE_FILE.unlink()

    def test_a_won_dispute_keeps_the_licence(self):
        self.flags[self.GOOD] = {"disputed": True, "dispute_won": True}
        self.activate(self.GOOD); self.stale(); sf.require_licence()

    def test_nothing_counts_a_use_except_one_activation(self):
        self.activate(self.GOOD); self.stale(); sf.require_licence()
        with mock.patch.dict(os.environ, {"SHOTFLEET_KEY": self.GOOD}): sf.require_licence()
        self.assertTrue(all(set(c) == {"product_id", "license_key", "increment_uses_count"} for c in self.calls))  # nothing else is sent
        counted = [c for c in self.calls if c["increment_uses_count"] != "false"]
        self.assertEqual(len(counted), 1); self.assertEqual(self.uses[self.GOOD], 1)
        self.assertEqual(self.calls[-1]["increment_uses_count"], "false")

    def test_a_gumroad_outage_is_not_a_verdict(self):
        self.activate(self.GOOD); self.stale(); self.status = 503
        sf.require_licence()  # offline grace, the licence stays
        self.assertTrue(sf.LICENCE_FILE.exists())
        with self.assertRaises(OSError): sf.gumroad_verify(self.GOOD, count_use=False)

    def test_a_build_without_a_product_id_fails_loudly(self):
        with mock.patch.object(sf, "GUMROAD_PRODUCT_ID", ""), self.assertRaisesRegex(sf.Fail, "no Gumroad product id"): self.activate(self.GOOD)


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

    @needs_mac

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

    @needs_mac

    def test_checking_one_device_of_a_multi_device_run_leaves_the_ipad_rule_to_the_whole_run(self):
        class Stop(Exception): pass
        with tempfile.TemporaryDirectory() as d:
            out = self.make(d, {"iphone-17-pro-max": (1320, 2868)}, [1, 2])
            with mock.patch.object(sf, "store_rules", side_effect=lambda images, android, ipad, tablet=False: (_ for _ in ()).throw(Stop(ipad))), \
                 contextlib.redirect_stdout(io.StringIO()), self.assertRaises(Stop) as cm:
                sf.cmd_check(out / "iphone-17-pro-max")
            self.assertEqual(cm.exception.args, (False,))


class StuckOcrFallback(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.bin = self.d / "bin"; self.bin.mkdir()
        self.log = self.d / "calls.txt"
        (self.bin / "tesseract").write_text('#!/bin/sh\nif [ "$1" = --list-langs ]; then echo "List of available languages (3):"; '
                                            f'printf "eng\\ndeu\\njpn\\n"; exit 0; fi\necho "$@" >> {self.log}\ncat "$1.txt"\n')
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

    @needs_mac

    def test_stuck_macos_ocr_falls_back_to_tesseract(self):
        code, out, report = self.check()
        self.assertIn("using Tesseract instead", out)
        self.assertIn("-l eng+deu", self.log.read_text()); self.assertIn("-l eng+jpn", self.log.read_text())
        self.assertTrue(any(p.startswith("ja/1.png: shows en") for p in report["problems"]))  # still catches English
        self.assertFalse(any(p.startswith("de/") for p in report["problems"]))

    def test_tesseract_lines_with_several_labels_still_count(self):
        t = sf.string_tables({"de": {"a": "Alle", "b": "Übungen", "c": "Noch nichts eingetragen"},
                              "en": {"a": "All", "b": "Exercises", "c": "Nothing logged yet"}})
        ocr = {"chars": 60, "text": "All Exercises WODs\nNothing logged yet", "lang": None, "langs": {}, "ocr": "external"}
        got, problem = sf.judge_screen("de", ocr, t)
        self.assertEqual(got, "en"); self.assertIsNotNone(problem)

    @needs_mac

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

    @needs_mac

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


class FastlaneBothStores(unittest.TestCase):
    def test_check_with_a_build_picks_its_half_of_a_fastlane_folder_for_both_stores(self):
        root = Path(tempfile.mkdtemp())
        (root / "screenshots").mkdir(); (root / "metadata/android").mkdir(parents=True)
        app = root / "My.app"; app.mkdir(); (app / "Info.plist").write_bytes(b"x")
        seen = []
        def stop(folder, **kw): seen.append(Path(folder)); raise StopIteration
        with mock.patch.object(sf, "find_screenshots", side_effect=stop), mock.patch.object(sf, "load_strings", return_value={"en": {"a": "A"}, "de": {"a": "B"}}), \
             mock.patch.object(sf, "device_build", return_value=False), contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(StopIteration):
            sf.cmd_check(root, app=app)
        self.assertEqual(seen, [root / "screenshots"]); self.assertIn("checking the iOS ones", out.getvalue())

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


class Extending(unittest.TestCase):
    """The optional extension points: [hooks], [overrides.<locale>], plugins. Off unless the config asks."""
    def config(self, d, extra):
        app = Path(d) / "My.app"; app.mkdir(exist_ok=True)
        (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "com.x", "DTPlatformName": "iphonesimulator"}))
        (Path(d) / "flow.yaml").write_text("- launchApp\n")
        (Path(d) / "shotfleet.toml").write_text('[ios]\napp = "My.app"\n' + extra)
        return Path(d) / "shotfleet.toml"

    def load(self, d, extra):
        with mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"):
            return sf.load_config(self.config(d, extra))

    def test_override_wins_over_the_apps_strings_and_re_prefix_is_a_regex(self):
        flow = '- tapOn: "Next"\n- tapOn: "Advanced"\n- tapOn: "Search"\n'
        out, missing, clash = sf.translate_flow(flow, {"n": "Next", "a": "Advanced"}, {"n": "İleri", "a": "İleri"},
                                                [{"Next": "İleri", "Advanced": "re:Gelişmiş.*", "Search": "Ara"}])
        self.assertEqual(out, "- tapOn: 'İleri'\n- tapOn: 'Gelişmiş.*'\n- tapOn: 'Ara'\n")
        self.assertEqual((missing, clash), ([], []))  # no 'untranslated' or 'also means' warnings for overridden text

    def test_overrides_of_several_languages_in_one_android_round_are_or_ed(self):
        out, _, _ = sf.translate_flow('- tapOn: "Next"\n', {"n": "Next"}, [{"n": "Weiter"}, {"n": "Siguiente"}],
                                      [{"Next": "Weiter!"}, {"Next": "Sig."}])
        self.assertEqual(out, "- tapOn: '(Weiter!|Sig\\.)'\n")

    @needs_mac

    def test_config_tables_are_validated(self):
        with tempfile.TemporaryDirectory() as d:
            for body, msg in (('[hooks]\nafter_exprt = "x"\n', "unknown event 'after_exprt'; did you mean 'after_export'"),
                              ('[hooks]\nafter_run = 3\n', "after_run .* should be a command"),
                              ('[overrides.tr]\n"Next" = 3\n', "overrides.tr"),
                              ('[hook]\n', "did you mean \\[hooks\\]")):
                with self.subTest(body=body), self.assertRaisesRegex(sf.Fail, msg): self.load(d, body)
            platform, cfg, _ = self.load(d, '[hooks]\nafter_run = ["echo a", "echo b"]\n[overrides.tr]\n"Next" = "İleri"\n')
            self.assertEqual(cfg["_hooks"]["after_run"], ["echo a", "echo b"]); self.assertEqual(cfg["_overrides"], {"tr": {"Next": "İleri"}})

    def test_hooks_run_in_order_with_the_environment_and_stop_at_the_first_failure(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "log"
            hooks = {"after_run": [f'echo "$SHOTFLEET_EVENT $SHOTFLEET_PLATFORM $SHOTFLEET_EXIT" >> {log}', f"echo second >> {log}"]}
            self.assertEqual(sf.run_hook(hooks, "after_run", str(Path(d) / "shotfleet.toml"), {"SHOTFLEET_PLATFORM": "ios", "SHOTFLEET_EXIT": "0"}), (0, None))
            self.assertEqual(log.read_text(), "after_run ios 0\nsecond\n")
            self.assertEqual(sf.run_hook({"before_run": ["exit 3", "echo never"]}, "before_run", str(Path(d) / "x.toml"), {}), (3, "exit 3"))
            self.assertEqual(sf.run_hook({}, "before_run", "x", {}), (0, None))  # nothing configured: nothing runs

    @needs_mac

    def test_before_run_failure_aborts_after_run_failure_changes_the_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = self.config(d, '[hooks]\nbefore_run = "exit 5"\n')
            with mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), mock.patch.object(sf, "capture_platform") as cap:
                with self.assertRaisesRegex(sf.Fail, r"hook before_run failed \(exit 5\)"): sf.run_platform(cfg_path, None, None, "ios")
                cap.assert_not_called()
            cfg_path.write_text('[ios]\napp = "My.app"\n[hooks]\nafter_run = "exit 1"\n')
            with mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), mock.patch.object(sf, "capture_platform", return_value=0), \
                 contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sf.run_platform(cfg_path, None, None, "ios"), 1)

    @needs_mac

    def test_after_run_counts_problems_across_all_devices_of_a_multi_device_run(self):
        with tempfile.TemporaryDirectory() as d:
            for dev, n in (("phone", 2), ("tablet", 1)):
                (Path(d) / "out" / dev).mkdir(parents=True)
                (Path(d) / "out" / dev / "run.json").write_text("{}"); (Path(d) / "out" / dev / "check.json").write_text(json.dumps({"problems": ["p"] * n}))
            log = Path(d) / "log"
            cfg_path = self.config(d, f'[hooks]\nafter_run = "echo $SHOTFLEET_PROBLEMS > {log}"\n')
            with mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), mock.patch.object(sf, "capture_platform", return_value=0):
                sf.run_platform(cfg_path, None, None, "ios")
            self.assertEqual(log.read_text().strip(), "3")

    def test_no_hooks_flag_and_export_hooks(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"; (out / "raw/de").mkdir(parents=True); (out / "raw/de/01.png").write_bytes(png(1320, 2868))
            marker = Path(d) / "marker"
            cfg = Path(d) / "shotfleet.toml"; cfg.write_text(f'[hooks]\nafter_export = "echo $SHOTFLEET_FASTLANE >> {marker}"\nbefore_export = "exit 7"\n')
            (out / "run.json").write_text(json.dumps({"platform": "ios", "config": str(cfg), "locales": {"de": {"ok": True}}}))
            (out / "check.json").write_text(json.dumps({"problems": []}))
            with self.assertRaisesRegex(sf.Fail, r"before_export failed \(exit 7\)"): sf.export_with_hooks(out, Path(d) / "fl")
            cfg.write_text(f'[hooks]\nafter_export = "echo $SHOTFLEET_FASTLANE >> {marker}"\n')
            sf.export_with_hooks(out, Path(d) / "fl")
            self.assertEqual(marker.read_text().strip(), str((Path(d) / "fl").resolve()))
            marker.unlink()
            with mock.patch.object(sf, "NO_HOOKS", True): sf.export_with_hooks(out, Path(d) / "fl")
            self.assertFalse(marker.exists())

    def test_unknown_command_runs_a_shotfleet_plugin_from_the_path(self):
        with mock.patch.object(sf.shutil, "which", side_effect=lambda n: "/bin/shotfleet-foo" if n == "shotfleet-foo" else None), \
             mock.patch.object(sf.os, "execv", side_effect=SystemExit(0)) as ex:
            with self.assertRaises(SystemExit): sf.main(["foo", "--bar"])
        ex.assert_called_once_with("/bin/shotfleet-foo", ["/bin/shotfleet-foo", "--bar"])
        # built-in commands are never shadowed
        with mock.patch.object(sf.os, "execv") as ex3, mock.patch.object(sf.shutil, "which", return_value="/bin/shotfleet-run"), \
             mock.patch.object(sf, "main_cmd", return_value=0):
            sf.main(["run", "x.toml"]); ex3.assert_not_called()


class FrameworkFixes(unittest.TestCase):
    """Bugs found by reading real Flutter, React Native and gettext projects (research/frameworks.md)."""
    def files(self, spec):
        root = Path(tempfile.mkdtemp())
        for rel, text in spec.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text(text)
        return root

    def test_empty_accessibility_tree_falls_back_to_ocr_but_a_short_real_screen_does_not(self):
        d = Path(tempfile.mkdtemp()); png = d / "1.png"; png.write_bytes(png_c(10, 10))
        png.with_suffix(".texts.json").write_text("[]"); self.assertIsNone(sf.screen_text(png))
        png.with_suffix(".texts.json").write_text('["", "  "]'); self.assertIsNone(sf.screen_text(png))
        png.with_suffix(".texts.json").write_text('["Επόμενο"]'); self.assertEqual(sf.screen_text(png)["text"], "Επόμενο")

    def test_a_locale_folder_beats_a_short_namespace_file_name(self):
        self.assertEqual(sf.locale_from_path("locales/en/app.json"), "en")
        self.assertEqual(sf.locale_from_path("locales/pt-BR/ui.json"), "pt-BR")
        self.assertEqual(sf.locale_from_path("locales/de/translation.json"), "de")
        self.assertEqual(sf.locale_from_path("locales/de.json"), "de")          # unchanged: the stem is the language
        self.assertEqual(sf.locale_from_path("app/de.json"), "de")              # a folder called app is not a language

    def test_i18next_namespaces_that_share_a_key_both_survive(self):
        root = self.files({"locales/en/common.json": '{"title": "Home"}', "locales/en/settings.json": '{"title": "Settings"}',
                           "locales/de/common.json": '{"title": "Startseite"}', "locales/de/settings.json": '{"title": "Einstellungen"}'})
        s = sf.load_strings_files(str(root / "locales/*/*.json"))
        self.assertEqual(sorted(s), ["de", "en"])
        self.assertEqual(sorted(s["en"].values()), ["Home", "Settings"]); self.assertEqual(sorted(s["de"].values()), ["Einstellungen", "Startseite"])
        out, missing, _ = sf.translate_flow('- tapOn: "Settings"\n- tapOn: "Home"\n', s["en"], s["de"])
        self.assertEqual((out, missing), ("- tapOn: 'Einstellungen'\n- tapOn: 'Startseite'\n", []))

    PO = (b'msgid ""\nmsgstr ""\n"Language: de\\n"\n"Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n\n'
          b'msgid "Next"\nmsgstr "Weiter"\n\n'
          b'msgid "%d item"\nmsgid_plural "%d items"\nmsgstr[0] "%d Eintrag"\nmsgstr[1] "%d Eintr\xc3\xa4ge"\n')

    def test_po_uses_the_language_header_and_reads_plural_forms(self):
        root = Path(tempfile.mkdtemp()); (root / "messages.po").write_bytes(self.PO)   # no language in the path
        s = sf.read_translation_file(root / "messages.po", "en")
        self.assertEqual(s["de"]["Next"], "Weiter"); self.assertEqual(s["en"]["Next"], "Next")   # not stored as the base language
        self.assertEqual({s["de"]["%d item#0"], s["de"]["%d item#1"]}, {"%d Eintrag", "%d Einträge"})
        out, missing, _ = sf.translate_flow('- tapOn: "3 items"\n', s["en"], s["de"])
        self.assertEqual(missing, []); self.assertIn("3 Eintr", out)

    def test_partly_translated_languages_are_reported_not_dropped_silently(self):
        en = {f"k{i}": f"Text {i}" for i in range(10)}
        ja = {f"k{i}": "x" for i in range(3)}      # 30%: skipped by the 50% rule
        de = dict(en)
        strings = {"en": en, "de": de, "ja": ja}
        self.assertEqual(sf.partly_translated(strings, "en"), [("ja", 30)])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): sf.note_partly_translated(strings, "en")
        self.assertIn("ja is only 30% translated", buf.getvalue()); self.assertIn('locales = [..., "ja"]', buf.getvalue())
        self.assertEqual(sf.partly_translated({"en": en, "de": de}, "en"), [])


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


class AutoTesseract(unittest.TestCase):
    def run_check(self, packs):
        d = Path(tempfile.mkdtemp()); b = d / "bin"; b.mkdir()
        (b / "tesseract").write_text('#!/bin/sh\ncat "$1.txt"\n'); (b / "tesseract").chmod(0o755)
        png = d / "shots" / "el" / "1.png"; png.parent.mkdir(parents=True); png.write_bytes(png_c(1320, 2868))
        Path(f"{png}.txt").write_text("Επόμενο\nΡυθμίσεις\nΈναρξη προπόνησης")
        strings = {"en": {"a": "Next", "b": "Settings", "c": "Start Training"},
                   "el": {"a": "Επόμενο", "b": "Ρυθμίσεις", "c": "Έναρξη προπόνησης"}}
        garbage = {"text": "Enouevo\nPuoniceic", "chars": 20, "lang": "hu", "langs": {"hu": 0.4}}  # macOS can't read Greek
        sf.tesseract_languages.cache_clear()
        with mock.patch.object(sf, "warm_up_ocr", return_value=True), mock.patch.object(sf, "read_text", return_value=garbage), \
             mock.patch.object(sf, "tesseract_languages", return_value=frozenset(packs)), \
             mock.patch.dict(os.environ, {"PATH": f"{b}:{os.environ['PATH']}"}), contextlib.redirect_stdout(io.StringIO()):
            sf.cmd_check(d / "shots", strings=strings, report_dir=d / "rep")
        return json.loads((d / "rep/check.json").read_text())["screenshots"][0]["lang"]

    @needs_mac

    def test_installed_tesseract_verifies_scripts_macos_cant_read(self):
        self.assertEqual(self.run_check({"eng", "ell"}), "el")   # read and verified

    @needs_mac

    def test_missing_language_pack_leaves_it_unverified_not_broken(self):
        self.assertIsNone(self.run_check({"eng"}))               # no Greek data: "couldn't read", no crash


class PlayDeviceFolders(unittest.TestCase):
    def test_phone_and_tablet_sets_are_found_separately(self):
        with tempfile.TemporaryDirectory() as d:
            for kind, size in (("phoneScreenshots", (1080, 1920)), ("tenInchScreenshots", (1440, 2560))):
                f = Path(d) / "metadata/android/de-DE/images" / kind; f.mkdir(parents=True)
                (f / "1.png").write_bytes(png_c(*size))
            self.assertEqual(sf.play_folders(d), ["phoneScreenshots", "tenInchScreenshots"])
            phone = sf.find_screenshots(d)
            tablet = sf.find_screenshots(d, play_folder="tenInchScreenshots")
            self.assertEqual(sf.image_info(phone["de-DE"][0])[0], (1080, 1920))
            self.assertEqual(sf.image_info(tablet["de-DE"][0])[0], (1440, 2560))


class Review20261003(unittest.TestCase):
    def test_tesseract_script_detection_flags_another_script_only_when_confident(self):
        # a Japanese screen in the Korean listing: Tesseract (-l eng+kor) reads Latin gibberish but its script detection says Japanese
        tables = sf.string_tables({"ko": {"a": "다음"}, "ja": {"a": "次へ"}, "en": {"a": "Next"}})
        scr = lambda s, c: {"text": "x ya", "chars": 4, "lang": None, "langs": {}, "ocr": "external", "lines": [], "osd_script": s, "osd_conf": c}
        with mock.patch.object(sf, "readable_languages", return_value={"ko", "ja", "en"}):
            lp, problem = sf.judge_screen("ko", scr("Japanese", 1.51), tables)
            self.assertIn("Japanese script, expected 'ko'", problem)
            self.assertEqual(sf.judge_screen("ko", scr("Japanese", 0.06), tables), ("ko", None))  # weak: Korean read as Japanese
            self.assertEqual(sf.judge_screen("ko", scr("Korean", 3.0), tables), ("ko", None))
            self.assertEqual(sf.judge_screen("ja", scr("Han", 2.0), tables), ("ja", None))  # kanji-heavy Japanese
            self.assertEqual(sf.judge_screen("ja", scr("Korean", 2.0), tables)[0], None)
        r = sf.tesseract_script("x.png", "de"); self.assertEqual(r, {})  # only ja, ko, th are asked
    def test_a_slow_warm_up_times_out_but_keeps_running_so_a_first_compile_can_finish(self):
        with tempfile.TemporaryDirectory() as d:
            done, ocr = Path(d) / "done", Path(d) / "ocr"
            ocr.write_text(f'#!/bin/sh\nsleep 2; touch {done}; echo Ready\n'); ocr.chmod(0o755)
            t = time.time()
            self.assertFalse(sf.warm_up_ocr(str(ocr), timeout=0.5))
            self.assertLess(time.time() - t, 1.5)
            for _ in range(50):
                if done.exists(): break
                time.sleep(0.1)
            self.assertTrue(done.exists())  # not killed
            self.assertTrue(sf.warm_up_ocr(str(ocr), timeout=10))

    def test_a_text_placeholder_with_one_word_around_it_is_not_evidence(self):
        # pt "%@ atrás" matched Spanish "Cuenta atrás", so a real Spanish screen was reported as Portuguese
        t = sf.string_tables({"es": {"a": "Cuenta atrás", "b": "Progreso"}, "pt": {"a": "Contagem regressiva", "b": "%@ atrás", "c": "Último: %d dias atrás"}})
        self.assertFalse(t["pt"].formats.match("una cuenta atras"))
        self.assertTrue(t["pt"].formats.match("ultimo: 3 dias atras"))  # numbers keep the shorter rule

    def test_tesseract_value_inside_a_longer_word_is_not_a_match(self):
        t = sf.string_tables({"en": {"a": "Start", "b": "History", "c": "Settings"},
                              "de": {"a": "Starten", "b": "Verlauf", "c": "Einstellungen"}})
        r = {"text": "Starten\nVerlauf", "chars": 15, "lang": None, "langs": {}, "ocr": "external"}
        with mock.patch.object(sf, "readable_languages", return_value={"en", "de"}):
            self.assertEqual(sf.judge_screen("en", r, t)[0], "de")

    def test_unusable_app_text_falls_back_to_ocr(self):
        with tempfile.TemporaryDirectory() as d:
            png = Path(d) / "1.png"; f = png.with_suffix(".texts.json")
            f.write_text("[]"); self.assertIsNone(sf.screen_text(png))        # empty tree
            f.write_text('["Welcome'); self.assertIsNone(sf.screen_text(png))  # half-written
            t = sf.string_tables({"de": {"a": "Weiter", "b": "Zurück"}})
            f.write_text(json.dumps(["Hi Sam", "Weiter"])); self.assertIsNone(sf.usable_text(png, t))  # 1 line proves nothing
            f.write_text(json.dumps(["Hi Sam", "Weiter", "Zurück"])); self.assertIsNotNone(sf.usable_text(png, t))

    def test_reader_survives_bad_trees_and_rereads_rewritten_screenshots(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); (d / "dbg").mkdir(); (d / "raw/de").mkdir(parents=True)
            (d / "dbg/maestro.log").write_text("Selected device X using port 7001 with execution plan ExecutionPlan(flowsToRun=[/f/de.yaml]")
            png = d / "raw/de/1.png"; png.write_bytes(b"x")
            calls = []
            def fake(port, bundle):
                calls.append(port)
                if len(calls) == 1: raise AttributeError("tree is a list")
                return ["Weiter", f"read {len(calls)}"]
            stop = threading.Event()
            with mock.patch.object(sf, "ios_screen_texts", fake):
                th = threading.Thread(target=sf.capture_texts, args=(stop, d / "dbg", d / "raw", "b")); th.start()
                png2 = d / "raw/de/2.png"; time.sleep(0.5); png2.write_bytes(b"y")  # reader lived through the first error
                for _ in range(50):
                    if png2.with_suffix(".texts.json").exists(): break
                    time.sleep(0.1)
                self.assertTrue(png2.with_suffix(".texts.json").exists())
                os.utime(png2, (1, 1))  # same path rewritten: read again
                n = len(calls); time.sleep(0.6); stop.set(); th.join(5)
            self.assertGreater(len(calls), n)
            self.assertFalse(list((d / "raw/de").glob("*.tmp")))

    def test_pause_goes_after_the_whole_map_form_screenshot_step(self):
        flow = "appId: x\n---\n- takeScreenshot:\n    cropOn:\n      text: a\n    path: s\n- tapOn: Next\n"
        out = sf.localize_flow(flow, "de", Path("/s")).splitlines()
        i = out.index("    path: '/s/s'")
        self.assertEqual(out[i + 1], "- extendedWaitUntil:")
        self.assertEqual(sum("__shotfleet_reading_screen__" in l for l in out), 1)

    def test_pool_cleanup_only_deletes_its_own_numbered_names(self):
        sims = [{"name": n, "udid": n, "isAvailable": True, "deviceTypeIdentifier": "T"}
                for n in ("shotfleet-iphone-17-pro-max-1", "shotfleet-iphone-17-2", "shotfleet-iphone-17-1")]
        calls = []
        def fake(cmd, **kw):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, json.dumps({"devices": {"rt": sims}}) if "-j" in cmd else "NEW", "")
        with mock.patch.object(sf, "sh", fake), mock.patch.object(sf.Sim, "run", return_value=""):
            sf.make_pool(1, "T2", "rt", "shotfleet-iphone-17")
        self.assertEqual([c[-1] for c in calls if "delete" in c], ["shotfleet-iphone-17-2", "shotfleet-iphone-17-1"])

    def test_ios_run_shuts_its_simulators_down_even_when_it_fails(self):
        calls = []
        sf.OUR_SIMS.add("U1")
        with mock.patch.object(sf, "ios_run_inner", side_effect=sf.Fail("x")), \
             mock.patch.object(sf, "sh", lambda cmd, **kw: calls.append(cmd)):
            with self.assertRaises(sf.Fail): sf.ios_run({}, None)
        self.assertEqual(calls, [["xcrun", "simctl", "shutdown", "U1"]]); self.assertFalse(sf.OUR_SIMS)

    @needs_mac

    def test_new_multi_device_run_hides_an_old_single_run_and_export_needs_the_ipad_set(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"; (out / "raw/de").mkdir(parents=True)
            (out / "run.json").write_text("{}"); (out / "check.json").write_text("{}")
            sf.clear_single_run(out)
            self.assertEqual([p.name for p in out.iterdir()], [])
        with tempfile.TemporaryDirectory() as d:
            out = MultiDevice().make(d, {"iphone-17-pro-max": (1320, 2868)}, [1, 2])
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(sf.Fail, "13\" iPad"):
                sf.cmd_export(out, Path(d) / "fl")

    @needs_mac

    def test_check_passes_report_dir_to_each_device(self):
        with tempfile.TemporaryDirectory() as d:
            out = MultiDevice().make(d, {"a": (1320, 2868), "b": (2064, 2752)}, [1])
            with mock.patch.object(sf, "cmd_check", return_value=0) as c, mock.patch.object(sf, "ipad_set_missing", return_value=0):
                sf.check_any(out, report=Path(d) / "rep")
            self.assertEqual(sorted(k.kwargs["report_dir"].name for k in c.call_args_list), ["a", "b"])

    @needs_mac

    def test_tablet_only_play_folder_is_checked_with_play_rules(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "supply/de-DE/images/tenInchScreenshots"; f.mkdir(parents=True)
            (f / "1.png").write_bytes(png_c(1440, 2560))
            with mock.patch.object(sf, "warm_up_ocr", return_value=True), \
                 mock.patch.object(sf, "read_text", return_value={"text": "Hallo", "chars": 5, "lang": "de", "langs": {"de": 1}}), \
                 contextlib.redirect_stdout(io.StringIO()) as out:
                sf.cmd_check(Path(d) / "supply", report_dir=Path(d) / "rep", play_folder="tenInchScreenshots")
        self.assertNotIn("App Store", out.getvalue())

    def test_nested_launch_app_keeps_its_indent(self):
        flow = ("appId: a\n---\n- launchApp\n- runFlow:\n    commands:\n      - launchApp:\n          arguments:\n"
                "            foo: bar\n      - tapOn: Y\n- tapOn: Z\n")
        body = sf.localize_flow(flow, "de", Path("/s")).split("\n---\n")[1].splitlines()
        i = body.index("      - launchApp:")
        self.assertEqual(body[i - 2:i], ["- runFlow:", "    commands:"])
        self.assertEqual(body[i + 1], "          arguments:")
        self.assertTrue(all(l.startswith("          ") for l in body[i + 1:i + 5]))
        self.assertEqual(body[i + 5:], ["      - tapOn: Y", "- tapOn: Z"])

    def test_bad_mcp_call_returns_an_error_and_clears_the_last_report(self):
        sf.LAST_REPORT = Path("/stale/check.json")
        text, err = sf.mcp_call("check", {})
        self.assertTrue(err); self.assertIn("KeyError", text); self.assertIsNone(sf.LAST_REPORT)

    def test_ocr_command_errors_and_tesseract_listing(self):
        with self.assertRaisesRegex(sf.Fail, r"unknown placeholder.*\{tesseract_with_english\}"):
            sf.external_ocr("tool {imag}", Path("a.png"), "de")
        r = subprocess.CompletedProcess([], 0, "", "List of available languages (2):\neng\ndeu\n")
        sf.tesseract_languages.cache_clear()
        with mock.patch.object(sf.shutil, "which", return_value="/x"), mock.patch.object(sf, "sh", return_value=r):
            self.assertEqual(sf.tesseract_languages(), {"eng", "deu"})
        sf.tesseract_languages.cache_clear()

    @needs_mac

    def test_macos_ocr_hanging_mid_check_switches_to_tesseract(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); png = d / "shots/de/1.png"; png.parent.mkdir(parents=True); png.write_bytes(png_c(1320, 2868))
            ext = {"text": "Weiter\nZurück", "chars": 13, "lang": None, "langs": {}, "ocr": "external"}
            with mock.patch.object(sf, "warm_up_ocr", return_value=True), \
                 mock.patch.object(sf, "read_text", side_effect=RuntimeError("hung twice")), \
                 mock.patch.object(sf, "external_ocr", return_value=ext) as e, \
                 mock.patch.object(sf, "tesseract_languages", return_value=frozenset({"eng", "deu"})), \
                 mock.patch.object(sf.shutil, "which", return_value="/x"), contextlib.redirect_stdout(io.StringIO()):
                sf.cmd_check(d / "shots", strings={"de": {"a": "Weiter", "b": "Zurück"}, "en": {"a": "Next", "b": "Back"}},
                             report_dir=d / "rep")
            self.assertEqual(e.call_count, 1)


if __name__ == "__main__":
    unittest.main()


class ReviewGrid(unittest.TestCase):
    def test_each_flagged_cell_names_its_problem_and_images_outside_the_report_keep_working(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); rep = d / "rep"; rep.mkdir(); (d / "shots" / "de").mkdir(parents=True)
            (d / "shots" / "de" / "01.png").write_bytes(b"x")
            rows = [{"file": "de/01.png", "src": "../shots/de/01.png"}, {"file": "fr/01.png", "src": "../shots/de/01.png"}]
            sf.write_gallery(rep, rows, ["de/01.png: shows en (expected de)", "identical image in 2 languages: de/01.png, fr/01.png"])
            page = (rep / "index.html").read_text()
        self.assertIn("shows en (expected de)", page)
        self.assertEqual(page.count("<small>"), 2)  # one visible note per flagged cell
        self.assertIn("file://", page)              # the report can be moved; the screenshots stay where they are
        self.assertNotIn('src="../shots', page)


class FrameworkHints(unittest.TestCase):
    """Flutter, React Native and the like keep their translations in compiled code: tell the user the `strings =` line to add."""
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp()); self.addCleanup(__import__("shutil").rmtree, self.dir, True)
        p = mock.patch.object(sf, "HINTED", set()); p.start(); self.addCleanup(p.stop)

    def app(self, name, files):
        app = self.dir / name; app.mkdir()
        (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "com.example." + name[:-4], "DTPlatformName": "iphonesimulator"}))
        for f in files: (app / f).parent.mkdir(parents=True, exist_ok=True); (app / f).write_bytes(b"x")
        return app

    def hints(self, build, strings_set=False):
        err = io.StringIO()
        with contextlib.redirect_stderr(err): sf.framework_hint(build, strings_set, self.dir)
        return [l for l in err.getvalue().splitlines()]

    def flutter(self): return self.app("flutter.app", ["Frameworks/App.framework/flutter_assets/kernel_blob.bin", "Frameworks/Flutter.framework/Flutter"])
    def rn(self): return self.app("rn.app", ["Frameworks/hermes.framework/hermes", "RCTI18nStrings.bundle/en.lproj/x"])
    def native(self): return self.app("native.app", ["en.lproj/Localizable.strings", "de.lproj/Localizable.strings"])

    def test_flutter_build_gets_the_strings_line_and_the_debug_banner_warning(self):
        got = self.hints(self.flutter())
        self.assertEqual(len(got), 2); self.assertTrue(all(l.startswith("hint: ") for l in got))
        self.assertIn('strings = "lib/l10n/*.arb"', got[0]); self.assertIn("DEBUG banner", got[1])

    def test_flutter_apk_is_recognised_too_and_a_release_build_has_no_banner_warning(self):
        import zipfile
        apk = self.dir / "app.apk"
        with zipfile.ZipFile(apk, "w") as z: z.writestr("lib/arm64-v8a/libflutter.so", "x"); z.writestr("assets/flutter_assets/AssetManifest.json", "{}")
        got = self.hints(apk)
        self.assertEqual(len(got), 1); self.assertIn('strings = "lib/l10n/*.arb"', got[0])

    def test_react_native_debug_build_is_told_to_add_strings_and_to_build_release(self):
        got = self.hints(self.rn())
        self.assertIn('strings = "src/locales/*/translation.json"', got[0]); self.assertIn("Metro", got[1]); self.assertIn("Release", got[1])
        self.assertEqual(self.hints(self.app("rel.app", ["main.jsbundle"]), strings_set=True), [])  # Release with strings set: nothing to say

    def test_the_line_names_the_translation_files_found_in_the_project(self):
        (self.dir / "src/translations").mkdir(parents=True); (self.dir / "src/translations/en.json").write_text("{}")
        self.assertIn('strings = "src/translations/*.json"', self.hints(self.rn())[0])

    def test_a_native_ios_build_gets_no_hint(self):
        self.assertEqual(self.hints(self.native()), [])

    def test_each_hint_is_shown_once_and_strings_in_the_config_silences_the_strings_hint(self):
        flutter = self.flutter()
        self.assertEqual(len(self.hints(flutter)), 2); self.assertEqual(self.hints(flutter), [])
        sf.HINTED.clear(); got = self.hints(flutter, strings_set=True)
        self.assertEqual(len(got), 1); self.assertIn("DEBUG banner", got[0])

    def test_init_prints_the_strings_line_for_a_flutter_build_and_stays_quiet_for_a_native_one(self):
        for build, expect in ((self.flutter(), 'strings = "lib/l10n/*.arb"'), (self.native(), None)):
            sf.HINTED.clear(); err, out = io.StringIO(), io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                self.assertEqual(sf.cmd_init(str(build), self.dir / build.stem), 0)
            if expect: self.assertIn(expect, err.getvalue()); self.assertIn("hint: ", err.getvalue())
            else: self.assertNotIn("hint:", err.getvalue())
            self.assertIn("languages", out.getvalue())

    @needs_mac

    def test_run_and_check_show_the_hint_before_they_can_fail(self):
        flutter = self.flutter()
        (self.dir / "shotfleet.toml").write_text(f'[ios]\napp = "{flutter}"\n'); (self.dir / "flow.yaml").write_text("- launchApp\n")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), mock.patch.object(sf, "latest_ios_runtime", return_value="rt"), \
             mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), \
             self.assertRaises(sf.Fail):  # no translations in the stub, so the run stops; the hint came first
            sf.cmd_run(str(self.dir / "shotfleet.toml"))
        self.assertIn('strings = "lib/l10n/*.arb"', err.getvalue())
        sf.HINTED.clear(); err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaisesRegex(sf.Fail, "no translations"):
            sf.cmd_check(self.dir / "out", app=flutter)
        self.assertIn('strings = "lib/l10n/*.arb"', err.getvalue())


class RetryOnSlowSimulator(unittest.TestCase):
    """iPad run on a loaded Mac: Maestro's clearState timed out between uninstall and reinstall, the app was gone,
    and the retry failed in 2 s per language with 'Unknown error' because nothing reinstalled it."""
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        app = self.d / "My.app"
        for lp, word in (("en", "Next"), ("de", "Weiter")):
            (app / f"{lp}.lproj").mkdir(parents=True)
            (app / f"{lp}.lproj" / "Localizable.strings").write_text(f'"next" = "{word}";\n')
        (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "x.y", "CFBundleLocalizations": ["en", "de"]}))
        (self.d / "flow.yaml").write_text('- launchApp\n- takeScreenshot: 01\n')
        (self.d / "shotfleet.toml").write_text('[ios]\napp = "My.app"\nlocales = ["de"]\n')
        self.calls, self.runs = [], 0

    def fake_sim(self):
        calls = self.calls
        class S:
            udid = "U1"
            def run(self, *a, check=True): calls.append(a[0]); return ""
        return S()

    def fake_maestro(self, cmd, env=None, timeout=None):
        self.runs += 1
        flows = Path(cmd[cmd.index("test") + 1]); out = flows.parent.parent.parent
        ok = self.runs == 2 and self.calls[-1] == "install"  # the retry only works when the app was reinstalled just before
        if ok: (out / "raw" / "de" / "01.png").write_bytes(b"x")
        Path(cmd[cmd.index("--output") + 1]).write_text(
            f'<testsuites><testsuite><testcase name="de" time="2">{"" if ok else "<failure>Unknown error</failure>"}</testcase></testsuite></testsuites>')
        return subprocess.CompletedProcess(cmd, 0 if ok else 1, "", "")

    def run_it(self, level, check=None):
        real = sf.sh
        def sh(cmd, **kw): return subprocess.CompletedProcess(cmd, 0, level, "") if cmd[0] == "sysctl" else real(cmd, **kw)
        with mock.patch.object(sf, "make_pool", return_value=[self.fake_sim()]), mock.patch.object(sf, "run_guarded", self.fake_maestro), \
             mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), \
             mock.patch.object(sf, "latest_ios_runtime", return_value="com.apple.CoreSimulator.SimRuntime.iOS-27-0"), \
             mock.patch.object(sf, "kill_stale_drivers"), mock.patch.object(sf, "cmd_check", side_effect=check or (lambda *a, **k: 0)), \
             mock.patch.object(sf, "java_env", return_value={}), mock.patch.object(sf, "sh", sh), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            code = sf.cmd_run(str(self.d / "shotfleet.toml"))
        return code, out.getvalue()

    @needs_mac

    def test_retry_reinstalls_the_app_first(self):
        code, out = self.run_it("1")
        self.assertEqual(self.calls.count("install"), 2)  # once before the run, once before the retry
        self.assertEqual(code, 0, out)
        self.assertIn("retrying 1: de", out)

    def test_overload_note_only_when_the_mac_was_loaded(self):
        with mock.patch.object(sf, "sh", lambda c, **k: subprocess.CompletedProcess(c, 0, "2", "")):
            self.assertIn("used 1 simulators instead of 2", sf.overload_note(2, 1))
            self.assertIn("short of memory", sf.overload_note(1, 1))
        with mock.patch.object(sf, "sh", lambda c, **k: subprocess.CompletedProcess(c, 0, "1", "")):
            self.assertEqual(sf.overload_note(2, 2), "")


class TypedTextPerLanguage(unittest.TestCase):
    FLOW = "appId: x\n---\n- launchApp\n- tapOn: Next\n- inputText: ${name}\n- takeScreenshot: 01\n"

    def test_the_localized_flow_carries_that_languages_text_in_its_header(self):
        inputs = {"name": "Alex", "ja": {"name": "田中"}, "pt": {"name": "Ana"}}
        ja = sf.localize_flow(self.FLOW, "ja", Path("/o"), sf.inputs_for(inputs, "ja")).split("\n---\n")[0]
        self.assertIn('env:\n  name: "田中"', ja)
        de = sf.localize_flow(self.FLOW, "de", Path("/o"), sf.inputs_for(inputs, "de")).split("\n---\n")[0]
        self.assertIn('name: "Alex"', de)                       # no German value: the default
        self.assertEqual(sf.inputs_for(inputs, "pt-BR"), {"name": "Ana"})  # the language part matches a region

    def test_an_env_block_the_user_wrote_is_extended_not_duplicated(self):
        flow = "appId: x\nenv:\n  mode: fast\n---\n- launchApp\n"
        header = sf.localize_flow(flow, "ja", Path("/o"), {"name": "田中"}).split("\n---\n")[0]
        self.assertEqual(header.count("env:"), 1)
        self.assertIn("mode: fast", header); self.assertIn('name: "田中"', header)

    def test_quotes_and_colons_in_the_text_stay_one_yaml_string(self):
        header = sf.with_env("appId: x", {"q": 'say "hi": #1'})
        self.assertIn('q: "say \\"hi\\": #1"', header)

    def test_a_flow_without_inputs_is_unchanged(self):
        self.assertEqual(sf.localize_flow(self.FLOW, "de", Path("/o"), {}), sf.localize_flow(self.FLOW, "de", Path("/o")))

    def test_the_config_checker_refuses_non_text_and_bad_names(self):
        sf.check_tables({"ios": {}, "inputs": {"name": "a", "ja": {"name": "田中"}}}, "t.toml")
        for bad in ({"inputs": {"name": 3}}, {"inputs": {"ja": {"na me": "x"}}}, {"inputs": {"ja": {"name": 1}}}):
            with self.assertRaises(sf.Fail): sf.check_tables(bad, "t.toml")

    def test_android_flows_get_the_defaults_only(self):
        text = sf.android_flow(self.FLOW, "f0", Path("/o"), sf.inputs_for({"name": "Alex", "ja": {"name": "田中"}}, "", defaults_only=True))
        self.assertIn('name: "Alex"', text); self.assertNotIn("田中", text)


class CorruptLicenceFile(unittest.TestCase):
    """A half-written licence.json (a crash, a full disk) must never crash a command or lock the user out of the free tier."""
    BAD = ("", "{", '{"key": "ABC', "[]", '"text"', "null", "{}", '{"key": ""}')

    def run_with(self, content):
        d = Path(tempfile.mkdtemp()); f = d / "licence.json"; f.write_text(content)
        return mock.patch.object(sf, "LICENCE_FILE", f), f

    def test_every_command_survives_an_unreadable_file(self):
        for content in self.BAD:
            patch, f = self.run_with(content)
            with patch, mock.patch.object(sys, "frozen", True, create=True), mock.patch.dict(os.environ, {}, clear=False):  # the gate only applies to released builds
                os.environ.pop("SHOTFLEET_KEY", None)
                self.assertIsNone(sf.read_licence(), content)
                with self.assertRaises(sf.NoLicence) as cm: sf.require_licence()   # export is refused, with a way out
                self.assertIn("activate again", str(cm.exception))
                sf.LOCALE_CAP = None
                with contextlib.redirect_stderr(io.StringIO()): sf.apply_free_tier()
                self.assertEqual(sf.LOCALE_CAP, sf.FREE_LANGUAGES, content)         # run falls back to the free tier
                sf.LOCALE_CAP = None
                out = io.StringIO()
                with contextlib.redirect_stdout(out): self.assertEqual(sf.cmd_deactivate(), 0)
                self.assertFalse(f.exists(), content)                                 # the broken file is removed
                self.assertIn("unreadable", out.getvalue())

    def test_a_good_file_still_reads(self):
        patch, _ = self.run_with(json.dumps({"key": "K", "store": "gumroad", "checked": 1}))
        with patch: self.assertEqual(sf.read_licence()["key"], "K")


def shots_with_texts(d, spec, ocr=False):
    """{label: {name: [lines]}} as screenshot folders: .texts.json (the app's own text, iOS) or <name>.png.txt (read by a fake OCR)."""
    for label, screens in spec.items():
        for name, lines in screens.items():
            png = Path(d) / "shots" / label / f"{name}.png"; png.parent.mkdir(parents=True, exist_ok=True); png.write_bytes(png_c(1320, 2868))
            if ocr: Path(f"{png}.txt").write_text("\n".join(lines))
            else: png.with_suffix(".texts.json").write_text(json.dumps(lines, ensure_ascii=False))


class ContentExpect(unittest.TestCase):
    """[expect.<screenshot>] any / all / not, per language: proves the seeded content is on screen. No device needed."""
    STRINGS = {"en": {"a": "Next", "b": "Settings"}, "de": {"a": "Weiter", "b": "Einstellungen"}}
    HOME = {"en": ["Next", "Settings", "Senior iOS Engineer"], "de": ["Weiter", "Einstellungen", "Senior iOS Engineer", "Steinmännchen"]}

    def check(self, expect, spec, ocr=False, readable=("en", "de")):
        d = tempfile.mkdtemp(); shots_with_texts(d, spec, ocr)
        fake = lambda _ocr, png, timeout=120: (lambda t: {"text": t, "chars": len(t), "lang": "en", "langs": {"en": 0.9}})(Path(f"{png}.txt").read_text())
        with mock.patch.object(sf, "warm_up_ocr", return_value=True), mock.patch.object(sf, "ocr_tool", return_value="ocr"), \
             mock.patch.object(sf, "read_text", fake), mock.patch.object(sf, "readable_languages", return_value=set(readable)), \
             contextlib.redirect_stdout(io.StringIO()):
            code = sf.cmd_check(Path(d) / "shots", strings=self.STRINGS, report_dir=Path(d) / "rep", expect=expect)
        report = json.loads((Path(d) / "rep/check.json").read_text())
        return code, report

    def test_the_apps_own_text_is_exact_and_matched_like_judge_screen(self):
        expect = {"01_home": {"any": ["senior ios  ENGINEER"], "not": ["No workouts yet", "Keine Workouts"], "de": {"all": ["Steinmännchen"]}}}
        code, report = self.check(expect, {lp: {"01_home": t} for lp, t in self.HOME.items()})
        self.assertEqual((code, report["problems"], report["notes"]), (0, [], []))  # case and spacing are folded; the de rule only applies to de

    def test_a_missing_string_and_an_empty_state_are_each_one_problem_line_with_the_screen(self):
        expect = {"01_home": {"all": ["Steinmännchen"], "not": ["Settings"]}}
        code, report = self.check(expect, {lp: {"01_home": t} for lp, t in self.HOME.items()})
        self.assertEqual(code, 1)
        self.assertEqual(sorted(report["problems"]), [
            'en/01_home.png: "Settings" must not be on screen', 'en/01_home.png: expected "Steinmännchen" on screen'])

    def test_any_needs_one_of_the_strings(self):
        screens = {lp: {"01_home": t} for lp, t in self.HOME.items()}
        self.assertEqual(self.check({"01_home": {"any": ["Nope", "Senior iOS Engineer"]}}, screens)[1]["problems"], [])
        problems = self.check({"01_home": {"any": ["Nope", "Never"]}}, screens)[1]["problems"]
        self.assertEqual(problems, ['de/01_home.png: expected one of "Nope", "Never" on screen', 'en/01_home.png: expected one of "Nope", "Never" on screen'])

    def test_a_locale_table_covers_regional_variants_and_unused_ones_are_noted(self):
        screens = {"de": {"01_home": self.HOME["de"]}}
        self.assertEqual(self.check({"01_home": {"de": {"all": ["Nope"]}}}, screens)[1]["problems"], ['de/01_home.png: expected "Nope" on screen'])
        notes = self.check({"01_home": {"all": ["Senior iOS Engineer"], "fr": {"all": ["x"]}}}, screens)[1]["notes"]
        self.assertEqual(notes, ["[expect.01_home.fr] matches none of the languages checked"])

    def test_a_table_for_a_screenshot_that_does_not_exist_is_a_problem_with_did_you_mean(self):
        problems = self.check({"01_hom": {"any": ["x"]}}, {"de": {"01_home": self.HOME["de"]}})[1]["problems"]
        self.assertEqual(problems, ["[expect.01_hom] matches no screenshot; did you mean [expect.01_home]?"])

    def test_ocr_never_passes_or_fails_what_it_cannot_read(self):
        # Android: no .texts.json, so OCR. Greek can't be read by this Mac's OCR (readable = en, de): not found proves nothing.
        screens = {"en": {"01_home": ["Next", "Settings"]}}
        expect = {"01_home": {"all": ["Επόμενο", "Missing text"], "not": ["Ρυθμίσεις", "Settings"], "any": ["Άλλο"]}}
        code, report = self.check(expect, screens, ocr=True)
        self.assertEqual(sorted(report["problems"]), ['en/01_home.png: "Settings" must not be on screen', 'en/01_home.png: expected "Missing text" on screen'])
        self.assertEqual(len(report["notes"]), 3)
        self.assertTrue(all("could not verify" in n for n in report["notes"]), report["notes"])
        # found is found, in any script OCR happened to read; and a readable script checked by OCR still fails when absent
        ok = self.check({"01_home": {"all": ["Next"], "any": ["Ρυθμίσεις", "Settings"]}}, screens, ocr=True)[1]
        self.assertEqual((ok["problems"], ok["notes"]), ([], []))
        # the same Greek strings on iOS (the app's own text) are exact: absent means absent
        bad = self.check({"01_home": {"all": ["Επόμενο"]}}, {"en": {"01_home": ["Next", "Settings"]}})[1]
        self.assertEqual(bad["problems"], ['en/01_home.png: expected "Επόμενο" on screen'])

    def test_without_expect_nothing_changes(self):
        code, report = self.check(None, {"en": {"01_home": self.HOME["en"]}})
        self.assertEqual(report["problems"], [])

    def test_the_tables_are_validated_like_every_other_setting(self):
        for body, msg in (('[expect.01_home]\nanny = ["x"]\n', r"unknown setting 'anny'; did you mean 'any'\?"),
                          ('[expect.01_home]\nany = "x"\n', r"any in shotfleet.toml should be a list of texts"),
                          ('[expect.01_home]\nnot = []\n', r"not in shotfleet.toml should be a list of texts"),
                          ('[expect.01_home.de]\nal = ["x"]\n', r"\[expect.01_home.de\].*unknown setting 'al'; did you mean 'all'\?"),
                          ('[expect]\nany = ["x"]\n', r"'any' should be a table named after a screenshot"),
                          ('[expect.01_home.any]\nx = ["x"]\n', r"unknown setting 'any'"),
                          ('[expec.01_home]\n', r"did you mean \[expect\]")):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as d:
                f = Path(d) / "shotfleet.toml"; f.write_text(body)
                with self.assertRaisesRegex(sf.Fail, msg): sf.read_expect(f)
            with tempfile.TemporaryDirectory() as d:
                f = Path(d) / "shotfleet.toml"; f.write_text('[ios]\napp = "x.app"\n' + body)
                with self.assertRaises(sf.Fail): sf.platforms_in(f)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "shotfleet.toml"; f.write_text('[ios]\napp = "x.app"\n')
            with self.assertRaisesRegex(sf.Fail, r"no \[expect.<screenshot>\] table"): sf.read_expect(f)

    @needs_mac

    def test_check_content_cli_reads_the_config_and_keeps_the_json_keys(self):
        d = Path(tempfile.mkdtemp()); shots_with_texts(d, {lp: {"01_home": t} for lp, t in self.HOME.items()})
        for lp, words in self.STRINGS.items():
            (d / "locales" / lp).mkdir(parents=True); (d / "locales" / lp / "translation.json").write_text(json.dumps(words))
        cfg = d / "shotfleet.toml"; cfg.write_text('[expect.01_home]\nall = ["Steinmännchen"]\n')
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sf.main(["check", str(d / "shots"), "--strings", str(d / "locales/*/translation.json"), "--content", str(cfg),
                            "--report", str(d / "rep"), "--json"])
        report = json.loads(out.getvalue())
        self.assertEqual((code, set(report)), (1, {"exit", "screenshots", "problems", "notes"}))
        self.assertEqual(report["problems"], ['en/01_home.png: expected "Steinmännchen" on screen'])
        self.assertIn("content: [expect] checked on 2 screens", err.getvalue())
        with contextlib.redirect_stderr(io.StringIO()) as e2:
            self.assertEqual(sf.main(["check", str(d / "shots"), "--content", str(d / "missing.toml")]), 2)
        self.assertIn("no config at", e2.getvalue())

    @needs_mac

    def test_run_passes_the_expect_tables_to_check(self):
        with tempfile.TemporaryDirectory() as d:
            app = Path(d) / "My.app"; app.mkdir()
            (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "com.x", "DTPlatformName": "iphonesimulator"}))
            (Path(d) / "flow.yaml").write_text("- launchApp\n")
            (Path(d) / "shotfleet.toml").write_text('[ios]\napp = "My.app"\n[expect.01_home]\nany = ["Hi"]\n')
            with mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"):
                _, cfg, _ = sf.load_config(Path(d) / "shotfleet.toml")
        self.assertEqual(cfg["_expect"], {"01_home": {"any": ["Hi"]}})


class SetupCommands(unittest.TestCase):
    """[ios] simctl and [android] shell: per-device commands after boot, built and substituted without a device."""
    def test_simctl_commands_get_the_udid_and_run_in_order_after_the_status_bar(self):
        calls = []
        class FakeSim:
            def __init__(self, udid): self.udid = udid
            def run(self, *a, check=True): calls.append(a); return ""
        listing = json.dumps({"devices": {"rt": []}})
        with mock.patch.object(sf, "sh", side_effect=lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, listing if "list" in cmd else "U1", "")), \
             mock.patch.object(sf, "Sim", FakeSim), mock.patch.object(sf, "OUR_SIMS", set()):
            pool = sf.make_pool(1, "dt", "rt", simctl=["ui $UDID appearance dark", "location ${UDID} set 52.3676,4.9041", 'privacy $UDID grant photos "com.x y"'])
        udid = pool[0].udid
        flat = [c for c in calls if c[0] in ("ui", "location", "privacy", "status_bar")]
        self.assertEqual([c[0] for c in flat], ["status_bar", "ui", "location", "privacy"])
        self.assertEqual(flat[1], ("ui", udid, "appearance", "dark"))
        self.assertEqual(flat[2], ("location", udid, "set", "52.3676,4.9041"))
        self.assertEqual(flat[3], ("privacy", udid, "grant", "photos", "com.x y"))  # quoting is shell-like, not a string split

    def test_android_shell_commands_run_per_emulator_after_the_demo_mode_loop(self):
        calls = []
        class FakeEmu:
            def __init__(self, port): self.port, self.serial = port, f"emulator-{port}"
            def adb(self, *a, check=True, timeout=180): calls.append((self.serial, a, check)); return ""
            def booted(self): return False
        home = Path(tempfile.mkdtemp()); (home / ".android/avd/shotfleet_android.avd/snapshots/shotfleet").mkdir(parents=True)
        with mock.patch.object(sf, "Emu", FakeEmu), mock.patch.object(sf, "start_emu"), mock.patch.object(sf, "wait_booted"), \
             mock.patch.object(sf.time, "sleep"), mock.patch.object(sf.Path, "home", return_value=home):
            sf.android_pool(2, {"shell": ["setprop debug.remoti.demo 1", "settings put system font_scale 1.0"]}, [])
        for serial in ("emulator-5702", "emulator-5704"):
            mine = [(a, check) for s, a, check in calls if s == serial]
            self.assertEqual(mine[-2:], [(("shell", "setprop debug.remoti.demo 1"), True), (("shell", "settings put system font_scale 1.0"), True)])
            self.assertEqual(mine[len(sf.DEMO_MODE) - 1], (("shell", sf.DEMO_MODE[-1]), False))  # demo mode first, and it stays best-effort
            self.assertEqual(len(mine), len(sf.DEMO_MODE) + 2)

    @needs_mac

    def test_a_failing_command_is_a_setup_error_that_prints_it(self):
        class Boom:
            udid = "U9"
            def run(self, *a, check=True): raise RuntimeError("simctl " + " ".join(a) + ": Unable to set")
            def adb(self, *a, check=True): raise RuntimeError("adb " + " ".join(a) + ": Permission denied")
        with self.assertRaisesRegex(sf.Fail, r"\[ios\] simctl command failed.*simctl ui U9 appearance dark: Unable to set"):
            sf.run_setup(Boom(), "simctl", ["ui $UDID appearance dark"])
        with self.assertRaisesRegex(sf.Fail, r"\[android\] shell command failed.*adb shell setprop a b: Permission denied"):
            sf.run_setup(Boom(), "shell", ["setprop a b"])
        # as the CLI sees it: exit 2, one line, no traceback
        boom = sf.Fail("[ios] simctl command failed, stopping before the run: simctl ui U9 appearance dark: Unable to set")
        with mock.patch.object(sf, "cmd_run", side_effect=boom), mock.patch.object(sf, "apply_free_tier"), \
             mock.patch.object(sf.shutil, "which", return_value=None), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(sf.main(["run"]), 2)
        self.assertEqual(err.getvalue().strip(), f"shotfleet: {boom}")

    def test_the_settings_are_validated_like_every_other_one(self):
        with tempfile.TemporaryDirectory() as d:
            app = Path(d) / "My.app"; app.mkdir()
            (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "com.x", "DTPlatformName": "iphonesimulator"}))
            (Path(d) / "flow.yaml").write_text("- launchApp\n")
            cases = (('simctl = "ui"', "simctl in shotfleet.toml should be a list"),
                     ('simctl = [1]', "simctl in shotfleet.toml should be a list of commands"),
                     ('simctl = ["ui \\"x"]', "can't read"),
                     ('simctl_ = []', r"unknown setting 'simctl_'; did you mean 'simctl'\?"),
                     ('shell = ["x"]', "unknown setting 'shell'"))
            for line, msg in cases:
                (Path(d) / "shotfleet.toml").write_text(f'[ios]\napp = "My.app"\n{line}\n')
                with self.subTest(line=line), mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), self.assertRaisesRegex(sf.Fail, msg):
                    sf.load_config(Path(d) / "shotfleet.toml")
            apk = Path(d) / "a.apk"; apk.write_bytes(b"x")
            for line, msg in (('shell = [3]', r"\[android\] shell in shotfleet.toml should be a list of commands"), ('simctl = []', "unknown setting 'simctl'")):
                (Path(d) / "shotfleet.toml").write_text(f'[android]\napk = "a.apk"\npackage = "p"\n{line}\n')
                with self.subTest(line=line), mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), \
                     mock.patch.object(sf, "aapt2", return_value="aapt2"), mock.patch.object(sf, "sh", return_value=subprocess.CompletedProcess([], 0, "", "")), \
                     self.assertRaisesRegex(sf.Fail, msg):
                    sf.load_config(Path(d) / "shotfleet.toml")


# ---------------------------------------------------------------------------------------------------------------------
# Claims G1 (2026-10-03): behaviour claims that a deterministic test can prove. No simulator, emulator, network or Maestro.
# Each class names the claim ids (tests/claims.json) it backs.
# ---------------------------------------------------------------------------------------------------------------------
G1_STRINGS = {"en": {"a": "Next", "b": "Settings", "c": "Start Training", "d": "Training log"},
              "de": {"a": "Weiter", "b": "Einstellungen", "c": "Training starten", "d": "Trainingsprotokoll"},
              "ja": {"a": "次へ", "b": "設定", "c": "トレーニング開始", "d": "記録"}}
G1_SHOWS = {lp: list(t.values()) for lp, t in G1_STRINGS.items()}  # what a screen in that language shows


def g1_image(salt, size=(1320, 2868)):
    """A PNG header of that size; the salt makes every image different bytes (identical bytes are what `check` calls a copy)."""
    return png_c(*size) + salt.encode()


def g1_check(spec, strings=G1_STRINGS, readable=("en", "de", "ja"), ocr=None, **kw):
    """Run cmd_check on {label: {name: lines | (lines, size) | (lines, size, salt)}}. Lines are the app's own text (.texts.json, as an iOS
    run saves them) unless `ocr` is True: then a fake text recognition reads them from <name>.png.txt. -> (code, report, stdout)."""
    d = Path(tempfile.mkdtemp())
    for label, screens in spec.items():
        for name, shot in screens.items():
            lines, size, salt = (shot, (1320, 2868), f"{label}/{name}") if isinstance(shot, list) else (shot + (f"{label}/{name}",))[:3]
            png = d / "shots" / label / name; png.parent.mkdir(parents=True, exist_ok=True); png.write_bytes(g1_image(salt, size))
            if ocr: Path(f"{png}.txt").write_text("\n".join(lines))
            else: png.with_suffix(".texts.json").write_text(json.dumps(lines, ensure_ascii=False))
    def fake_ocr(_ocr, png, timeout=120):
        text = Path(f"{png}.txt").read_text()
        return {"text": text, "chars": len(text), "lang": "en" if "Next" in text else None, "langs": {"en": 0.9} if "Next" in text else {}}
    with mock.patch.object(sf, "warm_up_ocr", return_value=True), mock.patch.object(sf, "ocr_tool", return_value="ocr"), \
         mock.patch.object(sf, "readable_languages", return_value=set(readable)), mock.patch.object(sf, "read_text", fake_ocr), \
         mock.patch.object(sf, "tesseract_languages", return_value=set()), contextlib.redirect_stdout(io.StringIO()) as out:
        code = sf.cmd_check(d / "shots", strings=strings, report_dir=d / "rep", **kw)
    return code, json.loads((d / "rep/check.json").read_text()), out.getvalue()


class G1CheckDetectors(unittest.TestCase):
    """C003, C009, C024, C025: every screenshot goes through the checks, and each mistake is reported as one named problem."""
    CLEAN = {"de": {"01.png": G1_SHOWS["de"], "02.png": G1_SHOWS["de"]}, "en": {"01.png": G1_SHOWS["en"], "02.png": G1_SHOWS["en"]},
             "ja": {"01.png": G1_SHOWS["ja"], "02.png": G1_SHOWS["ja"]}}

    def test_a_clean_set_passes_and_every_screenshot_is_judged(self):  # C003
        code, report, out = g1_check(self.CLEAN)
        self.assertEqual((code, report["problems"]), (0, []))
        self.assertEqual(sorted(r["file"] for r in report["screenshots"]), sorted(f"{l}/{n}" for l, s in self.CLEAN.items() for n in s))
        self.assertEqual({r["file"]: r["lang"] for r in report["screenshots"]}["de/02.png"], "de")  # each one judged, with the language it shows
        self.assertIn("checked 6 screenshots in 3 languages: 0 problem(s)", out)

    def test_wrong_language_is_one_problem_naming_the_file_and_the_language_it_shows(self):  # C003, C009
        spec = {**self.CLEAN, "de": {"01.png": G1_SHOWS["de"], "02.png": G1_SHOWS["en"]}}
        code, report, _ = g1_check(spec)
        self.assertEqual(code, 1)
        self.assertEqual(report["problems"], ["de/02.png: shows en strings (4 lines) more than de (0)"])

    def test_the_app_text_is_compared_with_the_apps_strings_not_with_a_language_guess(self):  # C009
        # Japanese strings on a German screen: no language detection runs for an iOS run's own text (lang is None)
        spec = {**self.CLEAN, "de": {"01.png": G1_SHOWS["ja"] + ["Weiter"], "02.png": G1_SHOWS["de"]}}
        code, report, _ = g1_check(spec)
        self.assertEqual(report["problems"], ["de/01.png: shows ja strings (4 lines) more than de (1)"])

    def test_the_same_comparison_runs_on_text_read_by_ocr_the_android_and_other_tools_path(self):  # C009
        spec = {**self.CLEAN, "de": {"01.png": G1_SHOWS["de"], "02.png": G1_SHOWS["en"]}}
        code, report, _ = g1_check(spec, ocr=True)
        self.assertEqual((code, report["problems"]), (1, ["de/02.png: shows en strings (4 lines) more than de (0)"]))
        self.assertEqual(g1_check(self.CLEAN, ocr=True)[:2][0], 0)

    def test_the_same_image_in_two_languages_is_reported_once_with_both_files(self):  # C025, C003
        same = g1_image("same")
        d = Path(tempfile.mkdtemp())
        for lp in ("de", "en"):
            png = d / "shots" / lp / "01.png"; png.parent.mkdir(parents=True); png.write_bytes(same)
            png.with_suffix(".texts.json").write_text(json.dumps(G1_SHOWS["en"]))  # 41 characters: enough text to count as a copy
        with mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "readable_languages", return_value={"en", "de"}), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sf.cmd_check(d / "shots", strings=G1_STRINGS, report_dir=d / "rep"), 1)
        problems = json.loads((d / "rep/check.json").read_text())["problems"]
        self.assertEqual([p for p in problems if p.startswith("identical")], ["identical image in 2 languages: de/01.png, en/01.png"])

    def test_known_blind_spot_two_short_screens_in_two_languages_are_not_called_copies(self):  # C025, C003 (the 40-character floor)
        short = ["OK", "Go"]  # a watch screen: identical in every language, and fine
        code, report, _ = g1_check({"de": {"01.png": short}, "en": {"01.png": short}}, strings={"en": {"a": "OK", "b": "Go"}, "de": {"a": "OK", "b": "Go"}})
        self.assertEqual([p for p in report["problems"] if p.startswith("identical")], [])

    def test_a_language_that_did_not_produce_every_screen_is_reported_as_missing(self):  # C025, C003
        spec = {**self.CLEAN, "ja": {"01.png": G1_SHOWS["ja"]}}
        code, report, _ = g1_check(spec)
        self.assertEqual((code, report["problems"]), (1, ["ja: missing 02.png"]))

    def test_a_listing_in_a_language_the_app_does_not_have_is_named_and_not_read_as_another_language(self):  # C024
        spec = {**self.CLEAN, "fr-FR": {"01.png": G1_SHOWS["en"], "02.png": G1_SHOWS["en"]}}
        code, report, _ = g1_check(spec)
        self.assertEqual(code, 1)
        self.assertEqual(report["problems"], ["fr-FR: the app has no fr-FR translation, so this listing shows another language"])

    def test_a_size_the_store_refuses_is_one_problem_per_file(self):  # C003, C100 (the size half)
        spec = {**self.CLEAN, "de": {"01.png": (G1_SHOWS["de"], (1000, 2000)), "02.png": G1_SHOWS["de"]}}
        code, report, _ = g1_check(spec)
        self.assertEqual((code, report["problems"]), (1, ["de/01.png: 1000x2000 isn't an App Store screenshot size"]))

    def test_a_translated_caption_over_an_english_ui_is_named_as_such(self):  # C100 (the caption half)
        tables = sf.string_tables(G1_STRINGS)
        ocr = {"text": "\n".join(G1_SHOWS["en"]), "chars": 60, "caption": "トレーニングを記録", "caption_lang": "ja"}
        got, problem = sf.judge_screen("ja", ocr, tables)
        self.assertEqual(got, "en")
        self.assertEqual(sf.caption_problem("ja", ocr, tables, problem),
                         "the caption is in ja but the app UI shows en strings (4 lines) more than ja (0)")
        self.assertEqual(sf.caption_problem("ja", {**ocr, "caption_lang": "de"}, tables, problem), problem)  # not the language's caption: plain problem


class G1ScriptsMacosCannotRead(unittest.TestCase):
    """C071: for a script macOS text recognition cannot read, `check` still checks other-language screens, copies and missing
    screens, and says that it did only that. (The '33 languages' number is a measurement on one Mac: see the claim.)"""
    STRINGS = {"en": G1_STRINGS["en"], "el": {"a": "Επόμενο", "b": "Ρυθμίσεις", "c": "Έναρξη προπόνησης", "d": "Αρχείο προπόνησης"}}

    def test_a_blank_read_of_an_unreadable_script_proves_nothing_either_way(self):
        tables = sf.string_tables(self.STRINGS)
        with mock.patch.object(sf, "readable_languages", return_value={"en", "de"}):
            self.assertEqual(sf.judge_screen("el", {"chars": 0, "text": ""}, tables), (None, None))
            got, problem = sf.judge_screen("el", {"chars": 60, "text": "\n".join(G1_SHOWS["en"])}, tables)
            self.assertEqual(got, "en"); self.assertIn("shows en strings", problem)  # another language's strings are still caught
            self.assertIn("no text found", sf.judge_screen("en", {"chars": 0, "text": ""}, tables)[1])  # a readable one is not excused

    def test_check_says_it_only_did_the_weaker_checks_and_still_finds_missing_and_wrong_language(self):
        english = {"01.png": G1_SHOWS["en"], "02.png": G1_SHOWS["en"], "03.png": G1_SHOWS["en"]}
        d = Path(tempfile.mkdtemp())
        shots = {"en": english, "el": {"01.png": [], "02.png": G1_SHOWS["en"]}}
        for label, screens in shots.items():
            for name, lines in screens.items():
                png = d / "shots" / label / name; png.parent.mkdir(parents=True, exist_ok=True); png.write_bytes(g1_image(f"{label}/{name}"))
                Path(f"{png}.txt").write_text("\n".join(lines))
        fake = lambda _o, png, timeout=120: (lambda t: {"text": t, "chars": len(t), "lang": "en" if t else None, "langs": {"en": 0.9} if t else {}})(Path(f"{png}.txt").read_text())
        with mock.patch.object(sf, "warm_up_ocr", return_value=True), mock.patch.object(sf, "ocr_tool", return_value="ocr"), \
             mock.patch.object(sf, "readable_languages", return_value={"en", "de"}), mock.patch.object(sf, "read_text", fake), \
             mock.patch.object(sf, "tesseract_languages", return_value=set()), contextlib.redirect_stdout(io.StringIO()) as out:
            code = sf.cmd_check(d / "shots", strings=self.STRINGS, report_dir=d / "rep")
        problems = json.loads((d / "rep/check.json").read_text())["problems"]
        self.assertEqual(code, 1)
        self.assertIn("macOS can't read the script of el: those screens were only checked for showing another language, copies and missing screens", out.getvalue())
        self.assertEqual(sorted(problems), ["el/02.png: shows en strings (4 lines) more than el (0)", "el: missing 03.png"])  # nothing said about el/01.png


class G1MultiDeviceExport(unittest.TestCase):
    """C021: the Android 10-inch tablet set is exported next to the phone set (the 7-inch and iPad 13-inch sets are covered by
    SevenInchTablet and MultiDevice)."""
    def test_phone_and_tablet_runs_export_to_their_own_play_folders(self):
        with tempfile.TemporaryDirectory() as d:
            for dev, size in (("phone", (1080, 1920)), ("tablet", (1440, 2560))):
                out = Path(d) / "out" / dev; (out / "raw/de").mkdir(parents=True)
                (out / "raw/de/01.png").write_bytes(png_c(*size))
                (out / "run.json").write_text(json.dumps({"platform": "android", "device": dev, "locales": {"de": {"ok": True}}}))
                (out / "check.json").write_text(json.dumps({"problems": []}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sf.cmd_export(Path(d) / "out", Path(d) / "fl"), 0)
            images = Path(d) / "fl/metadata/android/de-DE/images"
            self.assertEqual(sorted(p.name for p in images.iterdir()), ["phoneScreenshots", "tenInchScreenshots"])
            self.assertEqual(sf.png_size(images / "phoneScreenshots/phone_01.png"), (1080, 1920))
            self.assertEqual(sf.png_size(images / "tenInchScreenshots/tablet_01.png"), (1440, 2560))

    def test_the_tablet_device_matches_what_google_play_wants_and_the_ipad_size_is_the_13_inch_class(self):
        w, h, _ = sf.ANDROID_DEVICES["tablet"]["size"]
        self.assertEqual((w, h, h * 9 == w * 16), (1440, 2560, True))  # 9:16 at 1080 px or more: eligible for Play's recommendations
        d = Path(tempfile.mkdtemp()); pngs = [d / f"{i}.png" for i in range(4)]
        for p in pngs: p.write_bytes(png_c(w, h))
        self.assertEqual(sf.store_rules({"de": pngs}, android=True, tablet=True), ([], []))
        self.assertEqual(sf.apple_class((2064, 2752)), 'iPad 13"'); self.assertEqual(sf.apple_class((2048, 2732)), 'iPad 13"')


class G1CollisionWarningComesFirst(unittest.TestCase):
    """C017: a clash between two words is printed before any simulator or emulator boots, on iOS and on Android."""
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        for lp, words in (("en", {"next": "Next", "advanced": "Advanced"}), ("tr", {"next": "İleri", "advanced": "İleri"})):
            (self.d / "locales" / lp).mkdir(parents=True); (self.d / "locales" / lp / "translation.json").write_text(json.dumps(words, ensure_ascii=False))
        (self.d / "flow.yaml").write_text('- launchApp\n- tapOn: "Next"\n- takeScreenshot: 01\n')
        self.path = lambda p: self.d / p
        self.cfg = {"_inputs": {}, "flow": "flow.yaml", "out": "out", "strings": "locales/*/translation.json", "locales": ["tr"]}

    def run_until_boot(self, call):
        class Stop(Exception): pass
        with mock.patch.object(sf, "fit_parallel", return_value=1), contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(Stop):
            call(Stop)
        lines = out.getvalue().splitlines()
        warn = next(i for i, l in enumerate(lines) if l.startswith("warning tr: ") and "'Next' -> 'İleri' also means 'Advanced'" in l)
        boot = next(i for i, l in enumerate(lines) if l.startswith("booting "))
        self.assertLess(warn, boot, lines)
        self.assertIn("anchor that step (below:/above:)", lines[warn])

    @needs_mac

    def test_ios(self):
        cfg = {**self.cfg, "app": "My.app", "bundle_id": "x.y", "device_type": "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max",
               "runtime": "com.apple.CoreSimulator.SimRuntime.iOS-27-0"}
        def call(Stop):
            with mock.patch.object(sf, "make_pool", side_effect=Stop): sf.ios_run(cfg, self.path)
        self.run_until_boot(call)

    def test_android(self):
        cfg = {**self.cfg, "apk": "a.apk", "package": "p.q"}
        def call(Stop):
            with mock.patch.object(sf, "android_pool", side_effect=Stop): sf.android_run(cfg, self.path, self.path("out"), None, None)
        self.run_until_boot(call)


class G1SetupCommandFailureStopsTheRun(unittest.TestCase):
    """C120: a failing [ios] simctl / [android] shell command stops the run before anything is installed or captured (exit 2, command printed)."""
    @needs_mac
    def test_ios_stops_before_install_and_maestro(self):
        d = Path(tempfile.mkdtemp()); app = d / "My.app"
        (app / "en.lproj").mkdir(parents=True); (app / "en.lproj/Localizable.strings").write_text('"next" = "Next";\n')
        (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "x.y", "CFBundleLocalizations": ["en"], "DTPlatformName": "iphonesimulator"}))
        (d / "flow.yaml").write_text("- launchApp\n- takeScreenshot: 01\n")
        (d / "shotfleet.toml").write_text('[ios]\napp = "My.app"\nsimctl = ["ui $UDID appearance dark"]\n')
        calls = []
        class Sim:
            def __init__(self, udid): self.udid = udid
            def run(self, *a, check=True):
                calls.append(a[0])
                if a[0] == "ui": raise RuntimeError("simctl ui U1 appearance dark: Unable to set")
                return ""
        real = sf.sh
        def sh(cmd, **kw):
            if cmd[:3] == ["xcrun", "simctl", "list"]: return subprocess.CompletedProcess(cmd, 0, json.dumps({"devices": {"rt": []}}), "")
            if cmd[0] == "sysctl": return subprocess.CompletedProcess(cmd, 0, "1", "")
            if cmd[:2] == ["xcrun", "simctl"]: return subprocess.CompletedProcess(cmd, 0, "U1\n", "")
            return real(cmd, **kw)
        with mock.patch.object(sf, "Sim", Sim), mock.patch.object(sf, "sh", sh), mock.patch.object(sf, "OUR_SIMS", set()), \
             mock.patch.object(sf, "run_guarded", side_effect=AssertionError("Maestro must not start")), mock.patch.object(sf, "kill_stale_drivers"), \
             mock.patch.object(sf, "latest_ios_runtime", return_value="rt"), mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), \
             mock.patch.object(sf, "java_env", return_value={}), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(sf.Fail, r"\[ios\] simctl command failed, stopping before the run: .*Unable to set"):
                sf.cmd_run(str(d / "shotfleet.toml"))
        self.assertNotIn("install", calls)
        self.assertEqual(calls[-1], "ui")  # nothing was run after the failing command

    def test_android_stops_before_install_and_maestro(self):
        d = Path(tempfile.mkdtemp()); home = d / "home"; (home / ".android/avd/shotfleet_android.avd/snapshots/shotfleet").mkdir(parents=True)
        for lp, w in (("en", "Next"), ("de", "Weiter")):
            (d / "locales" / lp).mkdir(parents=True); (d / "locales" / lp / "translation.json").write_text(json.dumps({"a": w}))
        (d / "flow.yaml").write_text("- launchApp\n- takeScreenshot: 01\n")
        calls = []
        class Emu:
            def __init__(self, port): self.port, self.serial = port, f"emulator-{port}"
            def booted(self): return False
            def adb(self, *a, check=True, timeout=180):
                calls.append(a)
                if a[:1] == ("shell",) and a[1].startswith("setprop") and check: raise RuntimeError("adb shell setprop a b: Permission denied")
                return ""
        cfg = {"flow": "flow.yaml", "apk": "a.apk", "package": "p.q", "strings": "locales/*/translation.json", "locales": ["de"], "shell": ["setprop a b"]}
        with mock.patch.object(sf, "Emu", Emu), mock.patch.object(sf, "start_emu"), mock.patch.object(sf, "wait_booted"), mock.patch.object(sf.time, "sleep"), \
             mock.patch.object(sf.Path, "home", return_value=home), mock.patch.object(sf, "fit_parallel", return_value=1), \
             mock.patch.object(sf, "run_guarded", side_effect=AssertionError("Maestro must not start")), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(sf.Fail, r"\[android\] shell command failed, stopping before the run: .*Permission denied"):
                sf.android_run(cfg, lambda p: d / p, d / "out", None, None)
        self.assertFalse([c for c in calls if c[0] == "install"])


class G1ContentExpectInRun(unittest.TestCase):
    """C119: `run` hands the config's [expect.*] tables to the check that ends it (the check itself is ContentExpect)."""
    @needs_mac
    def test_run_passes_expect_to_cmd_check(self):
        t = RetryOnSlowSimulator("run_it"); t.setUp()
        (t.d / "shotfleet.toml").write_text('[ios]\napp = "My.app"\nlocales = ["de"]\n[expect.01]\nany = ["Hi"]\n')
        seen = []
        code, out = t.run_it("1", check=lambda *a, **k: seen.append(k) or 0)
        self.assertEqual(code, 0, out)
        self.assertEqual(seen[-1]["expect"], {"01": {"any": ["Hi"]}})


class G1ExitCodes(unittest.TestCase):
    """C064: 0 all good, 1 problems found, 2 setup error, 130 interrupted; `check --json` keeps its documented keys."""
    def run_check(self, spec, *extra):
        d = Path(tempfile.mkdtemp())
        for label, screens in spec.items():
            for name, lines in screens.items():
                png = d / "shots" / label / name; png.parent.mkdir(parents=True, exist_ok=True); png.write_bytes(g1_image(f"{label}/{name}"))
                png.with_suffix(".texts.json").write_text(json.dumps(lines, ensure_ascii=False))
        for lp, words in G1_STRINGS.items():
            (d / "locales" / lp).mkdir(parents=True); (d / "locales" / lp / "translation.json").write_text(json.dumps(words, ensure_ascii=False))
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "readable_languages", return_value={"en", "de", "ja"}), \
             mock.patch.object(sf, "warm_up_ocr", return_value=True), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sf.main(["check", str(d / "shots"), "--strings", str(d / "locales/*/translation.json"), "--report", str(d / "rep"), *extra])
        return code, out.getvalue(), err.getvalue()

    def test_zero_for_a_clean_set_one_for_a_problem(self):
        clean = {"de": {"01.png": G1_SHOWS["de"]}, "en": {"01.png": G1_SHOWS["en"]}}
        self.assertEqual(self.run_check(clean)[0], 0)
        code, out, err = self.run_check({**clean, "de": {"01.png": G1_SHOWS["en"]}}, "--json")
        self.assertEqual(code, 1)
        report = json.loads(out)
        self.assertEqual({k: report[k] for k in ("exit", "problems")}, {"exit": 1, "problems": ["de/01.png: shows en strings (4 lines) more than de (0)"]})
        self.assertEqual(set(report), {"exit", "screenshots", "problems", "notes"})

    def test_two_for_a_setup_error_with_one_line_on_stderr(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err): self.assertEqual(sf.main(["check", "/no/such/folder"]), 2)
        self.assertEqual(err.getvalue().strip(), "shotfleet: no folder at /no/such/folder")
        with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(sf.main(["run", "/no/such/shotfleet.toml"]), 2)

    def test_130_when_interrupted_and_stale_drivers_are_cleaned_up(self):
        with mock.patch.object(sf, "check_any", side_effect=KeyboardInterrupt), mock.patch.object(sf, "kill_stale_drivers") as kill, \
             contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(sf.main(["check", "x"]), 130)
        kill.assert_called_once(); self.assertIn("stopped", err.getvalue())

    def test_doctor_is_two_when_nothing_is_ready(self):  # also C059
        self.assertEqual(G1Doctor().nothing_installed()[0], 2)


class G1Doctor(unittest.TestCase):
    """C059: doctor checks Maestro, Java, Xcode and the Android SDK and puts a fix on every line that is missing."""
    def doctor(self, present):
        d = Path(tempfile.mkdtemp()); sdk = d / "sdk"; sdk.mkdir()
        if present:
            for rel in ("platform-tools/adb", "emulator/emulator", "cmdline-tools/latest/bin/avdmanager", "cmdline-tools/latest/bin/sdkmanager",
                        "build-tools/36.0.0/aapt2", "system-images/android-36/google_apis/arm64-v8a/package.xml"):
                (sdk / rel).parent.mkdir(parents=True, exist_ok=True); (sdk / rel).write_text("x")
        ok = lambda cmd, **k: subprocess.CompletedProcess(cmd, 0 if present else 1, "Ready\n" if present else "", "")
        out = io.StringIO()
        with mock.patch.object(sf, "SDK", sdk), mock.patch.object(sf, "BREW", d / "brew"), mock.patch.object(sf.Path, "home", return_value=d / "home"), \
             mock.patch.object(sf.shutil, "which", side_effect=(lambda c, **k: f"/usr/bin/{c}") if present else (lambda c, **k: None)), \
             mock.patch.object(sf, "find_java", return_value=(present, None)), mock.patch.object(sf, "java_env", return_value={}), \
             mock.patch.object(sf, "sh", ok), mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "latest_release", return_value=None), \
             mock.patch.object(sf, "read_maestro_version", return_value="2.0.10"), contextlib.redirect_stdout(out):
            code = sf.cmd_doctor()
        return code, out.getvalue()

    def nothing_installed(self): return self.doctor(False)

    def test_a_mac_with_nothing_installed_gets_one_fix_per_missing_tool_and_exit_2(self):
        code, out = self.doctor(False)
        self.assertEqual(code, 2)
        missing = [l for l in out.splitlines() if l.startswith("MISSING")]
        for tool in ("maestro", "java 17+", "swiftc", "xcrun simctl", "adb", "emulator", "avdmanager", "aapt2", "system image"):
            line = next((l for l in missing if l.startswith(f"MISSING {tool}")), None)
            self.assertIsNotNone(line, f"{tool} not reported: {out}")
            self.assertIn("  -> ", line, f"{tool} has no fix")
        self.assertIn("get.maestro.mobile.dev", out); self.assertIn("brew install openjdk", out); self.assertIn("xcode-select --install", out)
        self.assertIn("sdkmanager", out)
        self.assertIn("iOS: not ready   Android: not ready", out); self.assertIn("next: fix the MISSING lines above", out)

    def test_a_complete_mac_is_ready_for_both_and_exit_0(self):
        code, out = self.doctor(True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("MISSING", out)
        self.assertIn("iOS: ready   Android: ready", out)


class G1ReadmeConfigBlocks(unittest.TestCase):
    """C063: every config key the README shows is accepted by the program's own validation, and the keys the claim lists are all shown."""
    README = (Path(sf.__file__).resolve().parent / "README.md").read_text()
    CLAIMED = {"flow", "out", "parallel", "locales", "base_locale", "bundle_id", "device_type", "runtime", "device_types", "devices"}

    def blocks(self):
        for block in re.findall(r"```toml\n(.*?)```", self.README, flags=re.S):
            try: yield tomllib.loads(block)
            except tomllib.TOMLDecodeError:  # a block that lists alternatives (strings = ... three times): each line on its own
                for line in block.splitlines():
                    if line.strip() and not line.lstrip().startswith("#"): yield tomllib.loads(line)

    def test_every_documented_table_and_key_passes_the_programs_validation(self):
        seen = set()
        for doc in self.blocks():
            sf.check_tables({k: v for k, v in doc.items() if isinstance(v, dict)}, "README")  # unknown tables, hook events, overrides, inputs, expect
            for platform in ("ios", "android"):
                known = {**sf.KEYS["common"], **sf.KEYS[platform]}
                for key, value in doc.get(platform, {}).items():
                    self.assertIn(key, known, f"[{platform}] {key} is in the README but not accepted")
                    self.assertTrue(isinstance(value, known[key]) and not (known[key] is int and isinstance(value, bool)), f"{key} has the wrong type")
                    seen.add(key)
            for key, value in doc.items():  # top-level `strings = ...` lines
                if not isinstance(value, dict): self.assertIn(key, sf.KEYS["common"]); seen.add(key)
        self.assertLessEqual(self.CLAIMED, seen)
        self.assertIn("strings", seen)

    def test_the_documented_android_devices_exist(self):
        doc = next(d for d in self.blocks() if "devices" in d.get("android", {}))
        self.assertLessEqual(set(doc["android"]["devices"]), set(sf.ANDROID_DEVICES))


class G1ReactIntlAndFormats(unittest.TestCase):
    """C036: react-intl's flat JSON with ICU plurals and {name} placeholders is read like i18next's."""
    def test_react_intl_flat_json_with_icu_plural(self):
        d = Path(tempfile.mkdtemp()); (d / "messages").mkdir()
        (d / "messages/en.json").write_text(json.dumps({"home.next": "Next", "jobs": "{count, plural, one {# job} other {# jobs}}", "hello": "Hello, {name}!"}))
        (d / "messages/de.json").write_text(json.dumps({"home.next": "Weiter", "jobs": "{count, plural, one {# Job} other {# Jobs}}", "hello": "Hallo, {name}!"}))
        got = sf.load_strings_files([str(d / "messages/*.json")])
        self.assertEqual(got["de"], {"home.next": "Weiter", "jobs#one": "{count} Job", "jobs#other": "{count} Jobs", "hello": "Hallo, {name}!"})
        out, missing, _ = sf.translate_flow("appId: x\n---\n- tapOn: Next\n- assertVisible: 3 jobs\n- assertVisible: Hello, Anna!\n", got["en"], got["de"])
        self.assertEqual((out, missing), ("appId: x\n---\n- tapOn: 'Weiter'\n- assertVisible: '(3 Job|3 Jobs)'\n- assertVisible: 'Hallo, Anna!'\n", []))


class G1InitIsTwoLines(unittest.TestCase):
    """C018: `shotfleet init` writes a config with two lines that are not comments (four with both platforms) and a starter flow."""
    def test_one_build_two_lines_two_builds_four_lines(self):
        with tempfile.TemporaryDirectory() as d:
            app = Path(d) / "My.app"; app.mkdir()
            (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "com.example.my", "DTPlatformName": "iphonesimulator"}))
            apk = Path(d) / "a.apk"; apk.write_bytes(b"x")
            body = lambda: [l for l in (Path(d) / "dest/shotfleet.toml").read_text().splitlines() if l.strip() and not l.lstrip().startswith("#")]
            with mock.patch.object(sf, "load_strings", return_value={"en": {"a": "A"}, "de": {"a": "B"}}), \
                 mock.patch.object(sf, "load_strings_apk", return_value={"en": {"a": "A"}, "de": {"a": "B"}}), \
                 mock.patch.object(sf, "aapt2", return_value="aapt2"), contextlib.redirect_stdout(io.StringIO()) as out, \
                 mock.patch.object(sf, "sh", side_effect=lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, "package: name='p.q'\n" if "badging" in cmd else "com.example.my", "")):
                sf.cmd_init([str(app)], Path(d) / "dest")
                self.assertEqual(body(), ["[ios]", f'app = "{sf.config_path(app, Path(d) / "dest")}"'])
                self.assertTrue((Path(d) / "dest/flow.yaml").read_text().count("- launchApp") == 1)
                (Path(d) / "dest/shotfleet.toml").unlink()
                sf.cmd_init([str(app), str(apk)], Path(d) / "dest")
                self.assertEqual([l.split(" =")[0] for l in body()], ["[ios]", "app", "[android]", "apk"])


class G1HookVariables(unittest.TestCase):
    """C068: the environment each hook event really gets. (README.md says _BUNDLE_ID reaches every event and _LOCALES the run
    hooks; the export hooks get no _BUNDLE_ID: see the claim.)"""
    NAMES = ("EVENT", "VERSION", "CONFIG", "PLATFORM", "OUT", "BUNDLE_ID", "LOCALES", "EXIT", "PROBLEMS", "REPORT", "FASTLANE")

    @needs_mac

    def test_each_event_gets_exactly_these_variables(self):
        d = Path(tempfile.mkdtemp()); app = d / "My.app"; app.mkdir()
        (app / "Info.plist").write_bytes(__import__("plistlib").dumps({"CFBundleIdentifier": "com.example.my", "DTPlatformName": "iphonesimulator"}))
        (d / "flow.yaml").write_text("- launchApp\n")
        dump = lambda ev: f"env | grep '^SHOTFLEET_' | sort > {ev}.env"
        (d / "shotfleet.toml").write_text('[ios]\napp = "My.app"\n[hooks]\n' + "".join(f"{ev} = \"{dump(ev)}\"\n" for ev in sf.HOOK_EVENTS))
        out = d / "out"; (out / "raw/de").mkdir(parents=True); (out / "raw/de/01.png").write_bytes(b"x")
        (out / "check.json").write_text(json.dumps({"problems": ["a", "b"]}))
        (out / "run.json").write_text(json.dumps({"config": str(d / "shotfleet.toml"), "platform": "ios", "locales": {"de": {"ok": True}}}))
        with mock.patch.object(sf, "NO_HOOKS", False), mock.patch.object(sf.shutil, "which", return_value="/usr/bin/maestro"), \
             mock.patch.object(sf, "capture_platform", return_value=0), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sf.run_platform(d / "shotfleet.toml", ["de"], None, "ios"), 0)
            (out / "check.json").write_text(json.dumps({"problems": []}))
            self.assertEqual(sf.export_with_hooks(out, d / "fl"), 0)
        def seen(ev):
            got = {l.split("=", 1)[0].removeprefix("SHOTFLEET_"): l.split("=", 1)[1] for l in (d / f"{ev}.env").read_text().splitlines()}
            return {k: v for k, v in got.items() if k in self.NAMES}
        self.assertEqual(set(seen("before_run")), {"EVENT", "VERSION", "CONFIG", "PLATFORM", "OUT", "BUNDLE_ID", "LOCALES"})
        self.assertEqual(set(seen("after_run")), {"EVENT", "VERSION", "CONFIG", "PLATFORM", "OUT", "BUNDLE_ID", "LOCALES", "EXIT", "PROBLEMS", "REPORT"})
        self.assertEqual(set(seen("before_export")), {"EVENT", "VERSION", "CONFIG", "PLATFORM", "OUT", "FASTLANE", "REPORT"})
        self.assertEqual(set(seen("after_export")), {"EVENT", "VERSION", "CONFIG", "PLATFORM", "OUT", "FASTLANE", "REPORT", "EXIT"})
        self.assertEqual((seen("before_run")["LOCALES"], seen("before_run")["BUNDLE_ID"]), ("de", "com.example.my"))
        self.assertEqual((seen("after_run")["EXIT"], seen("after_run")["PROBLEMS"]), ("0", "2"))


class G1StatusBar(unittest.TestCase):
    """C010: the commands that fix the status bar to 9:41 and a full battery are sent to every simulator and emulator
    (what the pictures show is the evidence in the claim)."""
    def test_ios_status_bar_override_on_every_simulator(self):
        calls = []
        class FakeSim:
            def __init__(self, udid): self.udid = udid
            def run(self, *a, check=True): calls.append(a); return ""
        with mock.patch.object(sf, "sh", side_effect=lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, json.dumps({"devices": {"rt": []}}) if "list" in cmd else "U1", "")), \
             mock.patch.object(sf, "Sim", FakeSim), mock.patch.object(sf, "OUR_SIMS", set()):
            sf.make_pool(1, "dt", "rt")
        bar = next(c for c in calls if c[0] == "status_bar")
        self.assertEqual(bar[2], "override")
        for flag, value in (("--time", "9:41"), ("--batteryState", "charged"), ("--batteryLevel", "100")):
            self.assertEqual(bar[bar.index(flag) + 1], value)

    def test_android_demo_mode_fixes_the_clock_and_battery(self):
        joined = "\n".join(sf.DEMO_MODE)
        self.assertIn("clock -e hhmm 0941", joined); self.assertIn("battery -e level 100 -e plugged false", joined)
        self.assertIn("notifications -e visible false", joined)


class G1NothingLeavesTheMac(unittest.TestCase):
    """C004: the only network calls in the program are a local driver call, one version lookup and the licence calls; `check` and `export`
    work with the network cut off (so no screenshot or app file is sent anywhere)."""
    def test_every_network_call_site_is_a_known_one(self):
        tree = ast.parse((Path(sf.__file__).resolve()).read_text())
        owners = {fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef)
                  and any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "urlopen" for n in ast.walk(fn))}
        # download and fetch_text are only for `doctor --fix` (test_downloads_are_only_reachable_from_doctor_fix)
        self.assertEqual(owners, {"ios_screen_texts", "latest_release", "polar_post", "gumroad_verify", "licence_api", "download", "fetch_text"})

    def test_downloads_are_only_reachable_from_doctor_fix(self):
        tree = ast.parse((Path(sf.__file__).resolve()).read_text())
        fetchers = {"download", "fetch_text"}
        callers = {fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef) and fn.name not in fetchers
                   and any(isinstance(n, ast.Call) and getattr(n.func, "id", "") in fetchers for n in ast.walk(fn))}
        self.assertEqual(callers, {"install_maestro", "install_jre", "install_cmdline_tools"})
        # ...and those are called from nowhere but the fix plan
        installers = callers
        users = {fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef) and fn.name not in installers
                 and any(isinstance(n, ast.Name) and n.id in installers for n in ast.walk(fn))}
        self.assertEqual(users, {"fix_plan"})

    def test_check_and_export_run_with_the_network_cut_off(self):
        def no_net(*a, **k): raise AssertionError("network used")
        with mock.patch.object(sf.urllib.request, "urlopen", no_net), mock.patch("socket.socket.connect", no_net), mock.patch("socket.create_connection", no_net):
            code, report, _ = g1_check(G1CheckDetectors.CLEAN)
            self.assertEqual(code, 0)
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "out"; (out / "raw/de").mkdir(parents=True); (out / "raw/de/01.png").write_bytes(png_c(1320, 2868))
                (out / "run.json").write_text(json.dumps({"platform": "ios", "locales": {"de": {"ok": True}}})); (out / "check.json").write_text(json.dumps({"problems": []}))
                with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(sf.cmd_export(out, Path(d) / "fl"), 0)
