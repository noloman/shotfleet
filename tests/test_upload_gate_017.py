"""0.1.7 upload gate: the store coverage matrix, `check --compare`, and `export --print-upload`. No device, no network, fake text readers.

Run: python3 -m unittest tests.test_upload_gate_017
"""
import contextlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shotfleet as sf
from test_shotfleet import G1_SHOWS, G1_STRINGS, g1_check, g1_image, png_c

P69, P65, IPAD = (1320, 2868), (1284, 2778), (2064, 2752)


def make(root, spec):
    """{label: {name: size}} -> {label: [files]} of header-only PNGs."""
    out = {}
    for label, shots in spec.items():
        for name, size in shots.items():
            f = Path(root) / label / name; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(g1_image(f"{label}/{name}", size))
            out.setdefault(label, []).append(f)
    return out


def shots(n, size, prefix="s"): return {f"{prefix}{i}.png": size for i in range(n)}


class AppStoreMatrix(unittest.TestCase):
    def matrix(self, spec, ipad=True):
        return sf.coverage_matrix(make(tempfile.mkdtemp(), spec), False, ipad)

    def test_a_language_without_ipad_screenshots_is_missing_and_says_why(self):
        m = self.matrix({"en": {**shots(3, P69), **shots(3, IPAD, "i")}, "ja": shots(3, P69)})
        self.assertEqual(m["locales"]["en"]['iPad 13"'], {"status": "ok", "count": 3})
        self.assertEqual(m["locales"]["ja"]['iPad 13"']["status"], "missing")
        self.assertIn('ja: iPad 13" missing (the App Store needs it because your app runs on iPad)', m["summary"])
        self.assertEqual([s for s in m["summary"] if s.startswith("en")], [])

    def test_ipad_is_optional_when_the_app_does_not_run_on_ipad(self):
        m = self.matrix({"en": shots(3, P69)}, ipad=False)
        self.assertEqual(m["locales"]["en"]['iPad 13"']["status"], "optional")
        self.assertEqual(m["summary"], [])

    def test_the_65_inch_set_alone_is_enough_and_neither_is_missing(self):
        m = self.matrix({"en": shots(2, P65), "de": shots(2, P69), "fr": shots(2, (1179, 2556))}, ipad=False)
        self.assertEqual(m["locales"]["en"]['iPhone 6.9"']["status"], "optional")
        self.assertEqual(m["locales"]["fr"]['iPhone 6.9"']["status"], "missing")
        self.assertEqual(m["locales"]["fr"]['iPhone 6.5"']["status"], "missing")

    def test_more_than_ten_and_wrong_sizes(self):
        m = self.matrix({"en": {**shots(11, P69), "odd.png": (1000, 1000)}}, ipad=False)
        self.assertEqual(m["locales"]["en"]['iPhone 6.9"'], {"status": "too many", "count": 11})
        self.assertEqual(m["locales"]["en"]["other sizes"], {"status": "wrong size", "count": 1})
        self.assertIn('en: iPhone 6.9" has 11 screenshots (the App Store takes at most 10)', m["summary"])
        self.assertIn("en: 1 screenshot(s) aren't an App Store screenshot size", m["summary"])

    def test_unknown_store_has_no_matrix(self):
        self.assertIsNone(sf.coverage_matrix({"en": []}, None))


class PlayMatrix(unittest.TestCase):
    def matrix(self, **sets):
        root = tempfile.mkdtemp()
        return sf.coverage_matrix({k: make(Path(root) / k, v) for k, v in sets.items()}, True)

    def test_phone_and_tablet_cells(self):
        m = self.matrix(phoneScreenshots={"en": shots(8, (1080, 1920)), "de": shots(9, (1080, 1920)) },
                        sevenInchScreenshots={"en": shots(4, (1200, 1920)), "de": shots(2, (1200, 1920))},
                        tenInchScreenshots={"en": shots(4, (800, 1280))})
        cell = lambda l, c: m["locales"][l][c]
        self.assertEqual(m["columns"], ["phone", '7" tablet', '10" tablet'])
        self.assertEqual(cell("en", "phone"), {"status": "ok", "count": 8})
        self.assertEqual(cell("de", "phone"), {"status": "too many", "count": 9})
        self.assertEqual(cell("de", '7" tablet'), {"status": "missing", "count": 2})
        self.assertEqual(cell("en", '10" tablet'), {"status": "wrong size", "count": 4})  # under 1080 px
        self.assertIn("de: phone has 9 screenshots (Google Play takes at most 8 per device type)", m["summary"])
        self.assertIn('de: 7" tablet has 2 screenshot(s); Google asks for at least 4 for tablets', m["summary"])

    def test_a_language_with_only_tablet_shots_is_missing_its_phone_set_and_20_9_is_not_a_wrong_size(self):
        m = self.matrix(phoneScreenshots={"en": shots(1, (1080, 2400))}, sevenInchScreenshots={"ja": shots(4, (1200, 1920))})
        self.assertEqual(m["locales"]["en"]["phone"]["status"], "ok")
        self.assertEqual(m["locales"]["ja"]["phone"], {"status": "missing", "count": 0})
        self.assertIn("ja: no phone screenshots (Google Play needs at least two screenshots across device types)", m["summary"])


