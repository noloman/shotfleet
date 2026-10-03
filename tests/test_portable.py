"""The parts of shotfleet that must not need macOS tools: reading .strings/.stringsdict/Info.plist without plutil and
PlistBuddy. They run on Linux, and on a Mac with the Apple tools hidden so the Python path is tested there too."""
import contextlib, io, json, plistlib, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

REAL_WHICH = sf.shutil.which
def no_apple_tools(cmd, *a, **k):
    return None if cmd in ("plutil", "/usr/libexec/PlistBuddy") else REAL_WHICH(cmd, *a, **k)


class StringsText(unittest.TestCase):
    def test_comments_escapes_and_unicode(self):
        t = ('/* Next button */\n"next" = "Weiter";\n// line comment\n"quote" = "He said \\"hi\\"\\nbye";\n'
             '"uni" = "\\U00e9\\u00fc";\n"jp" = "次へ";\n')
        self.assertEqual(sf.parse_strings_text(t), {"next": "Weiter", "quote": 'He said "hi"\nbye', "uni": "éü", "jp": "次へ"})

    def test_unquoted_keys_and_wrapped_dictionary(self):
        self.assertEqual(sf.parse_strings_text('{ Cancel = "Abbrechen"; "OK" = "OK"; }'), {"Cancel": "Abbrechen", "OK": "OK"})

    def test_empty_and_comment_only_files(self):
        self.assertEqual(sf.parse_strings_text(""), {})
        self.assertEqual(sf.parse_strings_text("/* nothing */\n"), {})

    def test_garbage_is_a_value_error(self):
        for bad in ('"a" = "b"', '"a" "b";', '"a" = "unterminated;', "/* open"):
            with self.assertRaises(ValueError, msg=bad): sf.parse_strings_text(bad)


