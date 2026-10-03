"""The parts of shotfleet that must not need macOS tools: reading .strings/.stringsdict/Info.plist without plutil and
PlistBuddy. They run on Linux, and on a Mac with the Apple tools hidden so the Python path is tested there too."""
import plistlib, sys, tempfile, unittest
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


if __name__ == "__main__":
    unittest.main()
