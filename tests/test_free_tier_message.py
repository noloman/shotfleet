"""What `run` says when it is capped to the free tier (research/limits-product-improvements-2026-10-05.md, finding 2): that there is no
valid licence, why a SHOTFLEET_KEY was refused, which languages were captured, and that --locales picks others. Wording only: the exit
code and who is licensed are unchanged (0 for the capped run; an unreachable licence server caps only a key that never passed a check on this machine).

Fake tools and a stubbed licence server (urlopen): no network, simulator, emulator or Maestro.
Run: python3 -m unittest tests.test_free_tier_message   (or: cd tests && python3 -m unittest test_free_tier_message)
"""
import contextlib, io, os, sys, unittest, urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_claims_unit import FleetCase, GUMROAD_KEY, Reply, gumroad_answer, http_error, sf


class FreeTierMessage(FleetCase):
    def run_cli(self, key=None, urlopen=None, *argv):
        """`shotfleet run` on a frozen build with SHOTFLEET_KEY=key (unset when None) and `urlopen` standing in for Gumroad."""
        def no_server(*a, **k): raise AssertionError("a licence server was contacted")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
             mock.patch.object(sf, "GUMROAD_PRODUCT_ID", "prod1"), mock.patch.object(sf, "RELEASE_DATE", sf.datetime.date(2024, 10, 1)), mock.patch.object(sf.urllib.request, "urlopen", urlopen or no_server):
            os.environ.pop("SHOTFLEET_KEY", None)
            if key is not None: os.environ["SHOTFLEET_KEY"] = key
            code = sf.main(["run", self.config(), "--platform", "ios", *argv])
        return code, out.getvalue(), err.getvalue()

    def test_no_key_says_no_valid_licence_names_the_two_languages_and_points_at_locales(self):
        code, out, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertEqual(list(self.ios.values()), [["de", "en"]])
        self.assertIn("free tier: capturing 2 of 4 languages (de, en)", out)
        self.assertIn("because there is no valid licence", out)
        self.assertIn("--locales a,b", out)
        self.assertIn("`shotfleet activate <key>` unlocks every language", out)
        self.assertNotIn("SHOTFLEET_KEY", out)  # no key was set, so the line does not talk about one

    def test_a_refused_key_stops_run_with_the_reason_instead_of_a_green_two_language_run(self):
        """0.1.6 (review N1): SHOTFLEET_KEY is a CI gate, so a refused key must not exit 0 with 2 languages."""
        gone = {"success": False, "message": "That license does not exist for the provided product."}
        def refused(*a, **k): raise http_error(404, gone)
        code, out, err = self.run_cli(GUMROAD_KEY, refused)
        self.assertEqual(code, 2)
        self.assertEqual(list(self.ios.values()), [])  # nothing was captured
        self.assertIn("SHOTFLEET_KEY isn't a valid licence (That license does not exist for the provided product)", err)
        self.assertIn("stops here instead of capturing only 2 languages", err)
        self.assertNotIn(GUMROAD_KEY, out + err)

    def test_a_key_that_is_not_a_shotfleet_key_stops_run_too(self):
        code, out, err = self.run_cli("not-a-key")
        self.assertEqual(code, 2)
        self.assertIn("(not a shotfleet key)", err)

    def test_an_unreachable_licence_server_stops_run_for_a_key_this_machine_never_checked_and_says_why(self):
        def offline(*a, **k): raise urllib.error.URLError("offline")
        code, out, err = self.run_cli(GUMROAD_KEY, offline)
        self.assertEqual(code, 2)
        self.assertEqual(list(self.ios.values()), [])
        self.assertIn("SHOTFLEET_KEY couldn't be checked", err)
        self.assertIn("passed a check in the last 30 days", err)

    def test_an_unreachable_licence_server_is_no_cap_for_a_key_that_passed_a_check_here(self):
        def ok(*a, **k): return Reply(gumroad_answer())
        def offline(*a, **k): raise urllib.error.URLError("offline")
        self.run_cli(GUMROAD_KEY, ok); self.ios.clear()
        code, out, err = self.run_cli(GUMROAD_KEY, offline)
        self.assertEqual(code, 0, err)
        self.assertEqual(list(self.ios.values()), [["de", "en", "fr", "ja"]])
        self.assertNotIn("free tier", out + err)

    def test_locales_picks_which_two_and_the_message_names_them(self):
        code, out, err = self.run_cli(None, None, "--locales", "ja,fr,de")
        self.assertEqual(code, 0, err)
        self.assertEqual(list(self.ios.values()), [["fr", "ja"]])  # the fake Maestro lists them sorted; the message below keeps the given order
        self.assertIn("free tier: capturing 2 of 3 languages (ja, fr)", out)

    def test_a_licensed_run_prints_no_free_tier_line(self):
        def ok(*a, **k): return Reply(gumroad_answer())
        code, out, err = self.run_cli(GUMROAD_KEY, ok)
        self.assertEqual(code, 0, err)
        self.assertNotIn("free tier", out + err)
        self.assertEqual(list(self.ios.values()), [["de", "en", "fr", "ja"]])


if __name__ == "__main__":
    unittest.main()
