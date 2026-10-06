"""Patient text-recognition warm-up, its messages, and the Latin-script rule. Fake helper scripts only: no Vision, no
Tesseract, no Neural Engine; `ps` is mocked. Also the check-wide budget (unverified screens, --strict) and the per-Mac warm-up
lock (two real processes). Run: python3 -m unittest tests.test_ocr_wait"""
import contextlib, importlib.util, io, json, os, shutil, stat, struct, subprocess, sys, tempfile, textwrap, time, unittest, zlib
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp())
spec = importlib.util.spec_from_file_location("sf_ocr_wait", ROOT / "shotfleet.py")
sf = importlib.util.module_from_spec(spec); spec.loader.exec_module(sf)
sf.OCR_LOCK = str(TMP / "warmup.lock")  # never the Mac's real lock: a shotfleet run elsewhere on this Mac must not wait on the tests


def fake_helper(body):
    p = TMP / f"fake{len(list(TMP.glob('fake*')))}"
    p.write_text("#!/bin/sh\n" + textwrap.dedent(body))
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def ps(cpu, time_):
    return subprocess.CompletedProcess([], 0, f"{cpu} {time_} /System/.../ANECompilerService\n  0.0 0:01.00 /usr/bin/other\n", "")


class AneState(unittest.TestCase):
    def test_ps_time_formats(self):
        for t, minutes in (("18:10.86", 18.18), ("1:03:22.10", 63.37), ("2-03:00:00.00", 2 * 1440 + 180)):
            with mock.patch.object(sf, "sh", return_value=ps("97.0", t)):
                busy, m = sf.ane_state()
            self.assertTrue(busy); self.assertAlmostEqual(m, minutes, delta=0.05)

    def test_not_running_or_idle(self):
        with mock.patch.object(sf, "sh", return_value=subprocess.CompletedProcess([], 0, "  0.0 0:01.00 /usr/bin/other\n", "")):
            self.assertEqual(sf.ane_state(), (False, 0))
        with mock.patch.object(sf, "sh", return_value=ps("0.0", "18:10.86")):
            self.assertFalse(sf.ane_state()[0])

    def test_messages_tell_what_to_do(self):
        for state, must in (((True, 700), "looks stuck"), ((True, 5), "can take minutes"), ((False, 0), "overloaded")):
            with mock.patch.object(sf, "ane_state", return_value=state):
                self.assertIn(must, sf.ocr_not_answering())
        for must in ("Run check again later", "close heavy apps", "brew install tesseract", "No restart needed"):
            self.assertIn(must, sf.OCR_WHAT_TO_DO)


class WarmUp(unittest.TestCase):
    def run_warm(self, helper, state, **kw):
        t0 = time.time()
        with mock.patch.object(sf, "ane_state", return_value=state), mock.patch.object(sf, "OCR_LOCK", str(TMP / f"lock{time.time_ns()}")):
            return sf.warm_up_ocr(helper, **kw), time.time() - t0  # its own lock: a helper an earlier test left running holds its one

    def test_hung_and_idle_gives_up_at_timeout(self):
        ok, took = self.run_warm(fake_helper("sleep 30\n"), (False, 0), timeout=0.5, patience=20)
        self.assertFalse(ok); self.assertLess(took, 3)

    def test_slow_compile_is_waited_for_while_service_works(self):
        ok, took = self.run_warm(fake_helper("sleep 1.5; echo Ready\n"), (True, 5), timeout=0.5, patience=20)
        self.assertTrue(ok); self.assertGreater(took, 1.4)

    def test_patience_is_a_ceiling(self):
        ok, took = self.run_warm(fake_helper("sleep 30\n"), (True, 5), timeout=0.5, patience=2)
        self.assertFalse(ok); self.assertLess(took, 5)

    def test_stuck_service_is_not_waited_for(self):
        ok, took = self.run_warm(fake_helper("sleep 30\n"), (True, 700), timeout=0.5, patience=20)
        self.assertFalse(ok); self.assertLess(took, 3)

    def test_a_helper_that_exits_without_an_answer_is_started_again(self):  # first call fails, second answers
        flag = TMP / "warm-flag"
        h = fake_helper(f"if [ -e {flag} ]; then echo Ready; else touch {flag}; exit 1; fi\n")
        with mock.patch.object(sf, "OCR_RETRY_S", 0.2):
            ok, took = self.run_warm(h, (True, 5), timeout=5, patience=20)
        self.assertTrue(ok)

    def test_a_helper_that_always_fails_gives_up_at_timeout(self):
        with mock.patch.object(sf, "OCR_RETRY_S", 0.2):
            ok, took = self.run_warm(fake_helper("exit 1\n"), (False, 0), timeout=1.5)
        self.assertFalse(ok); self.assertLess(took, 4)

    def test_default_patience_is_off(self):  # callers and tests that pass only timeout behave as before
        ok, took = self.run_warm(fake_helper("sleep 30\n"), (True, 5), timeout=0.5)
        self.assertFalse(ok); self.assertLess(took, 3)


