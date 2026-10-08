"""0.1.8 fixes from the dogfood runs of 2026-10-08: regex selectors in the strings pre-check, port 7001, a splash that never hides,
the failure screenshot after a retry. Fakes only: no simulator, emulator, Maestro, adb or text recognition.

Run: python3 -m unittest tests.test_018b_fixes
"""
import contextlib, io, subprocess, sys, tempfile, unittest
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