class CheckWritesTheMatrix(unittest.TestCase):
    CLEAN = {"de": {"01.png": G1_SHOWS["de"]}, "en": {"01.png": G1_SHOWS["en"]}}

    def test_check_json_console_and_html_carry_the_matrix_and_the_exit_code_is_unchanged(self):
        code, report, out = g1_check(self.CLEAN)
        self.assertEqual(code, 0)
        self.assertEqual(report["coverage"]["store"], "App Store")
        self.assertEqual(report["coverage"]["locales"]["de"]['iPhone 6.9"'], {"status": "ok", "count": 1})
        self.assertIn("App Store coverage (language x device class):", out)

    def test_the_html_report_has_the_table(self):
        d = Path(tempfile.mkdtemp())
        cov = sf.coverage_matrix(make(d, {"en": shots(2, P69)}), False, True)
        page = sf.coverage_html(cov)
        self.assertIn("<h2>App Store coverage</h2>", page)
        self.assertIn("missing", page)


class Compare(unittest.TestCase):
    def prev(self, label="de"):
        d = Path(tempfile.mkdtemp())
        for name, text in {"01.png": ["Weiter", "Einstellungen"], "02.png": ["Weiter", "Einstellungen", "Trainingsprotokoll"], "03.png": ["Weiter", "Einstellungen", "Weg"]}.items():
            f = d / label / name; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(g1_image(f"prev/{name}"))
            f.with_suffix(".texts.json").write_text(json.dumps(text, ensure_ascii=False))
        # 01 has the same bytes as the current one
        (d / label / "01.png").write_bytes(g1_image("de/01.png"))
        return d

    CUR = {"de": {"01.png": ["Weiter", "Einstellungen"], "02.png": ["Weiter", "Einstellungen", "Training starten"], "04.png": ["Weiter", "Einstellungen", "Hinzu"]}}

    def test_new_removed_changed_and_the_text_that_moved(self):
        code, report, out = g1_check(self.CUR, compare=self.prev())
        c = report["compare"]["locales"]["de"]
        self.assertEqual((c["new"], c["removed"]), (["04.png"], ["03.png"]))
        self.assertEqual(c["changed"], [{"screen": "02.png", "text": True, "text_added": ["Training starten"], "text_removed": ["Trainingsprotokoll"]}])
        self.assertEqual(report["compare"]["unchanged"], 1)
        self.assertIn("de/04.png: new", out); self.assertIn("de/03.png: removed", out)
        self.assertIn("de/02.png: changed (text added: 'Training starten'; text removed: 'Trainingsprotokoll')", out)

    def test_it_is_a_report_not_a_failure(self):
        code, report, _ = g1_check(self.CUR, compare=self.prev())
        self.assertEqual((code, report["problems"]), (0, []))

    def test_a_fastlane_folder_matches_by_store_code_and_has_no_text_to_compare(self):
        prev = Path(tempfile.mkdtemp())
        for n in ("01.png", "02.png"):
            f = prev / "screenshots/de-DE" / n; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(g1_image("old/" + n))
        code, report, out = g1_check({"de": {"01.png": ["Weiter", "Einstellungen"], "02.png": ["Weiter", "Einstellungen", "Neu"]}}, compare=prev)
        self.assertEqual([c["screen"] for c in report["compare"]["locales"]["de"]["changed"]], ["01.png", "02.png"])
        self.assertFalse(report["compare"]["locales"]["de"]["changed"][0]["text"])
        self.assertIn("de/01.png: changed (the picture; no text saved to compare)", out)

    def test_languages_only_on_one_side_are_named(self):
        _, report, _ = g1_check({"de": {"01.png": G1_SHOWS["de"]}, "ja": {"01.png": G1_SHOWS["ja"]}}, compare=self.prev("de"))
        self.assertEqual(report["compare"]["new_languages"], ["ja"])

    def test_a_missing_folder_is_a_clear_failure(self):
        with self.assertRaises(sf.Fail): sf.check_any(tempfile.mkdtemp(), compare="/no/such/folder")

    def test_no_compare_means_no_compare_key(self):
        _, report, out = g1_check(self.CUR)
        self.assertNotIn("compare", report); self.assertNotIn("compared with", out)


class PrintUpload(unittest.TestCase):
    def test_the_commands(self):
        self.assertEqual(sf.upload_command("fl", False), "fastlane deliver --screenshots_path fl/screenshots --skip_metadata --skip_binary_upload --overwrite_screenshots --force")
        self.assertEqual(sf.upload_command("my fl", True), "fastlane supply --metadata_path 'my fl/metadata/android' --skip_upload_apk --skip_upload_aab "
                                                            "--skip_upload_metadata --skip_upload_changelogs --skip_upload_images")

    def test_export_prints_them_only_when_asked_and_never_runs_anything(self):
        d = Path(tempfile.mkdtemp()); out = d / "out"
        (out / "raw/en").mkdir(parents=True); (out / "raw/en/01.png").write_bytes(g1_image("x"))
        (out / "run.json").write_text(json.dumps({"platform": "ios", "locales": {"en": {"ok": True}}}))
        (out / "check.json").write_text(json.dumps({"problems": []}))
        for flag, shown in (([], False), (["--print-upload"], True)):
            buf = io.StringIO()
            with mock.patch.object(sf, "sh") as sh, mock.patch.object(sf.subprocess, "run") as run, \
                 contextlib.redirect_stdout(buf):
                code = sf.main(["export", str(out), "--fastlane", str(d / "fl"), "--no-hooks", *flag])
            self.assertEqual(code, 0)
            self.assertEqual("fastlane deliver" in buf.getvalue(), shown)
            sh.assert_not_called(); run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