class ReadText(unittest.TestCase):
    def test_vision_failure_is_an_error_not_an_empty_screen(self):
        h = fake_helper("echo 'Vision failed: Code=13' >&2; exit 2\n")
        with mock.patch.object(sf, "ane_state", return_value=(False, 0)), self.assertRaisesRegex(RuntimeError, "Vision failed: Code=13"):
            sf.read_text(h, "x.png", timeout=5)

    def test_an_error_while_macos_compiles_is_retried_until_it_answers(self):  # the 2026-10-06 e5rtError 13 after a warm-up that answered
        flag = TMP / "read-flag"
        h = fake_helper(f"""if [ -e {flag} ]; then echo '{{"chars": 3}}'; else touch {flag}; echo 'e5rtError 13' >&2; exit 2; fi\n""")
        with mock.patch.object(sf, "OCR_RETRY_S", 0.2), mock.patch.object(sf, "ane_state", return_value=(True, 5)):
            self.assertEqual(sf.read_text(h, "x.png", timeout=5, patience=20)["chars"], 3)

    def test_that_retry_has_a_ceiling_and_skips_a_stuck_service(self):
        h = fake_helper("echo 'e5rtError 13' >&2; exit 2\n")
        with mock.patch.object(sf, "OCR_RETRY_S", 0.2):
            for state, patience in (((True, 5), 1), ((True, 700), 20)):
                with mock.patch.object(sf, "ane_state", return_value=state), self.assertRaisesRegex(RuntimeError, "e5rtError"):
                    t0 = time.time(); sf.read_text(h, "x.png", timeout=5, patience=patience)

    def test_good_answer(self):
        h = fake_helper("""echo '{"lang": "de", "chars": 3, "text": "abc"}'\n""")
        self.assertEqual(sf.read_text(h, "x.png", timeout=5)["chars"], 3)

    def test_a_compile_mid_check_is_waited_for(self):
        h = fake_helper("""sleep 1.5; echo '{"chars": 3}'\n""")
        with mock.patch.object(sf, "ane_state", return_value=(True, 5)):
            self.assertEqual(sf.read_text(h, "x.png", timeout=0.5, patience=20)["chars"], 3)

    def test_hang_is_retried_once_then_names_the_cause(self):
        h = fake_helper("exec sleep 30\n")  # one process, like the real helper: the kill ends it (a shell's child would hold the pipe 30 s)
        with mock.patch.object(sf, "ane_state", return_value=(True, 700)), self.assertRaisesRegex(RuntimeError, "stuck"):
            sf.read_text(h, "x.png", timeout=0.3)


class Languages(unittest.TestCase):
    """macOS 14's reader list (INFERENCE: 7 to 20 languages, no Catalan) on a Mac."""
    def judge(self, lp, ocr, listed=("en", "de")):
        with mock.patch.object(sf, "readable_languages", return_value=set(listed)), mock.patch.object(sf, "vision_available", return_value=True):
            return sf.judge_screen(lp, {"chars": 99, "text": "x", "ocr": "vision", **ocr}, sf.string_tables({"en": {"a": "Advanced"}, lp: {"a": "Avançat"}}))

    def test_catalan_screen_that_is_english_is_flagged_like_on_macos_15(self):
        got, problem = self.judge("ca", {"lang": "en", "langs": {"en": 0.862}})
        self.assertEqual(got, "en"); self.assertIn("text looks like 'en', expected 'ca'", problem)

    def test_real_catalan_passes(self):
        self.assertEqual(self.judge("ca", {"lang": "ca", "langs": {"ca": 0.97}}), ("ca", None))

    def test_croatian_read_as_slovenian_is_not_a_finding(self):
        self.assertEqual(self.judge("hr", {"lang": "sl", "langs": {"sl": 0.9, "hr": 0.05}}), ("hr", None))

    def test_unreadable_script_is_still_skipped(self):
        self.assertEqual(self.judge("el", {"lang": "en", "langs": {"en": 0.862}}), (None, None))

    def test_not_on_linux(self):  # Tesseract names no language, so the Latin rule is for macOS only
        with mock.patch.object(sf, "readable_languages", return_value={"en"}), mock.patch.object(sf, "vision_available", return_value=False):
            self.assertFalse(sf.can_read("ca"))


