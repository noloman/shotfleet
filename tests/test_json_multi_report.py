"""`--json` on a check over several reports (a multi-device run) prints ONE document covering all of them.
Real main -> check_any -> cmd_check; fake text recognition, no device, no Maestro.

Run: python3 -m unittest tests.test_json_multi_report
"""
import contextlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shotfleet as sf
from test_shotfleet import G1_SHOWS, G1_STRINGS, g1_image


class JsonMultiReport(unittest.TestCase):
    def run_json(self, devices):
        """devices: {device: {locale: lines}} under one multi-device run folder -> (exit code, parsed stdout)."""
        d = Path(tempfile.mkdtemp())
        for dev, locales in devices.items():
            (d / "out" / dev).mkdir(parents=True); (d / "out" / dev / "run.json").write_text("{}")
            for lp, lines in locales.items():
                png = d / "out" / dev / lp / "01.png"; png.parent.mkdir(parents=True)
                png.write_bytes(g1_image(f"{dev}/{lp}")); png.with_suffix(".texts.json").write_text(json.dumps(lines, ensure_ascii=False))
        for lp, words in G1_STRINGS.items():
            (d / "locales" / lp).mkdir(parents=True); (d / "locales" / lp / "translation.json").write_text(json.dumps(words, ensure_ascii=False))
        out = io.StringIO()
        with mock.patch.object(sf, "ocr_tool", return_value="ocr"), mock.patch.object(sf, "readable_languages", return_value={"en", "de", "ja"}), \
             mock.patch.object(sf, "warm_up_ocr", return_value=True), mock.patch.object(sf, "ipad_set_missing", return_value=0), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = sf.main(["check", str(d / "out"), "--strings", str(d / "locales/*/translation.json"), "--report", str(d / "rep"), "--json"])
        return code, json.loads(out.getvalue())

    GOOD = {"de": G1_SHOWS["de"], "en": G1_SHOWS["en"]}
    BAD = {"de": G1_SHOWS["en"], "en": G1_SHOWS["en"]}  # the German screen shows English

    def test_the_problem_of_the_first_report_is_not_lost(self):
        code, doc = self.run_json({"ipad": self.BAD, "iphone": self.GOOD})  # ipad sorts first: its report is not the last one
        self.assertEqual((code, doc["exit"]), (1, 1))
        self.assertTrue(doc["problems"], "exit is 1 but problems is empty")
        self.assertEqual([Path(r["report"]).parent.name for r in doc["reports"]], ["ipad", "iphone"])
        self.assertEqual(doc["reports"][0]["problems"], doc["problems"])
        self.assertEqual(doc["reports"][1]["problems"], [])
        self.assertEqual(len(doc["screenshots"]), 4)

    def test_a_single_report_keeps_its_exact_shape(self):
        code, doc = self.run_json({"iphone": self.BAD})
        self.assertEqual(code, 1)
        self.assertEqual(list(doc), ["exit", "screenshots", "problems", "notes"])
        self.assertTrue(doc["problems"])


if __name__ == "__main__":
    unittest.main()
