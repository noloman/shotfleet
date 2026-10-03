"""Translations written as an object in code (Ignite, i18n-js, vue-i18n): read as data, never executed."""
import contextlib, io, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shotfleet as sf

IGNITE_EN = '''import { Translations } from "./en"
/* the English texts */
const en = {
  common: {
    ok: "OK!",   // trailing comment with "quotes"
    cancel: 'Cancel',
    "back": `Back`,
  },
  welcomeScreen: {
    postscript:
      "psst  \\u2014 This isn't what your app looks like. (ship it!)",
    long: "one " + "two " +
      "three",
    items: ["First", "Second"],
  },
  errorScreen: { title: "Something went wrong!", retry: t("retry"), count: 3 },
}

export default en
export type Translations = typeof en
'''


class ParseObject(unittest.TestCase):
    def test_ignite_style_file(self):
        tree, skipped = sf.parse_js_translations(IGNITE_EN)
        self.assertEqual(tree["common"], {"ok": "OK!", "cancel": "Cancel", "back": "Back"})
        self.assertEqual(tree["welcomeScreen"]["postscript"], "psst  — This isn't what your app looks like. (ship it!)")
        self.assertEqual(tree["welcomeScreen"]["long"], "one two three")
        self.assertEqual(tree["welcomeScreen"]["items"], {"0": "First", "1": "Second"})
        self.assertEqual(tree["errorScreen"], {"title": "Something went wrong!"})
        self.assertEqual(sorted(skipped), ["count", "retry"])

    def test_export_default_module_exports_and_typed_constants(self):
        for src in ('export default { a: "x" }', 'module.exports = { a: "x" }', 'const de: Translations = { a: "x" } as const;',
                    'export const messages = { a: "x" } satisfies Messages', 'export default defineMessages({ a: "x" })'):
            self.assertEqual(sf.parse_js_translations(src)[0], {"a": "x"}, src)

    def test_template_with_interpolation_and_code_are_skipped_not_guessed(self):
        tree, skipped = sf.parse_js_translations("export default { ok: 'fine', hi: `Hello ${name}`, f: (n) => 'x' + n, ...other, [k]: 'v' }")
        self.assertEqual(tree, {"ok": "fine"})
        self.assertEqual(len(skipped), 4)

    def test_comments_do_not_confuse_strings(self):
        tree, _ = sf.parse_js_translations('export default {\n  url: "http://example.com/a", // not a comment start inside the string\n  b: "/* keep */"\n}')
        self.assertEqual(tree, {"url": "http://example.com/a", "b": "/* keep */"})

    def test_a_file_without_an_object_is_an_error(self):
        for bad in ("export const x = 5", "", "const a = { b: 'open'"):
            with self.assertRaises(ValueError, msg=bad): sf.parse_js_translations(bad)


class ReadFiles(unittest.TestCase):
    def setUp(self): self.d = Path(tempfile.mkdtemp())

    def write(self, rel, text):
        f = self.d / rel; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(text); return f

    def read(self, f):
        with contextlib.redirect_stderr(io.StringIO()): return sf.read_translation_file(f, "en")

    def test_one_language_per_file(self):
        t = self.read(self.write("app/i18n/en.ts", IGNITE_EN))
        self.assertEqual(list(t), ["en"])
        self.assertEqual(t["en"]["common.ok"], "OK!")
        self.assertEqual(t["en"]["welcomeScreen.items.1"], "Second")

    def test_plural_keys_work_like_in_json(self):
        t = self.read(self.write("de.ts", "export default { items_one: '{{count}} Ding', items_other: '{{count}} Dinge' }"))
        self.assertEqual(t["de"], {"items#one": "{{count}} Ding", "items#other": "{{count}} Dinge"})

    def test_every_language_in_one_file(self):
        t = self.read(self.write("i18n.js", "export default { en: { hi: 'Hi' }, 'pt-BR': { hi: 'Oi' } }"))
        self.assertEqual(t, {"en": {"hi": "Hi"}, "pt-BR": {"hi": "Oi"}})

    def test_code_files_next_to_the_language_files_are_ignored(self):
        self.assertEqual(self.read(self.write("app/i18n/index.ts", "export const config = { debug: 'yes' }")), {})

    def test_a_file_that_is_not_a_translation_object_says_so(self):
        f = self.write("de.ts", "export const x = 5")
        with self.assertRaisesRegex(sf.Fail, "can't read de.ts"): sf.read_translation_file(f, "en")

    def test_load_strings_files_and_a_flow_translate_through_it(self):
        self.write("app/i18n/en.ts", "export default { common: { ok: 'OK!', cancel: 'Cancel' } }")
        self.write("app/i18n/de.ts", "export default { common: { ok: 'OK!', cancel: 'Abbrechen' } }")
        self.write("app/i18n/index.ts", "export const config = {}")
        with contextlib.redirect_stderr(io.StringIO()):
            s = sf.load_strings_files([str(self.d / "app/i18n/*.ts")])
        self.assertEqual(sorted(s), ["de", "en"])
        out, missing, _ = sf.translate_flow('- tapOn: "Cancel"\n', s["en"], s["de"])
        self.assertEqual(missing, []); self.assertIn("Abbrechen", out)

    def test_init_in_an_ignite_project_finds_the_files(self):
        import json
        self.write("package.json", json.dumps({"dependencies": {"react-native": "1", "expo": "1"}}))
        self.write("app/i18n/en.ts", "export default { a: 'x' }"); self.write("app/i18n/de.ts", "export default { a: 'y' }")
        self.write("app/i18n/index.ts", "export {}")
        self.assertEqual(sf.detect_project(self.d).strings, "app/i18n/*.ts")


if __name__ == "__main__":
    unittest.main()