class PlistFiles(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        patcher = mock.patch.object(sf.shutil, "which", no_apple_tools)
        patcher.start(); self.addCleanup(patcher.stop)

    def test_strings_in_utf8_utf16_and_binary_plist(self):
        (self.d / "a.strings").write_text('"k" = "ü";\n', encoding="utf-8")
        (self.d / "b.strings").write_bytes('\ufeff"k" = "ü";\n'.encode("utf-16"))
        (self.d / "c.strings").write_bytes(plistlib.dumps({"k": "ü"}, fmt=plistlib.FMT_BINARY))
        for n in "abc": self.assertEqual(sf.plist_to_json(self.d / f"{n}.strings"), {"k": "ü"}, n)

    def test_unreadable_file_is_none(self):
        (self.d / "x.strings").write_text("this is not a table")
        self.assertIsNone(sf.plist_to_json(self.d / "x.strings"))
        self.assertIsNone(sf.plist_to_json(self.d / "missing.strings"))

    def test_info_plist_values_print_like_plistbuddy(self):
        (self.d / "Info.plist").write_bytes(plistlib.dumps(
            {"CFBundleIdentifier": "com.x.app", "UIDeviceFamily": [1, 2], "DTPlatformName": "iphonesimulator"}))
        v = lambda k: sf.plist_value(self.d / "Info.plist", k)
        self.assertEqual(v("CFBundleIdentifier"), "com.x.app")
        self.assertIn("2", v("UIDeviceFamily"))
        self.assertEqual(v("Missing"), "")
        self.assertEqual(sf.plist_value(self.d / "nope.plist", "x"), "")

    def test_load_strings_reads_an_app_folder_without_plutil(self):
        for lp, word in (("en", "Next"), ("de", "Weiter")):
            (self.d / f"{lp}.lproj").mkdir()
            (self.d / f"{lp}.lproj" / "Localizable.strings").write_text(f'/* c */\n"next" = "{word}";\n')
        (self.d / "de.lproj" / "Localizable.stringsdict").write_bytes(plistlib.dumps(
            {"days": {"NSStringLocalizedFormatKey": "%#@d@", "d": {"NSStringFormatSpecTypeKey": "NSStringPluralRuleType",
                      "NSStringFormatValueTypeKey": "d", "one": "%d Tag", "other": "%d Tage"}}}))
        s = sf.load_strings(self.d)
        self.assertEqual(s["en"]["next"], "Next")
        self.assertEqual(s["de"]["next"], "Weiter")
        self.assertTrue(any("Tage" in v for v in s["de"].values()), s["de"])

    def test_strings_files_read_as_translation_sources(self):
        (self.d / "de.lproj").mkdir(); f = self.d / "de.lproj" / "Localizable.strings"; f.write_text('"next" = "Weiter";\n')
        self.assertEqual(sf.read_translation_file(f, "en"), {"de": {"next": "Weiter"}})


def png(w=1080, h=1920):  # just enough of a PNG for the size rules
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + b"\x08\x02\0\0\0"


class CheckWithoutMacOcr(unittest.TestCase):
    """`check` on Linux: no Vision, no Swift helper; Tesseract (or --ocr-command) reads every screenshot."""
    EN = {"a": "Next", "b": "Settings", "c": "Start Training"}
    DE = {"a": "Weiter", "b": "Einstellungen", "c": "Training starten"}

    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        for lp, words in (("en", self.EN), ("de", self.DE)):
            (self.d / lp).mkdir()
            (self.d / lp / "1.png").write_bytes(png()); (self.d / lp / "1.png.txt").write_text("\n".join(words.values()))
        (self.d / "de" / "2.png").write_bytes(png()); (self.d / "de" / "2.png.txt").write_text("\n".join(self.EN.values()))
        (self.d / "en" / "2.png").write_bytes(png()); (self.d / "en" / "2.png.txt").write_text("Home\nHistory\nProfile")
        for patcher in (mock.patch.object(sf, "is_mac", lambda: False),
                        mock.patch.object(sf, "ocr_tool", side_effect=AssertionError("the Swift helper must not be used"))):
            patcher.start(); self.addCleanup(patcher.stop)

    def run_check(self, **kw):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = sf.cmd_check(self.d, strings={"en": self.EN, "de": self.DE}, report_dir=self.d / "rep", **kw)
        return code, json.loads((self.d / "rep/check.json").read_text())

    def test_wrong_language_is_found_with_an_ocr_command_and_no_macos(self):
        code, report = self.run_check(ocr_command="cat {image}.txt")
        self.assertEqual(code, 1)
        self.assertTrue(any(p.startswith("de/2.png: shows en") for p in report["problems"]), report["problems"])
        self.assertFalse(any(p.startswith(("de/1.png", "en/1.png")) and "shows" in p for p in report["problems"]), report["problems"])

    def test_without_tesseract_it_says_how_to_install_it(self):
        with mock.patch.object(sf.shutil, "which", lambda c, *a, **k: None), mock.patch.dict(sf.os.environ, {}, clear=False):
            sf.os.environ.pop("SHOTFLEET_OCR", None)
            with self.assertRaises(sf.Fail) as e: self.run_check()
        self.assertIn("Tesseract", str(e.exception))

    def test_readable_languages_are_the_installed_tesseract_data(self):
        sf.readable_languages.cache_clear(); self.addCleanup(sf.readable_languages.cache_clear)
        with mock.patch.object(sf, "is_mac", lambda: False), mock.patch.object(sf, "tesseract_languages", lambda: frozenset({"eng", "deu", "chi_sim", "osd"})):
            self.assertEqual(sf.readable_languages(), {"en", "de", "zh"})

    def test_tesseract_gets_one_thread_so_parallel_runs_do_not_spin(self):
        self.assertEqual(sf.TESSERACT_ENV["OMP_THREAD_LIMIT"], "1")


class AndroidOnLinux(unittest.TestCase):
    def test_image_architecture_follows_the_cpu(self):
        for machine, abi in (("arm64", "arm64-v8a"), ("aarch64", "arm64-v8a"), ("x86_64", "x86_64"), ("AMD64", "x86_64")):
            self.assertEqual(sf.host_abi(machine), abi, machine)

    def test_find_image_takes_only_images_that_run_here(self):
        sdk = Path(tempfile.mkdtemp())
        for abi in ("arm64-v8a", "x86_64"):
            d = sdk / "system-images/android-36/google_apis" / abi; d.mkdir(parents=True); (d / "package.xml").write_text("")
        self.assertEqual(sf.find_image(sdk, abi="x86_64"), "system-images;android-36;google_apis;x86_64")
        self.assertEqual(sf.find_image(sdk, abi="arm64-v8a"), "system-images;android-36;google_apis;arm64-v8a")
        self.assertIsNone(sf.find_image(sdk, abi="riscv64"))

    def test_sdk_is_found_in_the_android_studio_folder_on_linux(self):
        home = Path(tempfile.mkdtemp()); (home / "Android/Sdk/platform-tools").mkdir(parents=True)
        with mock.patch.object(sf, "is_mac", lambda: False), mock.patch.object(sf.Path, "home", return_value=home):
            self.assertEqual(sf.find_sdk({"PATH": ""}), home / "Android/Sdk")

    def test_install_commands_on_linux_do_not_mention_homebrew(self):
        sdk = Path(tempfile.mkdtemp())
        with mock.patch.object(sf, "is_mac", lambda: False), mock.patch.object(sf, "cmdline_tool", lambda *a, **k: None):
            cmds = sf.sdkmanager_commands(["platform-tools"], sdk)
        self.assertFalse(any("brew" in c for c in cmds), cmds)
        self.assertIn("platform-tools", cmds[-1])

    def test_aapt2_from_the_path_is_used_when_the_sdk_has_none(self):
        with mock.patch.object(sf, "SDK", Path(tempfile.mkdtemp())), mock.patch.object(sf.shutil, "which", lambda c, *a, **k: "/usr/bin/aapt2" if c == "aapt2" else None):
            self.assertEqual(sf.aapt2(), "/usr/bin/aapt2")


if __name__ == "__main__":
    unittest.main()