def real_png(w, h):
    """A decodable PNG with rows of 'glyphs' (not blank to blank_screenshot)."""
    px = lambda x, y: (0, 0, 0) if (y // 6) % 3 == 0 and x % (5 + y % 7) < 3 and 40 < y < 260 else (255, 255, 255)
    raw = b"".join(b"\0" + b"".join(bytes(px(x, y)) for x in range(w)) for y in range(h))
    chunk = lambda k, d: struct.pack(">I", len(d)) + k + d + b"\0\0\0\0"
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class Budget(unittest.TestCase):
    """One OCR budget per check: when it runs out, check finishes and lists what it didn't read (2-second budget here)."""
    STRINGS = {"en": {"a": "Next", "b": "Settings", "c": "Start Training"},
               "de": {"a": "Weiter", "b": "Einstellungen", "c": "Training starten"},
               "ja": {"a": "次へ", "b": "設定", "c": "トレーニング開始"}}

    def setUp(self):
        self.d = Path(tempfile.mkdtemp(dir=TMP))
        for lp in ("de", "ja"):
            png = self.d / "shots" / lp / "01.png"; png.parent.mkdir(parents=True); png.write_bytes(real_png(60, 300))
        (self.d / "shots/de/01.texts.json").write_text(json.dumps(list(self.STRINGS["de"].values())))  # the app's own text: de is judged
        for lp, t in self.STRINGS.items():
            f = self.d / "locales" / lp / "translation.json"; f.parent.mkdir(parents=True); f.write_text(json.dumps(t, ensure_ascii=False))
        # warms up at once, then every read fails with macOS's compile error (the 2026-10-06 e5rt error 13), for ever
        self.helper = fake_helper('if [ "$1" = --warmup ]; then echo Ready; exit 0; fi\necho "e5rt: E5RT: error code 13" >&2; exit 2\n')

    def patches(self, helper=None):
        which = shutil.which
        return [mock.patch.object(sf, "is_mac", lambda: True), mock.patch.object(sf, "ocr_tool", return_value=helper or self.helper),
                mock.patch.object(sf, "ane_state", return_value=(True, 5)), mock.patch.object(sf, "OCR_BUDGET_S", 2),
                mock.patch.object(sf, "OCR_RETRY_S", 0.2), mock.patch.object(sf, "OCR_LOCK", str(TMP / f"lock{time.time_ns()}")),
                mock.patch.object(sf, "readable_languages", return_value={"en", "de", "ja"}),
                mock.patch.object(sf, "tesseract_languages", return_value=frozenset()), mock.patch.object(sf, "store_rules", return_value=([], [])),
                mock.patch.object(sf.shutil, "which", lambda c, *a, **k: None if c == "tesseract" else which(c, *a, **k))]

    def main(self, *extra, helper=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as st:
            for p in self.patches(helper): st.enter_context(p)
            st.enter_context(mock.patch.dict(os.environ)); os.environ.pop("SHOTFLEET_OCR", None)
            st.enter_context(contextlib.redirect_stdout(out)); st.enter_context(contextlib.redirect_stderr(err))
            t0 = time.time()
            code = sf.main(["check", str(self.d / "shots"), "--strings", str(self.d / "locales/*/translation.json"),
                            "--report", str(self.d / "rep"), *extra])
        return code, out.getvalue(), err.getvalue(), time.time() - t0

    def test_the_budget_ends_the_waiting_and_check_finishes_with_unverified_screens(self):
        code, out, _, took = self.main()
        self.assertEqual(code, 0); self.assertLess(took, 8)  # not exit 2, and not 6 minutes per screen
        report = json.loads((self.d / "rep/check.json").read_text())
        self.assertEqual(report["unverified"], ["ja/01.png"])
        self.assertEqual(report["problems"], [])
        self.assertIn("ja/01.png: not verified (macOS text recognition was busy)", report["notes"])
        for must in ("1 not verified", "NOT VERIFIED: 1 screenshot(s) not verified, because macOS text recognition was busy",
                     "Run check again later", "brew install tesseract", "No restart needed"):
            self.assertIn(must, out)
        self.assertNotIn("can't read the script of", out)
        self.assertIn("Not verified (1)", (self.d / "rep/index.html").read_text())

    def test_texts_json_screens_are_still_judged(self):  # de shows English in its app text: still a problem, exit 1
        (self.d / "shots/de/01.texts.json").write_text(json.dumps(list(self.STRINGS["en"].values())))
        code, *_ = self.main()
        report = json.loads((self.d / "rep/check.json").read_text())
        self.assertEqual(code, 1)
        self.assertTrue(any(p.startswith("de/01.png: shows en") for p in report["problems"]), report["problems"])
        self.assertEqual(report["unverified"], ["ja/01.png"])

    def test_json_carries_unverified_and_strict_makes_it_exit_1(self):
        for extra, want in (((), 0), (("--strict",), 1)):
            code, out, err, _ = self.main("--json", *extra)
            doc = json.loads(out)
            self.assertEqual((code, doc["exit"], doc["unverified"], doc["problems"]), (want, want, ["ja/01.png"], []))
        self.assertIn("--strict: exit 1", err)

    def test_a_warm_up_that_never_answers_also_ends_in_unverified_not_exit_2(self):
        code, out, _, took = self.main(helper=fake_helper("exec sleep 30\n"))
        self.assertEqual(code, 0); self.assertLess(took, 8)
        self.assertEqual(json.loads((self.d / "rep/check.json").read_text())["unverified"], ["ja/01.png"])

    def test_identical_unverified_screens_are_a_note_not_a_copy_problem(self):  # games and no-text screens are identical by design
        (self.d / "shots/de/01.texts.json").unlink()  # de and ja: the same bytes, neither read
        code, out, *_ = self.main()
        report = json.loads((self.d / "rep/check.json").read_text())
        self.assertEqual((code, report["problems"], report["unverified"]), (0, [], ["de/01.png", "ja/01.png"]))
        self.assertIn("2 unverified screens are identical across languages; run check again when text recognition answers to tell "
                      "whether they're copies (de/01.png, ja/01.png)", report["notes"])

    def test_read_text_stops_at_the_budget(self):
        with mock.patch.object(sf, "ane_state", return_value=(True, 5)), mock.patch.object(sf, "OCR_RETRY_S", 0.2), \
             mock.patch.object(sf, "OCR_BUDGET_S", 1.5), sf.ocr_budget(), self.assertRaises(sf.OcrBusy):
            t0 = time.time()
            try: sf.read_text(self.helper, "x.png", timeout=60, patience=360)
            finally: self.assertLess(time.time() - t0, 4)


LOCK_CHILD = """import importlib.util, sys
spec = importlib.util.spec_from_file_location("sf", sys.argv[1]); sf = importlib.util.module_from_spec(spec); spec.loader.exec_module(sf)
sf.OCR_LOCK, sf.ane_state = sys.argv[2], lambda: (True, 5)
print("warm", sf.warm_up_ocr(sys.argv[3], timeout=30, patience=30), flush=True)
"""


class WarmUpLock(unittest.TestCase):
    """One warm-up per Mac at a time, across processes (real processes, fake helpers)."""
    def test_two_warm_ups_take_turns(self):
        log = TMP / "turns.log"
        h = fake_helper(f'echo start >> {log}; sleep 3; echo end >> {log}; echo Ready\n')
        start = lambda: subprocess.Popen([sys.executable, "-c", LOCK_CHILD, str(ROOT / "shotfleet.py"), sf.OCR_LOCK, h],
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        first = start()
        deadline = time.time() + 30  # start the second only once the first holds the lock and its helper runs, so it must wait
        while not (log.exists() and "start" in log.read_text()) and time.time() < deadline: time.sleep(0.05)
        kids = [first, start()]
        outs = [k.communicate(timeout=60)[0] for k in kids]
        self.assertTrue(all("warm True" in o for o in outs), outs)
        self.assertEqual(log.read_text().split(), ["start", "end", "start", "end"])  # never two helpers at once
        self.assertEqual(sum("another shotfleet is preparing macOS text recognition; waiting" in o for o in outs), 1)

    def test_the_wait_for_the_lock_counts_against_the_budget(self):
        flag = TMP / "helper-ran"
        holder = subprocess.Popen([sys.executable, "-c", "import fcntl, sys, time; f = open(sys.argv[1], 'w'); fcntl.flock(f, fcntl.LOCK_EX); "
                                   "print('held', flush=True); time.sleep(60)", sf.OCR_LOCK], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(holder.stdout.readline().strip(), "held")
            out = io.StringIO()
            with mock.patch.object(sf, "ane_state", return_value=(True, 5)), mock.patch.object(sf, "OCR_BUDGET_S", 2), \
                 sf.ocr_budget(), contextlib.redirect_stdout(out):
                t0 = time.time(); ok = sf.warm_up_ocr(fake_helper(f"touch {flag}; echo Ready\n"), timeout=600, patience=360)
            self.assertFalse(ok); self.assertLess(time.time() - t0, 5)
            self.assertFalse(flag.exists())  # it never started a helper of its own
            self.assertIn("another shotfleet is preparing macOS text recognition; waiting", out.getvalue())
        finally:
            holder.kill(); holder.wait(); holder.stdout.close()


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
