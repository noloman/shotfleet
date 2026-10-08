"""0.1.8 fixes from the dogfood runs of 2026-10-08: regex selectors in the strings pre-check, port 7001, a splash that never hides,
the failure screenshot after a retry. Fakes only: no simulator, emulator, Maestro, adb or text recognition.

Run: python3 -m unittest tests.test_018b_fixes
"""
import contextlib, io, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

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


def fake_sh(lsof="", ps="", fail=None):
    """sf.sh with lsof and ps answered from here: no real port is looked at."""
    def sh(cmd, **kw):
        if fail and cmd[0] == "lsof": raise fail
        return SimpleNamespace(stdout={"lsof": lsof, "ps": ps}[cmd[0]], stderr="", returncode=0)
    return mock.patch.object(sf, "sh", side_effect=sh)


class Port7001(unittest.TestCase):  # item 22
    JAVA = "java -Dapple.awt.UIElement=true -classpath /opt/maestro/lib/maestro-cli.jar maestro.cli.AppKt --device 6A7B test flow"
    UNAVAILABLE = "[Failed] de (25s) (io.grpc.StatusRuntimeException: UNAVAILABLE: io exception)"

    def test_the_holder_is_read_from_lsof_and_ps(self):
        with fake_sh("p4321\n", self.JAVA + "\n"):
            pid, cmd = sf.port_7001_holder()
        self.assertEqual(pid, 4321); self.assertTrue(cmd.startswith("java -Dapple.awt.UIElement=true")); self.assertLessEqual(len(cmd), 90)

    def test_nobody_listening_and_no_lsof_both_give_none(self):
        with fake_sh(""): self.assertIsNone(sf.port_7001_holder())
        with fake_sh(fail=FileNotFoundError("lsof")): self.assertIsNone(sf.port_7001_holder())
        with fake_sh(fail=subprocess.TimeoutExpired("lsof", 15)): self.assertIsNone(sf.port_7001_holder())

    def test_the_message_says_it_in_plain_words_and_names_pid_and_command(self):
        self.assertEqual(sf.port_7001_message((4321, self.JAVA[:20] + " maestro")), "port 7001 is already used by another Maestro driver (pid 4321, java -Dapple.awt.UIE maestro)")
        self.assertIn("another program (pid 7, node server.js)", sf.port_7001_message((7, "node server.js")))

    def test_a_run_warns_before_it_starts_and_stops_nothing(self):
        with fake_sh("p4321\n", self.JAVA), mock.patch.object(sf, "kill_stale_drivers", side_effect=AssertionError("kills nothing")):
            _, text = quiet(sf.warn_port_7001)
        self.assertIn("port 7001 is already used by another Maestro driver (pid 4321, java", text); self.assertIn("does not stop it", text)
        with fake_sh(""): self.assertEqual(quiet(sf.warn_port_7001)[1], "")

    def test_a_failure_that_says_unavailable_gets_the_reason(self):
        with tempfile.TemporaryDirectory() as d, fake_sh("p4321\n", self.JAVA):
            note = sf.port_clash_note(d, ["Assertion is false", self.UNAVAILABLE])
            (Path(d) / "maestro1.log").write_text("io.grpc.StatusRuntimeException: UNAVAILABLE: io exception\n")
            from_log = sf.port_clash_note(d, ["no result (see maestro log)"])
        for got in (note, from_log):
            self.assertIn("port 7001 is already used by another Maestro driver (pid 4321, java", got); self.assertTrue(got.endswith("\n"))

    def test_a_clash_found_after_the_other_job_ended_is_still_explained(self):
        with tempfile.TemporaryDirectory() as d, fake_sh(""):
            got = sf.port_clash_note(d, [self.UNAVAILABLE])
        self.assertIn("nothing listens there now", got); self.assertIn("one job at a time", got)

    def test_other_failures_get_no_note_and_no_lsof_call(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(sf, "sh", side_effect=AssertionError("no lookup")):
            self.assertEqual(sf.port_clash_note(d, ["Assertion is false: id: login is visible", None]), "")


PKG = "com.obytes.development"
WINDOWS = """WINDOW MANAGER WINDOWS (dumpsys window windows)
  Window #4 Window{5d1 u0 NavigationBar0}:
    isReadyForDisplay()=true
%s  Window #2 Window{9f3 u0 com.obytes.development/com.obytes.MainActivity}:
    isReadyForDisplay()=false
"""
SPLASH_WINDOW = "  Window #3 Window{1a2b3c u0 Splash Screen com.obytes.development}:\n    mHasSurface=true isReadyForDisplay()=true\n"
RECORD = """  ActivityRecord{77aa u0 com.obytes.development/.MainActivity t12}:
    app=ProcessRecord{b1 4242:com.obytes.development/u0a190}
    %s
    startingDisplayed=%s startingMoved=false
    reportedDrawn=%s reportedVisible=false
"""


class StuckSplash(unittest.TestCase):  # item 24, Android
    def test_a_splash_window_that_is_still_up_is_found(self):
        self.assertTrue(sf.splash_showing(WINDOWS % SPLASH_WINDOW, PKG))
        self.assertTrue(sf.splash_showing(WINDOWS % SPLASH_WINDOW.replace("Splash Screen", "Starting"), PKG))  # before Android 12

    def test_a_normal_screen_and_other_apps_splashes_are_not(self):
        self.assertFalse(sf.splash_showing(WINDOWS % "", PKG))
        self.assertFalse(sf.splash_showing(WINDOWS % SPLASH_WINDOW.replace(PKG, "com.other.app"), PKG))
        self.assertFalse(sf.splash_showing(WINDOWS % SPLASH_WINDOW.replace(PKG, PKG + ".debug"), PKG))  # another package that starts with ours

    def test_an_activity_that_never_reported_drawn_behind_its_starting_window_is_found(self):
        self.assertTrue(sf.splash_showing(RECORD % ("startingWindow=Window{1 u0 splash}", "true", "false"), PKG))
        self.assertFalse(sf.splash_showing(RECORD % ("startingWindow=null", "false", "false"), PKG))  # not drawn, but no splash: not our message
        self.assertFalse(sf.splash_showing(RECORD % ("startingWindow=null", "false", "true"), PKG))
        self.assertFalse(sf.splash_showing(RECORD % ("", "true", "false"), "com.other.app"))

    def emulator(self, dump=None, error=None):
        calls = []
        def adb(*args, **kw):
            calls.append(args)
            if error: raise error
            return dump
        return SimpleNamespace(adb=adb, calls=calls)

    def test_the_check_asks_the_emulator_for_the_window_list_and_gives_up_quietly(self):
        e = self.emulator(WINDOWS % SPLASH_WINDOW)
        self.assertTrue(sf.app_splash_showing(e, PKG)); self.assertEqual(e.calls, [("shell", "dumpsys", "window")])
        self.assertFalse(sf.app_splash_showing(self.emulator(WINDOWS % ""), PKG))
        self.assertFalse(sf.app_splash_showing(self.emulator(error=RuntimeError("not responding")), PKG))

    def test_the_failure_message_says_so_and_calls_the_listed_texts_hidden(self):
        from tests.test_failure_messages import debug_dir, FLOW
        with tempfile.TemporaryDirectory() as d:
            debug_dir(d)
            got = sf.failure_details(d, "en", FLOW, "android", True)
            plain = sf.failure_details(d, "en", FLOW, "android")
        self.assertIn("the app's splash screen is still showing; taps can't reach the app", got)
        self.assertTrue(any(l.startswith("behind the splash, the screen tree lists: AnywhereRoles") for l in got)); self.assertFalse(any(l.startswith("on screen") for l in got))
        self.assertTrue(any(l.startswith("on screen: AnywhereRoles") for l in plain)); self.assertNotIn(sf.SPLASH_LINE, plain)


class PictureVersusTree(unittest.TestCase):  # item 24, iOS
    def details(self, seen, platform="ios"):
        from tests.test_failure_messages import debug_dir, FLOW
        with tempfile.TemporaryDirectory() as d:
            debug_dir(d)
            with mock.patch.object(sf, "screenshot_texts", return_value=seen) as ocr:
                return sf.failure_details(d, "en", FLOW, platform), ocr

    def test_a_picture_that_shows_none_of_the_trees_texts_is_said(self):
        got, ocr = self.details(["Loading", "Please wait"])
        line = next(l for l in got if l.startswith("the picture shows other text than the screen tree lists"))
        self.assertIn("The picture reads: Loading | Please wait.", line); self.assertIn("The tree lists: AnywhereRoles | Filter jobs | 4 jobs", line)
        self.assertIn("splash screen", line); self.assertTrue(any(l.startswith("on screen: AnywhereRoles") for l in got)); ocr.assert_called_once()

    def test_a_picture_that_shows_the_trees_texts_says_nothing_more(self):
        got, _ = self.details(["anywhereroles", "4 Jobs", "Something else"])
        self.assertFalse(any("other text" in l for l in got))

    def test_nothing_read_from_the_picture_says_nothing_more(self):
        self.assertFalse(any("other text" in l for l in self.details([])[0]))

    def test_android_does_not_read_the_picture_when_the_tree_has_texts(self):
        got, ocr = self.details(["Loading"], "android")
        ocr.assert_not_called(); self.assertFalse(any("other text" in l for l in got))


class FailureScreenshotKept(unittest.TestCase):  # item 25
    def folders(self, shots=(True, True)):
        """An output folder with the debug folders of two tries (attempt1, attempt2); shots says which of them saved a failure screenshot."""
        from tests.test_failure_messages import debug_dir
        out = Path(tempfile.mkdtemp()); self.addCleanup(lambda: __import__("shutil").rmtree(out, ignore_errors=True))
        tries = []
        for i, shot in enumerate(shots, 1):
            d = out / ".work" / "debug" / f"attempt{i}"
            png = debug_dir(d, flow="de", shot=shot)
            if shot: png.write_bytes(b"\x89PNG try %d" % i)
            tries.append((d, "de"))
        return out, tries[::-1]  # latest first

    def test_the_retrys_picture_is_copied_to_a_named_file_and_named_in_the_message(self):
        out, tries = self.folders()
        kept = sf.keep_failure_screenshot(out, "de", tries)
        self.assertEqual(kept, out / "failures" / "de.png"); self.assertEqual(kept.read_bytes(), b"\x89PNG try 2")
        got = sf.failure_details(*tries[0], kept=kept)
        self.assertIn(f"failure screenshot: {kept}", got); self.assertFalse(any(".maestro" in l for l in got))

    def test_it_stays_when_the_debug_folders_are_cleared(self):
        out, tries = self.folders()
        kept = sf.keep_failure_screenshot(out, "de", tries)
        __import__("shutil").rmtree(out / ".work")  # the next run does this
        self.assertTrue(kept.is_file())

    def test_when_the_retry_saved_no_picture_the_first_tries_is_kept_and_says_so(self):
        out, tries = self.folders((True, False))
        kept = sf.keep_failure_screenshot(out, "de", tries)
        self.assertEqual(kept.name, "de-first-try.png"); self.assertEqual(kept.read_bytes(), b"\x89PNG try 1")
        self.assertIn(f"failure screenshot: {kept} (the first try's: the retry saved none)", sf.failure_details(*tries[0], kept=kept))
        self.assertEqual(sf.keep_failure_screenshot(out, "de", [None, tries[1]]).name, "de-first-try.png")  # a missing try is skipped, not an error

    def test_a_language_that_passed_loses_an_old_picture_and_no_picture_makes_no_folder(self):
        out, tries = self.folders()
        sf.keep_failure_screenshot(out, "de", tries); (out / "failures" / "de-first-try.png").write_bytes(b"old")
        self.assertIsNone(sf.keep_failure_screenshot(out, "de", []))
        self.assertEqual(list((out / "failures").iterdir()), [])
        out2, tries2 = self.folders((False, False))
        self.assertIsNone(sf.keep_failure_screenshot(out2, "de", tries2)); self.assertFalse((out2 / "failures").exists())

    def test_other_languages_pictures_are_left_alone(self):
        out, tries = self.folders()
        (out / "failures").mkdir(); (out / "failures" / "ja.png").write_bytes(b"ja")
        sf.keep_failure_screenshot(out, "de", tries)
        self.assertEqual((out / "failures" / "ja.png").read_bytes(), b"ja")


class FailureKeptInARun(unittest.TestCase):  # item 25, a whole iOS run on the 0.1.7 fakes
    def setUp(self):
        from tests import test_reliability_017 as r17
        if sys.platform != "darwin": self.skipTest("iOS run path is macOS only")
        self.run_ = r17.IosRetries("run_it"); self.run_.setUp(); self.addCleanup(self.run_.doCleanups)
        self.calls, plain = 0, self.run_.fake_maestro
        def maestro(cmd, **kw):
            """The fake Maestro, plus the failure screenshot Maestro leaves in --debug-output (only on the calls in self.pictures)."""
            self.calls += 1
            done = plain(cmd, **kw)
            if self.calls in self.pictures:
                junit = Path(cmd[cmd.index("--output") + 1]).read_text()
                for lp in re.findall(r'<testcase name="(\w+)" time="2"><failure>', junit):
                    shot = Path(cmd[cmd.index("--debug-output") + 1]) / ".maestro/tests/2026/commands"
                    shot.mkdir(parents=True, exist_ok=True)
                    (shot / f"screenshot-❌-1-({lp}).png").write_bytes(b"\x89PNG call %d" % self.calls)
            return done
        self.run_.fake_maestro = maestro
        self.pictures = {1, 2}

    def go(self):
        with mock.patch.object(sf, "screenshot_texts", return_value=[]):
            code, out = self.run_.run_it()
        return code, out, (self.run_.d / "out").resolve()

    def test_a_failed_retry_leaves_its_picture_in_the_output_and_names_it(self):
        self.run_.outcomes = {"de": ["Unknown error"]}
        code, out, folder = self.go()
        self.assertEqual(code, 1, out)
        self.assertEqual((folder / "failures/de.png").read_bytes(), b"\x89PNG call 2")
        self.assertIn(f"failure screenshot: {folder / 'failures/de.png'}", out)
        self.assertEqual(self.run_.run_json()["de"]["failure_screenshot"], "failures/de.png")
        self.assertNotIn("failure_screenshot", self.run_.run_json()["fr"])
        self.assertEqual(list((folder / "failures").iterdir()), [folder / "failures/de.png"])

    def test_a_retry_that_saved_no_picture_leaves_the_first_tries(self):
        self.pictures = {1}
        self.run_.outcomes = {"de": ["Unknown error"]}
        code, out, folder = self.go()
        self.assertEqual((folder / "failures/de-first-try.png").read_bytes(), b"\x89PNG call 1")
        self.assertIn("(the first try's: the retry saved none)", out); self.assertEqual(self.run_.run_json()["de"]["failure_screenshot"], "failures/de-first-try.png")

    def test_a_later_run_that_passes_removes_the_old_picture(self):
        self.run_.outcomes = {"de": ["Unknown error"]}
        self.go()
        self.run_.outcomes = {}; self.calls = 0
        code, out, folder = self.go()
        self.assertEqual(code, 0, out); self.assertEqual(list((folder / "failures").iterdir()), [])
        self.assertNotIn("failure_screenshot", self.run_.run_json()["de"])


from tests.test_claims_unit import FleetCase  # a project with fake simulators, emulators and Maestro


class AndroidFailureInARun(FleetCase):  # items 24 and 25, a whole Android run on the fakes
    """One emulator, one language (en), a Maestro that fails the flow the way self.error says and leaves its failure screenshot on the calls in self.pictures."""
    dump = WINDOWS % SPLASH_WINDOW.replace(PKG, "p.q")

    def setUp(self):
        super().setUp()
        self.tries, self.pictures, self.error = 0, {1, 2}, "Assertion is false: id: login-button is visible"
        p = mock.patch.object(sf, "screenshot_texts", return_value=[]); p.start(); self.addCleanup(p.stop)

    def fake_android_pool(self, n, cfg, pool):
        test = self
        class Emu:
            serial = "emulator-5702"
            def adb(self, *a, check=True, timeout=180): return test.dump if a == ("shell", "dumpsys", "window") else ""
        pool.append(Emu())

    def fake_maestro(self, cmd, env=None, timeout=None, cwd=None, **kw):
        self.tries += 1
        junit, dbg = Path(cmd[cmd.index("--output") + 1]), Path(cmd[cmd.index("--debug-output") + 1])
        (dbg / ".maestro/tests/x").mkdir(parents=True, exist_ok=True)
        flow = next(Path(cmd[cmd.index("test") + 1]).glob("*.yaml")).stem
        (dbg / "maestro.log").write_text(f"Selected device emulator-5702 using port 7001 with execution plan ExecutionPlan(flowsToRun=[/x/{flow}.yaml], sequence=x)\n")
        if self.tries in self.pictures: (dbg / f".maestro/tests/x/screenshot-❌-1-({flow}).png").write_bytes(b"\x89PNG call %d" % self.tries)
        junit.write_text(f'<testsuites><testsuite><testcase name="{flow}" time="1"><failure>{self.error}</failure></testcase></testsuite></testsuites>')
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def go(self):
        code, out, err = self.main("run", self.config(ios=None, android='locales = ["en"]\n'))
        folder = (self.d / "out").resolve()
        return code, out, json.loads((folder / "run.json").read_text())["locales"]["en"], folder

    def test_a_stuck_splash_is_named_and_the_picture_stays_in_the_output(self):
        code, out, en, folder = self.go()
        self.assertEqual(code, 1, out); self.assertEqual(self.tries, 1)
        self.assertIn("     the app's splash screen is still showing; taps can't reach the app", out)
        self.assertIn(f"failure screenshot: {folder / 'failures/en.png'}", out)
        self.assertEqual((folder / "failures/en.png").read_bytes(), b"\x89PNG call 1"); self.assertEqual(en["failure_screenshot"], "failures/en.png")
        self.assertFalse(any(k.startswith("_") for k in en))

    def test_without_the_splash_window_the_message_does_not_claim_one(self):
        self.dump = WINDOWS % ""
        code, out, en, folder = self.go()
        self.assertNotIn("splash screen is still showing", out)

    def test_a_failed_retry_without_a_picture_leaves_the_first_tries(self):
        self.error, self.pictures = "Unknown error", {1}
        code, out, en, folder = self.go()
        self.assertEqual(code, 1, out); self.assertEqual(self.tries, 2)
        self.assertEqual((folder / "failures/en-first-try.png").read_bytes(), b"\x89PNG call 1")
        self.assertIn(f"failure screenshot: {folder / 'failures/en-first-try.png'} (the first try's: the retry saved none)", out)
        self.assertEqual(en["failure_screenshot"], "failures/en-first-try.png"); self.assertIn("the app's splash screen is still showing", out)
