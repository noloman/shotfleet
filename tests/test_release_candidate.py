"""tools/release-candidate.sh: the script is checked without building anything (the build takes minutes and hundreds of MB).
Syntax, the refusal to run without SHOTFLEET_RC=1, the safety rules in its text, and its Python helpers: above all that the fake
Gumroad licence server answers the way shotfleet.gumroad_verify reads it. Nothing here touches the network (127.0.0.1 only).

Run: python3 -m unittest discover -s tests
"""
import contextlib, importlib.util, io, json, os, subprocess, sys, tempfile, threading, time, unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import shotfleet as sf

SCRIPT = ROOT / "tools/release-candidate.sh"
TEXT = SCRIPT.read_text()


def load_helper():
    """The Python at the end of the script, extracted the way the script extracts it, imported as a module."""
    src = subprocess.run(["sed", "-n", "/^: <<.__PY__.$/,/^__PY__$/p", str(SCRIPT)], capture_output=True, text=True).stdout
    path = Path(tempfile.mkdtemp()) / "rc_helper.py"
    path.write_text("\n".join(src.splitlines()[1:-1]) + "\n")
    spec = importlib.util.spec_from_file_location("rc_helper", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


rc = load_helper()


class Script(unittest.TestCase):
    def test_syntax(self):
        r = subprocess.run(["sh", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stderr), (0, ""))

    def test_refuses_to_run_without_the_opt_in(self):
        env = {k: v for k, v in os.environ.items() if k != "SHOTFLEET_RC"}
        r = subprocess.run(["sh", str(SCRIPT)], capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(r.returncode, 2)
        self.assertIn("refusing to run", r.stderr)
        self.assertIn("SHOTFLEET_RC=1", r.stderr)
        self.assertEqual(r.stdout, "")  # it built and printed nothing
        r = subprocess.run(["sh", str(SCRIPT)], capture_output=True, text=True, env={**env, "SHOTFLEET_RC": "0"}, timeout=30)
        self.assertEqual(r.returncode, 2)  # only the exact value 1 opts in

    def test_help_does_not_build(self):
        r = subprocess.run(["sh", str(SCRIPT), "--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0)
        self.assertIn("SHOTFLEET_RC=1", r.stdout)

    def test_it_never_submits_deploys_pushes_or_calls_a_store(self):
        code = "\n".join(l for l in TEXT.splitlines() if not l.lstrip().startswith("#"))
        for forbidden in ("notarytool submit", "wrangler", "git push", "simctl boot", "simctl create", "api.gumroad.com", "api.polar.sh",
                          "lemonsqueezy", "SHOTFLEET_BASE=https://"):
            self.assertNotIn(forbidden, code)
        self.assertIn("env -u NOTARY_PROFILE", code)  # build.sh only notarizes when NOTARY_PROFILE is set
        self.assertIn("sed -i '' \"s|^GUMROAD_PRODUCT_ID", code)  # the product id goes into a copy under $SRC...
        self.assertNotIn('"$ROOT/shotfleet.py"', code.split("sed -i")[1].split("\n")[0])  # ...never into the repo's file

    def test_install_sh_still_has_the_candidate_line_the_script_rewrites(self):
        line = 'for DIR in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do'
        self.assertIn(line, (ROOT / "site/public/install.sh").read_text().splitlines())
        self.assertIn("for DIR in /opt/homebrew/bin /usr/local/bin ", TEXT)  # the sed patterns in the script

    def test_the_messages_the_script_greps_for_exist_in_the_program(self):
        # messages the script greps for must exist in the program, or its checks could never pass
        src = (ROOT / "shotfleet.py").read_text()
        for msg in ("need a licence: shotfleet activate", "free tier: capturing", "none of those languages are in the app",
                    "this key has used all", "the purchase was refunded", "this licence is no longer valid", "couldn't reach the licence server for 30 days",
                    "SHOTFLEET_KEY isn't a valid licence", "removed from this Mac. Gumroad can't give the activation back from here",
                    "that key didn't activate", "no licence on this Mac", "exported {len(done)} listings"):
            self.assertIn(msg, src)


class FakeServerContract(unittest.TestCase):
    """The fake licence server and the program's own gumroad_verify agree on the shape of Gumroad's answers."""
    PRODUCT = "RCTESTPRODUCT0001abc=="

    def setUp(self):
        self.fake = rc.FakeGumroad(self.PRODUCT)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), rc.handler(self.fake))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.patches = [mock.patch.object(sf, "GUMROAD_API", f"{self.base}/v2/licenses"),
                        mock.patch.object(sf, "GUMROAD_PRODUCT_ID", self.PRODUCT)]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in self.patches: p.stop()
        self.server.shutdown(); self.server.server_close()

    def post(self, path, **form):
        import urllib.parse, urllib.request
        with urllib.request.urlopen(urllib.request.Request(self.base + path, data=urllib.parse.urlencode(form).encode())) as r:
            return json.loads(r.read() or b"{}")

    def test_a_good_key_and_the_use_counter(self):
        self.assertEqual(sf.gumroad_verify(rc.GOOD, count_use=False), (True, 0, None))
        self.assertEqual(sf.gumroad_verify(rc.GOOD, count_use=True), (True, 1, None))
        self.assertEqual(sf.gumroad_verify(rc.GOOD, count_use=False), (True, 1, None))  # looking does not count
        self.assertEqual([c["increment_uses_count"] for c in self.fake.calls], ["false", "true", "false"])
        self.assertTrue(all(set(c) == {"product_id", "license_key", "increment_uses_count"} for c in self.fake.calls))

    def test_refunded_chargebacked_and_disputed_keys_are_refused_but_a_won_dispute_is_not(self):
        self.assertEqual(sf.gumroad_verify(rc.REFUNDED, count_use=False), (False, 0, "the purchase was refunded"))
        self.assertEqual(sf.gumroad_verify(rc.CHARGEBACK, count_use=False), (False, 0, "the purchase was charged back"))
        self.assertEqual(sf.gumroad_verify(rc.DISPUTED, count_use=False), (False, 0, "the purchase is disputed"))
        self.assertEqual(sf.gumroad_verify(rc.WON, count_use=False), (True, 0, None))

    def test_unknown_key_and_another_products_id_are_a_404_with_gumroads_message(self):
        want = (False, 0, "That license does not exist for the provided product")
        self.assertEqual(sf.gumroad_verify("00000000-00000000-00000000-00000001", count_use=False), want)
        with mock.patch.object(sf, "GUMROAD_PRODUCT_ID", "someoneelse=="):
            self.assertEqual(sf.gumroad_verify(rc.GOOD, count_use=False), want)

    def test_an_outage_is_an_oserror_not_a_verdict(self):
        self.post("/_ctl", outage="1")
        with self.assertRaisesRegex(OSError, "Gumroad answered 503"): sf.gumroad_verify(rc.GOOD, count_use=False)
        self.post("/_ctl", outage="0")
        self.assertTrue(sf.gumroad_verify(rc.GOOD, count_use=False)[0])

    def test_no_server_at_all_is_an_oserror_too(self):
        self.server.shutdown(); self.server.server_close()
        with self.assertRaisesRegex(OSError, "can't reach the licence server"): sf.gumroad_verify(rc.GOOD, count_use=False)

    def test_the_control_endpoint_refunds_and_unrefunds(self):
        self.post("/_ctl", refund=rc.GOOD)
        self.assertEqual(sf.gumroad_verify(rc.GOOD, count_use=False)[2], "the purchase was refunded")
        self.post("/_ctl", unrefund=rc.GOOD)
        self.assertTrue(sf.gumroad_verify(rc.GOOD, count_use=False)[0])

    def test_state_reports_uses_and_calls(self):
        import urllib.request
        sf.gumroad_verify(rc.GOOD, count_use=True)
        with urllib.request.urlopen(self.base + "/_state") as r: s = json.loads(r.read())
        self.assertEqual(s["uses"][rc.GOOD], 1); self.assertEqual(len(s["calls"]), 1); self.assertFalse(s["outage"])

    def test_activation_through_the_program_against_the_fake(self):
        """cmd_activate end to end: three Macs, the 4th refused without burning a use, a refunded key refused for free."""
        homes = [Path(tempfile.mkdtemp()) / "licence.json" for _ in range(4)]
        for i, lic in enumerate(homes):
            with mock.patch.object(sf, "LICENCE_FILE", lic), contextlib.redirect_stdout(io.StringIO()):
                if i < 3: self.assertEqual(sf.cmd_activate(rc.GOOD), 0)
                else:
                    with self.assertRaisesRegex(sf.Fail, "used all 3 activations. Email hello@shotfleet.com"): sf.cmd_activate(rc.GOOD)
        self.assertEqual(self.fake.uses[rc.GOOD], 3)
        with mock.patch.object(sf, "LICENCE_FILE", homes[0]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sf.cmd_activate(rc.GOOD), 0)  # already on this Mac: nothing counted
            with self.assertRaisesRegex(sf.Fail, "the purchase was refunded"): sf.cmd_activate(rc.REFUNDED)
        self.assertEqual((self.fake.uses[rc.GOOD], self.fake.uses[rc.REFUNDED]), (3, 0))


class Fixtures(unittest.TestCase):
    def test_fixture_has_the_planted_problems(self):
        """Deterministic: macOS's own text recognition is switched off (as when it is stuck), so --ocr-command reads every screenshot."""
        with tempfile.TemporaryDirectory() as d:
            rc.fixture(d)
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.dict(os.environ, {"SHOTFLEET_OCR": "cat {image}.txt"}), mock.patch.object(sf, "ocr_tool", return_value="ocr"), \
                 mock.patch.object(sf, "warm_up_ocr", return_value=False), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = sf.main(["check", f"{d}/shots", "--strings", f"{d}/locales/*/translation.json", "--report", f"{d}/rep", "--json"])
            report = json.loads(out.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(len(report["screenshots"]), 3)
        # el/2.png shows English (planted) and en/2.png is missing. On the frozen build, where macOS's own OCR reads English, en/1.png
        # (a header-only PNG) may also be reported blank: the script accepts both
        self.assertEqual(sorted(p.split(":")[0] for p in report["problems"]), ["el/2.png", "en"])

    def test_exportfx_exports_one_listing(self):
        with tempfile.TemporaryDirectory() as d:
            rc.exportfx(d)
            out = io.StringIO()
            with contextlib.redirect_stdout(out): code = sf.cmd_export(Path(d) / "out", Path(d) / "fl")
            self.assertEqual(code, 0)
            self.assertIn("exported 1 listings", out.getvalue())
            self.assertTrue((Path(d) / "fl/screenshots/de-DE/01.png").is_file())

    @unittest.skipUnless(sys.platform == "darwin", "reads the app's Info.plist with PlistBuddy")
    def test_freetier_config_prints_the_cap_and_stops_before_any_device(self):
        """The same thing the script asserts on the frozen build, here from source with the gate forced on."""
        with tempfile.TemporaryDirectory() as d:
            rc.freetier(d)
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(sf.sys, "frozen", True, create=True), mock.patch.object(sf, "LICENCE_FILE", Path(d) / "none.json"), \
                 mock.patch.object(sf, "LOCALE_CAP", None), mock.patch.object(sf.shutil, "which", return_value="/usr/bin/true"), \
                 mock.patch.object(sf, "make_pool", side_effect=AssertionError("a simulator must not be created")), \
                 mock.patch.dict(os.environ, {"SHOTFLEET_KEY": ""}), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = sf.main(["run", f"{d}/shotfleet.toml"])
        self.assertEqual(code, 2)
        self.assertIn("note: `export` and every language in `run` need a licence", err.getvalue())
        self.assertIn("free tier: capturing 2 of 3 languages (fr, it)", out.getvalue())
        self.assertIn("none of those languages are in the app", err.getvalue())
        self.assertNotIn("booting", out.getvalue())

    def test_age_makes_a_licence_old(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "licence.json"; f.write_text(json.dumps({"key": "k", "store": "gumroad", "checked": time.time()}))
            rc.age(f, 8)
            data = json.loads(f.read_text())
        self.assertEqual((data["key"], data["store"]), ("k", "gumroad"))
        self.assertAlmostEqual((time.time() - data["checked"]) / 86400, 8, places=2)

    def test_the_helper_cli_dispatches(self):
        with tempfile.TemporaryDirectory() as d:
            helper = Path(d) / "h.py"
            helper.write_text(subprocess.run(["sed", "-n", "/^: <<.__PY__.$/,/^__PY__$/p", str(SCRIPT)], capture_output=True, text=True).stdout.split("\n", 1)[1].rsplit("__PY__", 1)[0])
            for cmd in ("fixture", "freetier", "exportfx"):
                r = subprocess.run([sys.executable, str(helper), cmd, f"{d}/{cmd}"], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(d) / "fixture/shots/el/2.png").is_file())
            self.assertTrue((Path(d) / "freetier/shotfleet.toml").is_file())


if __name__ == "__main__":
    unittest.main()
