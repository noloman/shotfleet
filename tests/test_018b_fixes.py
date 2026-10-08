"""0.1.8 fixes from the dogfood runs of 2026-10-08: regex selectors in the strings pre-check, port 7001, a splash that never hides,
the failure screenshot after a retry. Fakes only: no simulator, emulator, Maestro, adb or text recognition.

Run: python3 -m unittest tests.test_018b_fixes
"""
import contextlib, io, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

EN = {"status": "%@ on %@", "round": "Round %d of %d", "hi": "Hello, {name}!", "save": "Save", "ok": "Done", "all": "%@"}
DE = {"status": "%@ am %@", "round": "Runde %d von %d", "hi": "Hallo, {name}!", "save": "Speichern", "ok": "Done"}


def quiet(fn, *a, **k):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        return fn(*a, **k), out.getvalue()


class RegexSelectorsInThePreCheck(unittest.TestCase):  # item 17
    def check(self, selector, base=EN, target=DE):
        only = []
        _, missing, _ = sf.translate_flow(f"appId: x\n---\n- assertVisible: {selector}\n", base, target, None, only)
        return missing, only

    def test_a_regex_built_from_a_format_string_warns_by_name(self):
        missing, only = self.check("'Interviewing on.*'")
        self.assertEqual(missing, []); self.assertEqual(only, [("Interviewing on.*", "%@ on %@")])

    def test_the_other_placeholder_styles_do_too(self):
        self.assertEqual(self.check("'Round [0-9]+ of .*'")[1], [("Round [0-9]+ of .*", "Round %d of %d")])
        self.assertEqual(self.check("'Hello, .*'")[1], [("Hello, .*", "Hello, {name}!")])
        self.assertEqual(self.check("'Sav.*'")[1], [("Sav.*", "Save")])
        base = {"a": "Hello, %1$s today"}
        self.assertEqual(self.check("'Hello, .* today'", base, {"a": "Hallo, %1$s heute"})[1], [("Hello, .* today", "Hello, %1$s today")])

    def test_a_regex_that_fits_no_app_text_is_still_not_found(self):
        self.assertEqual(self.check("'Nothing like [0-9]+.*'"), (["Nothing like [0-9]+"], []))
        self.assertEqual(self.check("'Nothing like [0-9]+'"), (["Nothing like [0-9]+"], []))

    def test_a_regex_that_reads_the_same_in_the_target_language_is_not_a_warning(self):
        self.assertEqual(self.check("'.*'"), ([], []))  # fits every text, in every language
        self.assertEqual(self.check("'Do.*'"), ([], []))  # "Done" is "Done" in German too

    def test_texts_the_app_has_are_translated_as_before(self):
        out, missing, _ = sf.translate_flow("appId: x\n---\n- assertVisible: '.*Save'\n- assertVisible: 'Round 2 of 12'\n", EN, DE, None, [])
        self.assertIn("'.*Speichern'", out); self.assertIn("Runde 2 von 12", out); self.assertEqual(missing, [])

    def test_a_placeholder_only_text_does_not_make_every_selector_a_hit(self):
        self.assertEqual(self.check("'Nothing here'"), (["Nothing here"], []))

    def test_run_prints_the_warning_with_the_fix(self):
        report = {"locales": {"de": {"untranslated_selectors": [], "base_only_selectors": [("Interviewing on.*", "%@ on %@")]},
                              "fr": {"untranslated_selectors": [], "base_only_selectors": [["Interviewing on.*", "%@ on %@"]]}}}
        _, text = quiet(sf.print_untranslated, report)
        self.assertEqual(text.count("Interviewing on.*"), 1)
        self.assertIn("'Interviewing on.*' matches '%@ on %@' in the base language only", text); self.assertIn("use an id", text)
