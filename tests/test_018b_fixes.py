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
